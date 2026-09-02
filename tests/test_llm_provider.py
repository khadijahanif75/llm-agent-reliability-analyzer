import pytest
from agent.factory import get_llm_provider
from agent.mock_llm import MockLLMProvider
from tracing.models import LLMAction

def test_mock_llm_calculator_decision():
    provider = MockLLMProvider()
    action = provider.decide("What is 345 multiplied by 72?", history=[])
    assert isinstance(action, LLMAction)
    assert action.action == "calculator"
    assert "expression" in action.arguments

def test_mock_llm_search_decision():
    provider = MockLLMProvider()
    action = provider.decide("Search for information about Celine Dion", history=[])
    assert action.action == "search"
    assert "query" in action.arguments

def test_mock_llm_database_decision():
    provider = MockLLMProvider()
    action = provider.decide("Find the university record for Toronto", history=[])
    assert action.action == "database"
    assert action.arguments.get("table") == "universities"

def test_mock_llm_factory():
    provider = get_llm_provider("mock")
    assert isinstance(provider, MockLLMProvider)