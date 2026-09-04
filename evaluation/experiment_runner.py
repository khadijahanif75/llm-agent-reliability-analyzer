import time
from typing import Any, Dict, List, Optional
from agent.agent import AgentLoop
from analysis.reliability import ReliabilityAnalyzer
from evaluation.evaluator import BenchmarkDataset
from storage.database import init_db
from tools.calculator import CalculatorTool
from tools.database import DatabaseTool
from tools.search import SearchTool

class ExperimentRunner:
    """Batch experiment orchestrator executing benchmark suites across agent configurations."""

    def __init__(
        self,
        max_retries: int = 2,
        max_steps: int = 6,
        search_failure_rate: float = 0.0,
        search_timeout_rate: float = 0.0,
        database_failure_rate: float = 0.0,
        seed: Optional[int] = 42
    ):
        init_db()
        self.max_retries = max_retries
        self.max_steps = max_steps
        
        # Configure Tools with Failure Injection Settings
        self.tools = [
            CalculatorTool(),
            SearchTool(
                failure_rate=search_failure_rate,
                timeout_rate=search_timeout_rate,
                seed=seed
            ),
            DatabaseTool(failure_rate=database_failure_rate)
        ]
        
        self.agent = AgentLoop(
            max_steps=self.max_steps,
            max_retries=self.max_retries,
            tools=self.tools
        )
        self.dataset_loader = BenchmarkDataset()
        self.analyzer = ReliabilityAnalyzer()

    def run_experiment(self, experiment_name: str = "default_experiment") -> Dict[str, Any]:
        """Executes full benchmark suite and returns consolidated experiment reliability report."""
        dataset = self.dataset_loader.load()
        start_time = time.time()
        
        run_ids = []
        for case in dataset:
            prompt = case["prompt"]
            expected_tool = case.get("expected_tool")
            run = self.agent.run(user_prompt=prompt, expected_tool=expected_tool)
            run_ids.append(run.run_id)

        duration = time.time() - start_time
        
        # Extract aggregate metrics from Analyzer
        overall = self.analyzer.compute_overall_metrics()
        tool_metrics = self.analyzer.compute_tool_metrics()
        accuracy = self.analyzer.compute_tool_selection_accuracy()
        taxonomy = self.analyzer.compute_failure_taxonomy()

        return {
            "experiment_name": experiment_name,
            "total_eval_cases": len(dataset),
            "execution_duration_sec": round(duration, 2),
            "config": {
                "max_retries": self.max_retries,
                "max_steps": self.max_steps
            },
            "metrics": overall,
            "tool_selection_accuracy": accuracy,
            "tool_metrics": tool_metrics,
            "failure_taxonomy": taxonomy
        }