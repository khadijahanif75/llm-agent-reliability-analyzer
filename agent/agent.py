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
    """Core Agent Execution Loop managing LLM decision cycles, tool dispatching, and trajectory tracing."""
    
    def __init__(
        self,
        llm_provider: Optional[BaseLLMProvider] = None,
        tracer: Optional[Tracer] = None,
        max_steps: Optional[int] = None,
        tools: Optional[List[BaseTool]] = None
    ):
        self.llm = llm_provider or get_llm_provider()
        self.tracer = tracer or Tracer()
        self.max_steps = max_steps or settings.MAX_STEPS
        
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
        """Executes full agent loop until final answer is reached or max steps exceeded."""
        run = self.tracer.start_run(user_prompt=user_prompt)
        history: List[Dict[str, Any]] = []
        step_number = 1
        
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

            # 3. Tool Selected & Execution
            tool_name = action.action
            tool_args = action.arguments
            
            self.tracer.log_event(
                run_id=run.run_id,
                step_number=step_number,
                event_type=TraceEventType.TOOL_STARTED,
                tool_name=tool_name,
                tool_input=tool_args
            )

            # Dispatch Tool
            result: ToolResult = self.dispatch_tool(tool_name=tool_name, arguments=tool_args)

            if result.success:
                self.tracer.log_event(
                    run_id=run.run_id,
                    step_number=step_number,
                    event_type=TraceEventType.TOOL_SUCCEEDED,
                    tool_name=tool_name,
                    tool_output=result.output,
                    latency_ms=result.latency_ms,
                    status="SUCCESS"
                )
                # Feed observation back into history
                history.append({
                    "event": "OBSERVATION",
                    "step": step_number,
                    "tool_name": tool_name,
                    "output": result.output
                })
            else:
                self.tracer.log_event(
                    run_id=run.run_id,
                    step_number=step_number,
                    event_type=TraceEventType.TOOL_FAILED,
                    tool_name=tool_name,
                    error_type=result.error_type,
                    error_message=result.error_message,
                    latency_ms=result.latency_ms,
                    status="FAILED"
                )
                return self.tracer.finish_run(
                    run=run,
                    final_response=f"Execution halted: Tool '{tool_name}' failed with error: {result.error_message}",
                    success=False,
                    primary_failure_type=result.error_type,
                    primary_failure_step=step_number
                )

            step_number += 1

        # 4. Maximum Steps Exceeded
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