import time
from typing import Any, Dict, List, Optional
from agent.factory import get_llm_provider
from agent.llm_client import BaseLLMProvider
from config import settings
from tools.base import BaseTool, ToolResult
from tools.calculator import CalculatorTool
from tools.database import DatabaseTool
from tools.search import SearchTool
from tracing.events import ErrorType, TraceEventType
from tracing.models import AgentRun, LLMAction
from tracing.tracer import Tracer

class AgentLoop:
    """Core Agent Execution Loop managing LLM decision cycles, tool dispatching, retries, and trajectory tracing."""
    
    def __init__(
        self,
        llm_provider: Optional[BaseLLMProvider] = None,
        tracer: Optional[Tracer] = None,
        max_steps: Optional[int] = None,
        max_retries: Optional[int] = None,
        tools: Optional[List[BaseTool]] = None
    ):
        self.llm = llm_provider or get_llm_provider()
        self.tracer = tracer or Tracer()
        self.max_steps = max_steps if max_steps is not None else settings.MAX_STEPS
        self.max_retries = max_retries if max_retries is not None else settings.MAX_RETRIES
        
        # Register Tools
        default_tools = [
            CalculatorTool(),
            SearchTool(
                failure_rate=settings.SEARCH_FAILURE_RATE if settings.ENABLE_FAILURE_INJECTION else 0.0
            ),
            DatabaseTool(
                failure_rate=settings.DATABASE_FAILURE_RATE if settings.ENABLE_FAILURE_INJECTION else 0.0
            )
        ]
        tool_list = tools or default_tools
        self.tools: Dict[str, BaseTool] = {t.name: t for t in tool_list}

    def is_recoverable_error(self, error_type: ErrorType) -> bool:
        """Determines if a tool failure is transient and eligible for retry execution."""
        return error_type in [ErrorType.TIMEOUT, ErrorType.TOOL_EXECUTION_ERROR]

    def dispatch_tool(self, tool_name: str, arguments: Dict[str, Any]) -> ToolResult:
        """Dispatches action execution to the matching registered tool."""
        if tool_name not in self.tools:
            return ToolResult(
                tool_name=tool_name,
                success=False,
                error_type=ErrorType.WRONG_TOOL_SELECTION,
                error_message=f"Tool '{tool_name}' is not registered in agent dispatch table."
            )
        tool = self.tools[tool_name]
        return tool.execute(**arguments)

    def run(self, user_prompt: str, expected_tool: Optional[str] = None) -> AgentRun:
        """Executes full agent loop until final answer is reached, retries exhausted, or max steps exceeded."""
        run = self.tracer.start_run(user_prompt=user_prompt)
        history: List[Dict[str, Any]] = []
        step_number = 1

        if self.max_steps <= 0:
            self.tracer.log_event(
                run_id=run.run_id,
                step_number=1,
                event_type=TraceEventType.MAX_STEPS_REACHED,
                status="FAILED",
                error_type=ErrorType.MAX_STEPS_EXCEEDED
            )
            return self.tracer.finish_run(
                run=run,
                final_response="Task failed: Maximum step limit reached immediately.",
                success=False,
                primary_failure_type=ErrorType.MAX_STEPS_EXCEEDED,
                primary_failure_step=1
            )

        while step_number <= self.max_steps:
            run.total_steps = step_number
            
            # 1. LLM Decision Step
            start_llm_time = time.perf_counter()
            action: LLMAction = self.llm.decide(user_prompt=user_prompt, history=history)
            llm_latency = (time.perf_counter() - start_llm_time) * 1000
            
            self.tracer.log_event(
                run_id=run.run_id,
                step_number=step_number,
                event_type=TraceEventType.LLM_DECISION,
                selected_tool=action.action,
                expected_tool=expected_tool,
                tool_selection_correct=(action.action == expected_tool) if expected_tool else None,
                latency_ms=llm_latency
            )

            # 2. Check for Termination (Final Answer)
            if action.action == "final_answer":
                self.tracer.log_event(
                    run_id=run.run_id,
                    step_number=step_number,
                    event_type=TraceEventType.FINAL_RESPONSE,
                    status="SUCCESS",
                    tool_output=action.final_answer
                )
                return self.tracer.finish_run(
                    run=run,
                    final_response=action.final_answer or "Task completed.",
                    success=True
                )

            # 3. Tool Selected & Execution with Retry Handling
            tool_name = action.action
            tool_args = action.arguments
            
            self.tracer.log_event(
                run_id=run.run_id,
                step_number=step_number,
                event_type=TraceEventType.TOOL_STARTED,
                tool_name=tool_name,
                tool_input=tool_args
            )

            # Execution Attempt Loop (Attempt 0 = Initial call, 1..max_retries = Retries)
            result: Optional[ToolResult] = None
            retry_count = 0
            
            for attempt in range(self.max_retries + 1):
                if attempt > 0:
                    retry_count = attempt
                    self.tracer.log_event(
                        run_id=run.run_id,
                        step_number=step_number,
                        event_type=TraceEventType.RETRY_ATTEMPT,
                        tool_name=tool_name,
                        retry_count=retry_count,
                        status="INFO"
                    )

                result = self.dispatch_tool(tool_name=tool_name, arguments=tool_args)
                
                if result.success:
                    break
                
                # If error is not recoverable, break immediately without spending retries
                if not self.is_recoverable_error(result.error_type):
                    break

            if result and result.success:
                self.tracer.log_event(
                    run_id=run.run_id,
                    step_number=step_number,
                    event_type=TraceEventType.TOOL_SUCCEEDED,
                    tool_name=tool_name,
                    tool_output=result.output,
                    latency_ms=result.latency_ms,
                    retry_count=retry_count,
                    status="SUCCESS"
                )
                history.append({
                    "event": "OBSERVATION",
                    "step": step_number,
                    "tool_name": tool_name,
                    "output": result.output
                })
            else:
                final_error = result.error_type if result else ErrorType.UNKNOWN_ERROR
                final_msg = result.error_message if result else "Unknown execution error"
                
                self.tracer.log_event(
                    run_id=run.run_id,
                    step_number=step_number,
                    event_type=TraceEventType.TOOL_FAILED,
                    tool_name=tool_name,
                    error_type=final_error,
                    error_message=final_msg,
                    latency_ms=result.latency_ms if result else 0.0,
                    retry_count=retry_count,
                    status="FAILED"
                )
                return self.tracer.finish_run(
                    run=run,
                    final_response=f"Execution halted: Tool '{tool_name}' failed after {retry_count} retries with error: {final_msg}",
                    success=False,
                    primary_failure_type=final_error,
                    primary_failure_step=step_number
                )

            step_number += 1

        # 4. Maximum Steps Exceeded Fallback
        self.tracer.log_event(
            run_id=run.run_id,
            step_number=step_number,
            event_type=TraceEventType.MAX_STEPS_REACHED,
            status="FAILED",
            error_type=ErrorType.MAX_STEPS_EXCEEDED
        )
        return self.tracer.finish_run(
            run=run,
            final_response="Task failed: Agent exceeded maximum allowed trajectory steps.",
            success=False,
            primary_failure_type=ErrorType.MAX_STEPS_EXCEEDED,
            primary_failure_step=step_number
        )