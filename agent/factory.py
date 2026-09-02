from agent.llm_client import BaseLLMProvider
from agent.mock_llm import MockLLMProvider
from agent.real_llm import RealLLMProvider
from typing import Optional
from config import settings

def get_llm_provider(provider_type: Optional[str] = None) -> BaseLLMProvider:
    """Factory function to instantiate the configured LLM provider."""
    p_type = provider_type or settings.LLM_PROVIDER
    p_type = p_type.lower()
    
    if p_type == "mock":
        return MockLLMProvider(model_name=settings.LLM_MODEL)
    elif p_type in ["openai", "real"]:
        return RealLLMProvider(api_key=settings.LLM_API_KEY, model_name=settings.LLM_MODEL)
    else:
        raise ValueError(f"Unknown LLM Provider: {p_type}. Supported options: 'mock', 'openai'")