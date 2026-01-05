"""Tests for dataset gate evaluation script."""
import pytest
import json
from pathlib import Path

def test_evaluator_exists():
    """Test evaluator script can be imported."""
    from scripts.eval.evaluate_dataset_gates import evaluate_dataset
    assert callable(evaluate_dataset)

def test_evaluator_returns_results():
    """Test evaluator returns results dict with expected keys."""
    from scripts.eval.evaluate_dataset_gates import evaluate_dataset

    results = evaluate_dataset(
        dataset_path="datasets/exports/fewshot-train.json",
        output_field="outputs.improved_prompt",
        template_id="example_md",
        limit=5
    )

    # Check structure
    assert isinstance(results, dict)
    assert "total_evaluated" in results
    assert "v0_1_pass_count" in results
    assert "v0_2_fail_counts" in results
    assert "gate_statistics" in results
