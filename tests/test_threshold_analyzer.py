"""Tests for threshold analysis script."""
import pytest
import json

def test_analyzer_exists():
    """Test analyzer can be imported."""
    from scripts.eval.analyze_thresholds import analyze_thresholds
    assert callable(analyze_thresholds)

def test_analyzer_identifies_threshold_issues():
    """Test analyzer identifies thresholds with high fail rates."""
    from scripts.eval.analyze_thresholds import analyze_thresholds

    # Mock results with high fail rate for P1 gate
    mock_results = {
        "total_evaluated": 100,
        "v0_2_fail_counts": {"P1_steps": 60},  # 60% fail rate
        "gate_statistics": {"P1_steps_fail_rate": 0.6}
    }

    recommendations = analyze_thresholds(mock_results)

    assert "P1_steps" in recommendations
    assert recommendations["P1_steps"]["issue"] == "high_fail_rate"
