from typing import Any, Dict, List, Optional
import pandas as pd
from storage.database import get_db_connection
from tracing.events import ErrorType

class ReliabilityAnalyzer:
    """Pandas-based analysis engine computing reliability, latency, tool accuracy, and failure taxonomy metrics."""

    def __init__(self):
        pass

    def _get_runs_df(self) -> pd.DataFrame:
        """Loads all agent_runs from SQLite into a Pandas DataFrame."""
        with get_db_connection() as conn:
            query = "SELECT * FROM agent_runs;"
            df = pd.read_sql_query(query, conn)
            return df

    def _get_events_df(self) -> pd.DataFrame:
        """Loads all trace_events from SQLite into a Pandas DataFrame."""
        with get_db_connection() as conn:
            query = "SELECT * FROM trace_events;"
            df = pd.read_sql_query(query, conn)
            return df

    def compute_overall_metrics(self) -> Dict[str, Any]:
        """Calculates macro system-level reliability and latency metrics."""
        df_runs = self._get_runs_df()
        
        if df_runs.empty:
            return {
                "total_runs": 0,
                "successful_runs": 0,
                "failed_runs": 0,
                "success_rate": 0.0,
                "failure_rate": 0.0,
                "avg_latency_ms": 0.0,
                "avg_steps": 0.0,
                "retry_rate": 0.0
            }

        total_runs = len(df_runs)
        successful_runs = int(df_runs["success"].sum())
        failed_runs = total_runs - successful_runs
        success_rate = (successful_runs / total_runs) * 100.0
        failure_rate = (failed_runs / total_runs) * 100.0
        avg_latency_ms = float(df_runs["total_latency_ms"].mean())
        avg_steps = float(df_runs["total_steps"].mean())

        # Retry Rate computation from events
        df_events = self._get_events_df()
        runs_with_retries = 0
        if not df_events.empty and "retry_count" in df_events.columns:
            runs_with_retries = df_events[df_events["retry_count"] > 0]["run_id"].nunique()
        
        retry_rate = (runs_with_retries / total_runs) * 100.0 if total_runs > 0 else 0.0

        return {
            "total_runs": total_runs,
            "successful_runs": successful_runs,
            "failed_runs": failed_runs,
            "success_rate": round(success_rate, 2),
            "failure_rate": round(failure_rate, 2),
            "avg_latency_ms": round(avg_latency_ms, 2),
            "avg_steps": round(avg_steps, 2),
            "retry_rate": round(retry_rate, 2)
        }

    def compute_tool_metrics(self) -> Dict[str, Any]:
        """Computes usage, failure rate, and execution latency grouped per tool."""
        df_events = self._get_events_df()
        
        if df_events.empty or "tool_name" not in df_events.columns:
            return {}

        # Filter events where a tool was actually invoked or completed
        tool_events = df_events[df_events["tool_name"].notna() & (df_events["tool_name"] != "")].copy()
        
        if tool_events.empty:
            return {}

        tool_stats = {}
        for tool_name, group in tool_events.groupby("tool_name"):
            total_calls = len(group[group["event_type"] == "TOOL_STARTED"])
            failed_calls = len(group[group["event_type"] == "TOOL_FAILED"])
            succeeded_calls = len(group[group["event_type"] == "TOOL_SUCCEEDED"])
            
            # Prevent division by zero
            denom = total_calls if total_calls > 0 else (succeeded_calls + failed_calls)
            failure_rate = (failed_calls / denom * 100.0) if denom > 0 else 0.0
            
            avg_latency = float(group["latency_ms"].mean()) if "latency_ms" in group.columns else 0.0

            tool_stats[tool_name] = {
                "total_calls": denom,
                "succeeded_calls": succeeded_calls,
                "failed_calls": failed_calls,
                "failure_rate": round(failure_rate, 2),
                "avg_latency_ms": round(avg_latency, 2)
            }

        return tool_stats

    def compute_tool_selection_accuracy(self) -> Dict[str, Any]:
        """Calculates LLM Tool Selection Accuracy based on ground-truth expected tools."""
        df_events = self._get_events_df()
        
        if df_events.empty or "tool_selection_correct" not in df_events.columns:
            return {"total_evaluated": 0, "accuracy": 0.0}

        evaluated = df_events[df_events["tool_selection_correct"].notna()].copy()
        
        if evaluated.empty:
            return {"total_evaluated": 0, "accuracy": 0.0}

        total_evaluated = len(evaluated)
        correct_selections = int(evaluated["tool_selection_correct"].sum())
        accuracy = (correct_selections / total_evaluated) * 100.0 if total_evaluated > 0 else 0.0

        return {
            "total_evaluated": total_evaluated,
            "correct_selections": correct_selections,
            "incorrect_selections": total_evaluated - correct_selections,
            "accuracy": round(accuracy, 2)
        }

    def compute_failure_taxonomy(self) -> Dict[str, int]:
        """Distribution of system runs broken down by primary failure classification."""
        df_runs = self._get_runs_df()
        
        if df_runs.empty or "primary_failure_type" not in df_runs.columns:
            return {}

        failed_runs = df_runs[df_runs["success"] == 0]
        if failed_runs.empty:
            return {}

        counts = failed_runs["primary_failure_type"].value_counts().to_dict()
        return {str(k): int(v) for k, v in counts.items() if k != "NONE"}