from evaluation.experiment_runner import ExperimentRunner

def test_experiment_runner_batch_execution():
    runner = ExperimentRunner(max_retries=1, max_steps=4)
    results = runner.run_experiment(experiment_name="test_batch_run")
    
    assert results["experiment_name"] == "test_batch_run"
    assert results["total_eval_cases"] >= 10
    assert "metrics" in results
    assert results["metrics"]["total_runs"] >= 10