import sqlite3
from pathlib import Path
from config import settings

def get_db_connection() -> sqlite3.Connection:
    """Creates a database connection with timeout handling to avoid database locks."""
    settings.DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    # timeout=20.0 prevents 'database is locked' errors under rapid test runs
    conn = sqlite3.connect(str(settings.DATABASE_PATH), timeout=20.0)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initializes the database schema for runs and trace events."""
    with get_db_connection() as conn:
        cursor = conn.cursor()

        # Agent Runs Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS agent_runs (
            run_id TEXT PRIMARY KEY,
            user_prompt TEXT NOT NULL,
            start_time TEXT NOT NULL,
            end_time TEXT,
            total_latency_ms REAL DEFAULT 0.0,
            total_steps INTEGER DEFAULT 0,
            final_response TEXT,
            status TEXT NOT NULL,
            success INTEGER DEFAULT 0,
            primary_failure_type TEXT,
            primary_failure_step INTEGER
        );
        """)

        # Trace Events Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS trace_events (
            event_id TEXT PRIMARY KEY,
            run_id TEXT NOT NULL,
            step_number INTEGER NOT NULL,
            event_type TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            tool_name TEXT,
            tool_input TEXT,
            tool_output TEXT,
            expected_tool TEXT,
            selected_tool TEXT,
            tool_selection_correct INTEGER,
            status TEXT NOT NULL,
            error_type TEXT,
            error_message TEXT,
            retry_count INTEGER DEFAULT 0,
            latency_ms REAL DEFAULT 0.0,
            FOREIGN KEY (run_id) REFERENCES agent_runs (run_id) ON DELETE CASCADE
        );
        """)
        conn.commit()