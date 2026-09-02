import uuid
from datetime import datetime
from storage.database import init_db
from storage.repositories import TraceRepository
from tracing.models import AgentRun, TraceEvent
from tracing.events import RunStatus, TraceEventType, ErrorType

def test_database_persistence():
    init_db()
    repo = TraceRepository()
    
    unique_run_id = f"test_run_{uuid.uuid4().hex[:6]}"
    unique_event_id = f"evt_{uuid.uuid4().hex[:6]}"
    
    # 1. Create Dummy Run
    run = AgentRun(
        run_id=unique_run_id,
        user_prompt="Calculate 10 * 50",
        start_time=datetime.utcnow(),
        status=RunStatus.SUCCESS,
        success=True
    )
    repo.save_run(run)
    
    # 2. Create Dummy Trace Event
    event = TraceEvent(
        event_id=unique_event_id,
        run_id=unique_run_id,
        step_number=1,
        event_type=TraceEventType.TOOL_STARTED,
        tool_name="calculator",
        tool_input={"expression": "10 * 50"}
    )
    repo.save_event(event)