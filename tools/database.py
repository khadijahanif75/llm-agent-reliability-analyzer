import sqlite3
from typing import Any, Dict, Optional
from tools.base import BaseTool, ToolResult
from storage.database import get_db_connection
from tracing.events import ErrorType

class DatabaseTool(BaseTool):
    def __init__(self, failure_rate: float = 0.0):
        super().__init__(
            name="database",
            description="Queries internal system records for student profiles, course statistics, and universities."
        )
        self.failure_rate = failure_rate
        self._seed_demo_tables()

    def _seed_demo_tables(self):
        """Ensures lightweight reference tables exist for demo queries."""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS students (
            student_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            major TEXT NOT NULL,
            gpa REAL
        );
        """)
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS universities (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            country TEXT NOT NULL,
            rank INTEGER
        );
        """)
        
        # Seed dummy data if empty
        cursor.execute("SELECT COUNT(*) FROM students;")
        if cursor.fetchone()[0] == 0:
            cursor.executemany("INSERT INTO students VALUES (?, ?, ?, ?);", [
                ("101", "Amina Khan", "Data Science", 3.85),
                ("102", "Liam Smith", "Computer Science", 3.60),
                ("103", "Sophia Chen", "Data Science", 3.92)
            ])
            cursor.executemany("INSERT INTO universities VALUES (?, ?, ?, ?);", [
                ("u1", "University of Toronto", "Canada", 21),
                ("u2", "University of Waterloo", "Canada", 112),
                ("u3", "University Alpha", "Canada", 45)
            ])
        
        conn.commit()
        conn.close()

    def _run(self, table: str, query_key: str, query_value: str) -> ToolResult:
        if table not in ["students", "universities"]:
            return ToolResult(
                tool_name=self.name,
                success=False,
                error_type=ErrorType.INVALID_TOOL_INPUT,
                error_message=f"Access denied or invalid table '{table}'. Supported tables: students, universities."
            )

        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Safe parameterized query prevents SQL Injection
            sql = f"SELECT * FROM {table} WHERE {query_key} LIKE ?"
            cursor.execute(sql, (f"%{query_value}%",))
            rows = cursor.fetchall()
            conn.close()

            if not rows:
                return ToolResult(
                    tool_name=self.name,
                    success=True,
                    output=[],
                    error_type=ErrorType.EMPTY_RESULT,
                    error_message=f"No records found in '{table}' where {query_key} matches '{query_value}'."
                )

            # Convert SQLite Row objects to list of dicts
            result_dicts = [dict(row) for row in rows]
            return ToolResult(
                tool_name=self.name,
                success=True,
                output=result_dicts
            )
        except sqlite3.OperationalError as e:
            return ToolResult(
                tool_name=self.name,
                success=False,
                error_type=ErrorType.DATABASE_ERROR,
                error_message=f"Database execution error: {str(e)}"
            )
        except Exception as e:
            return ToolResult(
                tool_name=self.name,
                success=False,
                error_type=ErrorType.TOOL_EXECUTION_ERROR,
                error_message=f"Unexpected error: {str(e)}"
            )