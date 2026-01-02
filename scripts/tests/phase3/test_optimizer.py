"""Tests for DSPy optimizer infrastructure."""
import json
from pathlib import Path


def test_load_phase2_datasets():
    """Should load train/val/test datasets from Phase 2"""
    # Import after path setup
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))

    from scripts.phase3_dspy.optimizer import DatasetLoader

    loader = DatasetLoader()
    train, val, test = loader.load_datasets()

    assert len(train) == 11, f"Expected 11 train examples, got {len(train)}"
    assert len(val) == 2, f"Expected 2 val examples, got {len(val)}"
    assert len(test) == 3, f"Expected 3 test examples, got {len(test)}"
    assert all('question' in ex for ex in train), "All examples must have 'question' field"
