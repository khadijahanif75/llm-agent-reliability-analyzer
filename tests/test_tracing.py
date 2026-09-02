from storage.database import init_db
from tracing.events import ErrorType, TraceEventType
from tracing.tracer import Tracer

def test_tracer_flow():
    init_db()
    tracer = Tracer()
    
    # 1. Start Run
    run = tracer.start_run(user_prompt="Find university details")
    assert run.run_id.startswith("run_")
    
    # 2. Log Tool Selected Event
    evt = tracer.log_event(
        run_id=run.run_id,
        step_number=1,
        event_type=TraceEventType.TOOL_SELECTED,
        selected_tool="database",
        expected_tool="database",
        tool_selection_correct=True
    )
    assert evt.selected_tool == "database"
    assert evt.tool_selection_correct is True

    # 3. Finish Run
    completed_run = tracer.finish_run(
        run=run,
        final_response="University details retrieved.",
        success=True
    )
    assert completed_run.success is True
    assert completed_run.total_latency_ms >= 0.0