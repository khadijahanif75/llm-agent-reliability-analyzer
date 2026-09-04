from agent.agent import AgentLoop
from analysis.reliability import ReliabilityAnalyzer
from evaluation.experiment_runner import ExperimentRunner
from storage.database import init_db

def test_complete_end_to_end_system_pipeline():
    # 1. Initialize Storage
    init_db()
    
    # 2. Run Single Agent Execution
    agent = AgentLoop()
    run = agent.run("Calculate 50 * 20", expected_tool="calculator")
    assert run.success is True
    assert "1000" in run.final_response

    # 3. Run Batch Benchmark Experiment
    runner = ExperimentRunner(max_retries=1, max_steps=4)
    exp_report = runner.run_experiment("E2E_TEST_EXP")
    assert exp_report["total_eval_cases"] >= 10
    assert exp_report["metrics"]["total_runs"] >= 10

    # 4. Verify Analyzer Processing
    analyzer = ReliabilityAnalyzer()
    metrics = analyzer.compute_overall_metrics()
    assert metrics["total_runs"] > 0
    assert metrics["success_rate"] >= 0.0