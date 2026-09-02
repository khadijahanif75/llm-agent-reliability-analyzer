import random
import time
from typing import Dict, List, Optional
from tools.base import BaseTool, ToolResult
from tracing.events import ErrorType

# Controlled Mock Search KB
MOCK_SEARCH_KNOWLEDGE_BASE = {
    "canada": "Canada is a country in North America. Its population is approximately 40 million as of recent estimates.",
    "python": "Python is a high-level, general-purpose programming language released in 1991 by Guido van Rossum.",
    "celine dion": "Celine Dion is a famous Canadian singer known for hits like 'My Heart Will Go On'.",
    "ai agent": "An AI agent is a software entity that perceives its environment and takes actions using tools to achieve goals.",
    "dubai": "Dubai is the most populous city in the United Arab Emirates, known for modern architecture and luxury tourism."
}

class SearchTool(BaseTool):
    def __init__(
        self,
        failure_rate: float = 0.0,
        timeout_rate: float = 0.0,
        seed: Optional[int] = None
    ):
        super().__init__(
            name="search",
            description="Searches external knowledge sources for facts, statistics, and general knowledge."
        )
        self.failure_rate = failure_rate
        self.timeout_rate = timeout_rate
        if seed is not None:
            random.seed(seed)

    def _run(self, query: str) -> ToolResult:
        if not query or not isinstance(query, str):
            return ToolResult(
                tool_name=self.name,
                success=False,
                error_type=ErrorType.INVALID_TOOL_INPUT,
                error_message="Query parameter must be a non-empty string."
            )

        # 1. Controlled Failure Injection: Timeout
        if random.random() < self.timeout_rate:
            time.sleep(0.1)  # Simulate delay
            return ToolResult(
                tool_name=self.name,
                success=False,
                error_type=ErrorType.TIMEOUT,
                error_message="Search service request timed out after 5000ms."
            )

        # 2. Controlled Failure Injection: Execution Error
        if random.random() < self.failure_rate:
            return ToolResult(
                tool_name=self.name,
                success=False,
                error_type=ErrorType.TOOL_EXECUTION_ERROR,
                error_message="Search provider connection failed (HTTP 503)."
            )

        # 3. Query Execution
        query_lower = query.lower()
        results = []
        for key, snippet in MOCK_SEARCH_KNOWLEDGE_BASE.items():
            if key in query_lower or any(word in query_lower for word in key.split()):
                results.append({"title": key.title(), "snippet": snippet})

        if not results:
            return ToolResult(
                tool_name=self.name,
                success=True,  # Execution worked, but yielded no data
                output=[],
                error_type=ErrorType.EMPTY_RESULT,
                error_message="No matching results found in knowledge base."
            )

        return ToolResult(
            tool_name=self.name,
            success=True,
            output=results
        )