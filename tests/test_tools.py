import pytest
from tools.calculator import CalculatorTool
from tools.search import SearchTool
from tools.database import DatabaseTool
from tracing.events import ErrorType

def test_calculator_success():
    calc = CalculatorTool()
    res = calc.execute(expression="345 * 72")
    assert res.success is True
    assert res.output == 24840

def test_calculator_invalid_expression():
    calc = CalculatorTool()
    res = calc.execute(expression="25 + * 40")
    assert res.success is False
    assert res.error_type == ErrorType.INVALID_TOOL_INPUT

def test_calculator_zero_division():
    calc = CalculatorTool()
    res = calc.execute(expression="100 / 0")
    assert res.success is False
    assert res.error_type == ErrorType.TOOL_EXECUTION_ERROR

def test_search_tool_success():
    search = SearchTool()
    res = search.execute(query="Tell me about Python")
    assert res.success is True
    assert len(res.output) > 0

def test_search_tool_timeout_injection():
    search = SearchTool(timeout_rate=1.0, seed=42)  # Force timeout
    res = search.execute(query="Canada population")
    assert res.success is False
    assert res.error_type == ErrorType.TIMEOUT

def test_database_tool_success():
    db = DatabaseTool()
    res = db.execute(table="students", query_key="name", query_value="Amina")
    assert res.success is True
    assert len(res.output) == 1
    assert res.output[0]["name"] == "Amina Khan"