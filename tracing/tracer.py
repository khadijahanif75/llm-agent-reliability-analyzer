import time
import uuid
from datetime import datetime
from typing import Any, Dict, Optional
from storage.repositories import TraceRepository
from tracing.events import ErrorType, RunStatus, TraceEventType
from tracing.models import AgentRun, TraceEvent

class Tracer:
    """Central instrumentation logger recording agent executions and step events."""
    
    def __init__(self, repository: Optional[TraceRepository] = None):
        self.repo = repository or TraceRepository()

    def start_run(self, user_prompt: str, run_id: Optional[str] = None) -> AgentRun:
        r_id = run_id or f"run_{uuid.uuid4().hex[:8]}"
        run = AgentRun(
            run_id=r_id,
            user_prompt=user_prompt,
            start_time=datetime.utcnow(),
            status=RunStatus.RUNNING
        )
        self.repo.save_run(run)
        
        # Log initial event
        self.log_event(
            run_id=r_id,
            step_number=0,
            event_type=TraceEventType.RUN_STARTED,
            status="INFO"
        )
        return run

    def log_event(
        self,
        run_id: str,
        step_number: int,
        event_type: TraceEventType,
        tool_name: Optional[str] = None,
        tool_input: Optional[Dict[str, Any]] = None,
        tool_output: Optional[Any] = None,
        expected_tool: Optional[str] = None,
        selected_tool: Optional[str] = None,
        tool_selection_correct: Optional[bool] = None,
        status: str = "INFO",
        error_type: ErrorType = ErrorType.NONE,
        error_message: Optional[str] = None,
        retry_count: int = 0,
        latency_ms: float = 0.0
    ) -> TraceEvent:
        event = TraceEvent(
            event_id=f"evt_{uuid.uuid4().hex[:8]}",
            run_id=run_id,
            step_number=step_number,
            event_type=event_type,
            timestamp=datetime.utcnow(),
            tool_name=tool_name,
            tool_input=tool_input,
            tool_output=tool_output,
            expected_tool=expected_tool,
            selected_tool=selected_tool,
            tool_selection_correct=tool_selection_correct,
            status=status,
            error_type=error_type,
            error_message=error_message,
            retry_count=retry_count,
            latency_ms=latency_ms
        )
        self.repo.save_event(event)
        return event

    def finish_run(
        self,
        run: AgentRun,
        final_response: Optional[str],
        success: bool,
        primary_failure_type: ErrorType = ErrorType.NONE,
        primary_failure_step: Optional[int] = None
    ) -> AgentRun:
        run.end_time = datetime.utcnow()
        run.total_latency_ms = (run.end_time - run.start_time).total_seconds() * 1000
        run.final_response = final_response
        run.success = success
        run.status = RunStatus.SUCCESS if success else RunStatus.FAILED
        run.primary_failure_type = primary_failure_type
        run.primary_failure_step = primary_failure_step

        self.repo.save_run(run)
        
        self.log_event(
            run_id=run.run_id,
            step_number=run.total_steps + 1,
            event_type=TraceEventType.RUN_COMPLETED if success else TraceEventType.RUN_FAILED,
            status="SUCCESS" if success else "FAILED",
            error_type=primary_failure_type
        )
        return run