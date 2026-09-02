import time
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from pydantic import BaseModel
from tracing.events import ErrorType

class ToolResult(BaseModel):
    tool_name: str
    success: bool
    output: Any = None
    error_type: ErrorType = ErrorType.NONE
    error_message: Optional[str] = None
    latency_ms: float = 0.0

class BaseTool(ABC):
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description

    @abstractmethod
    def _run(self, **kwargs) -> Any:
        """Internal execution method implemented by specific tools."""
        pass

    def execute(self, **kwargs) -> ToolResult:
        """Wrapper method handling execution timing and top-level error capture."""
        start_time = time.perf_counter()
        try:
            result = self._run(**kwargs)
            latency = (time.perf_counter() - start_time) * 1000
            
            if isinstance(result, ToolResult):
                result.latency_ms = latency
                return result
                
            return ToolResult(
                tool_name=self.name,
                success=True,
                output=result,
                latency_ms=latency
            )
        except Exception as e:
            latency = (time.perf_counter() - start_time) * 1000
            return ToolResult(
                tool_name=self.name,
                success=False,
                error_type=ErrorType.TOOL_EXECUTION_ERROR,
                error_message=str(e),
                latency_ms=latency
            )