from datetime import datetime
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field
from tracing.events import TraceEventType, ErrorType, RunStatus

class LLMAction(BaseModel):
    action: str  # e.g., 'calculator', 'search', 'database', 'final_answer'
    arguments: Dict[str, Any] = Field(default_factory=dict)
    final_answer: Optional[str] = None

class TraceEvent(BaseModel):
    event_id: str
    run_id: str
    step_number: int
    event_type: TraceEventType
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    tool_name: Optional[str] = None
    tool_input: Optional[Dict[str, Any]] = None
    tool_output: Optional[Any] = None
    
    expected_tool: Optional[str] = None
    selected_tool: Optional[str] = None
    tool_selection_correct: Optional[bool] = None
    
    status: str = "INFO"
    error_type: ErrorType = ErrorType.NONE
    error_message: Optional[str] = None
    retry_count: int = 0
    latency_ms: float = 0.0

class AgentRun(BaseModel):
    run_id: str
    user_prompt: str
    start_time: datetime = Field(default_factory=datetime.utcnow)
    end_time: Optional[datetime] = None
    total_latency_ms: float = 0.0
    total_steps: int = 0
    final_response: Optional[str] = None
    status: RunStatus = RunStatus.PENDING
    success: bool = False
    primary_failure_type: ErrorType = ErrorType.NONE
    primary_failure_step: Optional[int] = None