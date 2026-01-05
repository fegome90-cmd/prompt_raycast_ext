"""Tests for dataset gate evaluation script."""
import pytest
import json
import tempfile
from pathlib import Path
from scripts.eval.evaluate_dataset_gates import evaluate_dataset, _calculate_statistics, _get_nested_value

def test_evaluator_exists():
    """Test evaluator script can be imported."""
    assert callable(evaluate_dataset)

def test_evaluator_returns_results():
    """Test evaluator returns results dict with expected keys and values."""
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
    assert "skipped_indices" in results  # New field for tracking skips

    # Check actual values (not just structure)
    assert results["total_evaluated"] >= 0
    assert results["skipped_count"] >= 0
    assert isinstance(results["skipped_indices"], list)
    assert results["v0_1_pass_count"] >= 0
    assert results["v0_1_pass_count"] <= results["total_evaluated"]
    assert isinstance(results["individual_results"], list)
    assert len(results["individual_results"]) == results["total_evaluated"]


def test_evaluator_handles_missing_dataset_file():
    """Test evaluator raises FileNotFoundError for bad path."""
    with pytest.raises(SystemExit) as exc_info:
        evaluate_dataset(
            dataset_path="nonexistent.json",
            template_id="example_md"
        )
    # SystemExit(1) indicates error
    assert exc_info.value.code == 1


def test_evaluator_handles_malformed_json():
    """Test evaluator handles JSON decode errors."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        f.write("{ invalid json }")
        temp_path = f.name

    try:
        with pytest.raises(SystemExit) as exc_info:
            evaluate_dataset(dataset_path=temp_path, template_id="example_md")
        assert exc_info.value.code == 1
    finally:
        Path(temp_path).unlink(missing_ok=True)


def test_calculate_statistics_empty_dataset():
    """Test zero division protection in statistics calculation."""
    result = _calculate_statistics({
        "total_evaluated": 0,
        "v0_1_pass_count": 0,
        "v0_2_fail_counts": {},
        "v0_2_warn_counts": {}
    })
    assert result == {}


def test_calculate_statistics_normal_case():
    """Test statistics calculation with normal data."""
    result = _calculate_statistics({
        "total_evaluated": 10,
        "v0_1_pass_count": 5,
        "v0_2_fail_counts": {"A1_filler": 3},
        "v0_2_warn_counts": {"A1_filler": 2}
    })
    assert result["v0_1_pass_rate"] == 0.5
    assert result["A1_filler_fail_rate"] == 0.3
    assert result["A1_filler_warn_rate"] == 0.2


def test_get_nested_value_basic():
    """Test _get_nested_value with simple dot notation."""
    data = {"outputs": {"improved_prompt": "Hello world"}}
    result = _get_nested_value(data, "outputs.improved_prompt")
    assert result == "Hello world"


def test_get_nested_value_missing_key():
    """Test _get_nested_value with missing intermediate key."""
    data = {"outputs": {"improved_prompt": "Hello"}}
    result = _get_nested_value(data, "outputs.nonexistent.key")
    assert result is None


def test_get_nested_value_non_dict_value():
    """Test _get_nested_value when intermediate value is not a dict."""
    data = {"outputs": "string value"}
    result = _get_nested_value(data, "outputs.improved_prompt")
    assert result is None


def test_get_nested_value_empty_string():
    """Test _get_nested_value returns empty string as-is."""
    data = {"outputs": {"improved_prompt": ""}}
    result = _get_nested_value(data, "outputs.improved_prompt")
    assert result == ""
