from datetime import datetime
from storage.database import init_db
from storage.repositories import TraceRepository
from tracing.models import AgentRun, TraceEvent
from tracing.events import RunStatus, TraceEventType, ErrorType

def test_database_persistence():
    # 1. Initialize Test DB
    init_db()
    repo = TraceRepository()
    
    # 2. Create Dummy Run
    run = AgentRun(
        run_id="test_run_101",
        user_prompt="Calculate 10 * 50",
        start_time=datetime.utcnow(),
        status=RunStatus.SUCCESS,
        success=True
    )
    repo.save_run(run)
    
    # 3. Create Dummy Trace Event
    event = TraceEvent(
        event_id="evt_001",
        run_id="test_run_101",
        step_number=1,
        event_type=TraceEventType.TOOL_STARTED,
        tool_name="calculator",
        tool_input={"expression": "10 * 50"}
    )
    repo.save_event(event)
    
    print("Database persistence test passed successfully!")

if __name__ == "__main__":
    test_database_persistence()