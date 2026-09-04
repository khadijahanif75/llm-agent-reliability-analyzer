import json
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from evaluation.experiment_runner import ExperimentRunner

def main():
    print("==================================================")
    print(" Launching Benchmark Experiment Suite...")
    print("==================================================")
    
    runner = ExperimentRunner(
        max_retries=2,
        max_steps=6,
        search_failure_rate=0.10,
        search_timeout_rate=0.10
    )
    
    results = runner.run_experiment(experiment_name="EXP_BASELINE_001")
    
    print("\n---------------- EXPERIMENT REPORT ----------------")
    print(json.dumps(results, indent=2))
    print("---------------------------------------------------\n")

if __name__ == "__main__":
    main()