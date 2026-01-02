"""Tests for few-shot learning components."""
from pathlib import Path


def test_example_pool_from_train_set():
    """Should build example pool from train set"""
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))

    from scripts.data.fewshot.example_pool import ExamplePool

    train = [
        {"question": "test 1", "metadata": {"domain": "SOFTDEV", "confidence": 0.8}},
        {"question": "test 2", "metadata": {"domain": "AIML", "confidence": 0.6}}
    ]

    pool = ExamplePool()
    pool.build(train)

    assert len(pool.examples) == 2, f"Expected 2 examples, got {len(pool.examples)}"
    assert pool.has_domain("SOFTDEV"), "Should have SOFTDEV domain"
    assert pool.has_domain("AIML"), "Should have AIML domain"
