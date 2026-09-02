import json
import sqlite3
from typing import List, Optional
from storage.database import get_db_connection
from tracing.models import AgentRun, TraceEvent

class TraceRepository:
    def __init__(self):
        pass

    def save_run(self, run: AgentRun) -> None:
        """Saves or updates an AgentRun in SQLite safely using context manager."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO agent_runs (
                run_id, user_prompt, start_time, end_time, total_latency_ms,
                total_steps, final_response, status, success, primary_failure_type, primary_failure_step
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(run_id) DO UPDATE SET
                end_time=excluded.end_time,
                total_latency_ms=excluded.total_latency_ms,
                total_steps=excluded.total_steps,
                final_response=excluded.final_response,
                status=excluded.status,
                success=excluded.success,
                primary_failure_type=excluded.primary_failure_type,
                primary_failure_step=excluded.primary_failure_step
            """, (
                run.run_id,
                run.user_prompt,
                run.start_time.isoformat(),
                run.end_time.isoformat() if run.end_time else None,
                run.total_latency_ms,
                run.total_steps,
                run.final_response,
                run.status.value if hasattr(run.status, 'value') else run.status,
                1 if run.success else 0,
                run.primary_failure_type.value if hasattr(run.primary_failure_type, 'value') else run.primary_failure_type,
                run.primary_failure_step
            ))
            conn.commit()

    def save_event(self, event: TraceEvent) -> None:
        """Saves an individual TraceEvent to SQLite safely using context manager."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO trace_events (
                event_id, run_id, step_number, event_type, timestamp, tool_name,
                tool_input, tool_output, expected_tool, selected_tool,
                tool_selection_correct, status, error_type, error_message, retry_count, latency_ms
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(event_id) DO UPDATE SET
                status=excluded.status,
                error_type=excluded.error_type,
                error_message=excluded.error_message,
                latency_ms=excluded.latency_ms
            """, (
                event.event_id,
                event.run_id,
                event.step_number,
                event.event_type.value if hasattr(event.event_type, 'value') else event.event_type,
                event.timestamp.isoformat(),
                event.tool_name,
                json.dumps(event.tool_input) if event.tool_input else None,
                json.dumps(event.tool_output) if isinstance(event.tool_output, (dict, list)) else str(event.tool_output) if event.tool_output else None,
                event.expected_tool,
                event.selected_tool,
                1 if event.tool_selection_correct else 0 if event.tool_selection_correct is not None else None,
                event.status,
                event.error_type.value if hasattr(event.error_type, 'value') else event.error_type,
                event.error_message,
                event.retry_count,
                event.latency_ms
            ))
            conn.commit()