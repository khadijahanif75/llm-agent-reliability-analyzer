from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from tracing.models import LLMAction

class BaseLLMProvider(ABC):
    """Abstract Base Class for LLM providers."""
    
    def __init__(self, model_name: str):
        self.model_name = model_name

    @abstractmethod
    def decide(
        self,
        user_prompt: str,
        history: List[Dict[str, Any]]
    ) -> LLMAction:
        """
        Determines the next action based on prompt and observation history.
        
        Args:
            user_prompt: Original query from user.
            history: Chronological sequence of step decisions and observations.
            
        Returns:
            LLMAction: Structured action choice (tool call or final answer).
        """
        pass