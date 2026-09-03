from analysis.reliability import ReliabilityAnalyzer
from agent.agent import AgentLoop
from storage.database import init_db

def test_reliability_analyzer_metrics():
    init_db()
    
    # Run a sample task to ensure database populated
    agent = AgentLoop()
    agent.run("What is 100 * 2?", expected_tool="calculator")
    
    analyzer = ReliabilityAnalyzer()
    
    overall = analyzer.compute_overall_metrics()
    assert overall["total_runs"] > 0
    assert overall["success_rate"] >= 0.0

    tool_metrics = analyzer.compute_tool_metrics()
    assert "calculator" in tool_metrics
    assert tool_metrics["calculator"]["total_calls"] >= 1

    accuracy = analyzer.compute_tool_selection_accuracy()
    assert accuracy["total_evaluated"] >= 1
    assert accuracy["accuracy"] == 100.0