import json
from pathlib import Path
from typing import Any, Dict, List
from config import BASE_DIR

class BenchmarkDataset:
    """Benchmark Dataset Loader managing evaluation prompt specs."""

    def __init__(self, dataset_path: Path = BASE_DIR / "evaluation" / "dataset.json"):
        self.dataset_path = dataset_path

    def load(self) -> List[Dict[str, Any]]:
        """Loads evaluation dataset cases from JSON file."""
        if not self.dataset_path.exists():
            raise FileNotFoundError(f"Benchmark dataset file missing at: {self.dataset_path}")
            
        with open(self.dataset_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data