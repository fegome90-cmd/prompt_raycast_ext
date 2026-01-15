"""Tests for threshold analysis script."""
from scripts.eval.analyze_thresholds import analyze_thresholds


def test_analyzer_exists():
    """Test analyzer can be imported."""
    assert callable(analyze_thresholds)

def test_analyzer_identifies_threshold_issues():
    """Test analyzer identifies thresholds with high fail rates."""
    # Mock results with high fail rate for P1 gate
    mock_results = {
        "total_evaluated": 100,
        "v0_2_fail_counts": {"P1_steps": 60},  # 60% fail rate
        "gate_statistics": {"P1_steps_fail_rate": 0.6}
    }

    recommendations = analyze_thresholds(mock_results)

    assert "P1_steps" in recommendations
    assert recommendations["P1_steps"]["issue"] == "high_fail_rate"


def test_analyzer_threshold_boundaries():
    """Test behavior at exact threshold boundaries (50%, 70%)."""
    # Test just below 50% - should NOT be flagged
    mock_results_49 = {
        "total_evaluated": 100,
        "gate_statistics": {"P1_steps_fail_rate": 0.49}
    }
    rec_49 = analyze_thresholds(mock_results_49)
    assert "P1_steps" not in rec_49, "Fail rate at 49% should not trigger recommendation"

    # Test at exactly 50% - should be flagged
    mock_results_50 = {
        "total_evaluated": 100,
        "gate_statistics": {"P1_steps_fail_rate": 0.50}
    }
    rec_50 = analyze_thresholds(mock_results_50)
    assert "P1_steps" in rec_50, "Fail rate at 50% should trigger recommendation"

    # Test just above 50% - should be flagged
    mock_results_51 = {
        "total_evaluated": 100,
        "gate_statistics": {"P1_steps_fail_rate": 0.51}
    }
    rec_51 = analyze_thresholds(mock_results_51)
    assert "P1_steps" in rec_51, "Fail rate at 51% should trigger recommendation"

    # Test warn rate threshold at exactly 70%
    mock_results_70 = {
        "total_evaluated": 100,
        "gate_statistics": {"P1_steps_warn_rate": 0.70}
    }
    rec_70 = analyze_thresholds(mock_results_70)
    assert "P1_steps" in rec_70, "Warn rate at 70% should trigger recommendation"


def test_analyzer_handles_missing_gate_statistics():
    """Test analyzer validates input structure."""
    mock_results = {
        "total_evaluated": 100,
        # Missing gate_statistics
    }

    recommendations = analyze_thresholds(mock_results)

    assert "error" in recommendations
    assert "gate_statistics" in recommendations["error"]


def test_analyzer_handles_empty_data():
    """Test analyzer handles zero total evaluated."""
    mock_results = {
        "total_evaluated": 0,
        "gate_statistics": {}
    }

    recommendations = analyze_thresholds(mock_results)

    assert "error" in recommendations
