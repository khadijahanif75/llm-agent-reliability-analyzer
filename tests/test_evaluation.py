from evaluation.evaluator import BenchmarkDataset

def test_benchmark_dataset_loading():
    dataset = BenchmarkDataset()
    items = dataset.load()
    assert len(items) >= 10
    assert "prompt" in items[0]
    assert "expected_tool" in items[0]