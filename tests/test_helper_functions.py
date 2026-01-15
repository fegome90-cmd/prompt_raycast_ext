"""
Comprehensive unit tests for Phase 3 helper functions.

Tests cover:
- _calculate_averages() from api/metrics_api.py
- _normalize_guardrails() from api/prompt_improver_api.py
- _extract_confidence() from api/prompt_improver_api.py
"""

import pytest
from unittest.mock import Mock

from api.metrics_api import _calculate_averages
from api.prompt_improver_api import _normalize_guardrails, _extract_confidence


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def mock_metric():
    """Create a mock metric with given scores."""
    def _create(quality: float, performance: float, impact: float) -> Mock:
        metric = Mock()
        metric.quality.composite_score = quality
        metric.performance.performance_score = performance
        metric.impact.impact_score = impact
        return metric
    return _create


# ============================================================================
# Tests for _calculate_averages()
# ============================================================================

class TestCalculateAverages:
    """Test suite for _calculate_averages helper function."""

    def test_calculate_averages_empty_list(self):
        """Empty list returns all zeros."""
        result = _calculate_averages([])
        assert result == {"quality": 0.0, "performance": 0.0, "impact": 0.0}

    def test_calculate_averages_single_metric(self, mock_metric):
        """Single metric returns its own values."""
        mock = mock_metric(0.8, 0.7, 0.9)
        result = _calculate_averages([mock])
        assert result == {"quality": 0.8, "performance": 0.7, "impact": 0.9}

    def test_calculate_averages_multiple_metrics(self, mock_metric):
        """Multiple metrics return averaged values."""
        mock_metric1 = mock_metric(0.8, 0.7, 0.9)
        mock_metric2 = mock_metric(0.6, 0.5, 0.7)
        result = _calculate_averages([mock_metric1, mock_metric2])
        assert result == {"quality": 0.7, "performance": 0.6, "impact": 0.8}

    def test_calculate_averages_three_metrics(self, mock_metric):
        """Test averaging with three metrics."""
        mock_metric1 = mock_metric(1.0, 0.9, 0.8)
        mock_metric2 = mock_metric(0.6, 0.5, 0.4)
        mock_metric3 = mock_metric(0.8, 0.7, 0.6)
        result = _calculate_averages([mock_metric1, mock_metric2, mock_metric3])
        # (1.0 + 0.6 + 0.8) / 3 = 0.8
        # (0.9 + 0.5 + 0.7) / 3 = 0.7
        # (0.8 + 0.4 + 0.6) / 3 = 0.6
        assert result["quality"] == pytest.approx(0.8)
        assert result["performance"] == pytest.approx(0.7)
        assert result["impact"] == 0.6

    def test_calculate_averages_with_zero_values(self, mock_metric):
        """Test averaging with zero values in metrics."""
        mock_metric1 = mock_metric(0.5, 0.0, 0.3)
        mock_metric2 = mock_metric(0.5, 1.0, 0.7)
        result = _calculate_averages([mock_metric1, mock_metric2])
        assert result == {"quality": 0.5, "performance": 0.5, "impact": 0.5}

    def test_calculate_averages_with_extreme_values(self, mock_metric):
        """Test averaging with extreme (0.0 and 1.0) values."""
        mock_metric1 = mock_metric(1.0, 1.0, 1.0)
        mock_metric2 = mock_metric(0.0, 0.0, 0.0)
        result = _calculate_averages([mock_metric1, mock_metric2])
        assert result == {"quality": 0.5, "performance": 0.5, "impact": 0.5}


# ============================================================================
# Tests for _normalize_guardrails()
# ============================================================================

class TestNormalizeGuardrails:
    """Test suite for _normalize_guardrails helper function."""

    @pytest.mark.parametrize("input_str,expected", [
        ("guard1\nguard2\nguard3", ["guard1", "guard2", "guard3"]),
        ("  guard1  \n  guard2  ", ["guard1", "guard2"]),
        ("guard1\n\nguard2\n\n", ["guard1", "guard2"]),
        ("", []),
        ("single_guardrail", ["single_guardrail"]),
        ("   \n   \n   ", []),
        ("guard with spaces\n  another guard  ", ["guard with spaces", "another guard"]),
        ("guard1\n\n  guard2  \nguard3\n\n   ", ["guard1", "guard2", "guard3"]),
    ])
    def test_normalize_guardrails_string_inputs(self, input_str, expected):
        """String inputs are normalized correctly."""
        result = _normalize_guardrails(input_str)
        assert result == expected

    def test_normalize_guardrails_already_list(self):
        """List input is returned as-is."""
        input_list = ["guard1", "guard2"]
        result = _normalize_guardrails(input_list)
        assert result == input_list

    def test_normalize_guardrails_list_with_empty_strings(self):
        """List with empty strings is returned as-is."""
        input_list = ["guard1", "", "guard2"]
        result = _normalize_guardrails(input_list)
        assert result == input_list

    def test_normalize_guardrails_list_with_whitespace(self):
        """List with whitespace items is returned as-is."""
        input_list = ["  guard1  ", "  guard2  "]
        result = _normalize_guardrails(input_list)
        assert result == input_list


# ============================================================================
# Tests for _extract_confidence()
# ============================================================================

class TestExtractConfidence:
    """Test suite for _extract_confidence helper function."""

    @pytest.mark.parametrize("confidence_value,expected", [
        (0.85, 0.85),
        ("0.78", 0.78),
        (1, 1.0),
        (75, 75.0),
        ("8.5e-1", 0.85),
        (0.0, 0.0),
        (1.0, 1.0),
        (None, None),
        ("not_a_number", None),
        ("", None),
        ("   ", None),
    ])
    def test_extract_confidence_from_object_various_values(self, confidence_value, expected):
        """Extract confidence from object with various value types."""
        mock_result = Mock()
        mock_result.confidence = confidence_value
        result = _extract_confidence(mock_result)
        assert result == expected

    def test_extract_confidence_missing_attribute(self):
        """Object without confidence returns None."""
        mock_result = Mock(spec=[])
        result = _extract_confidence(mock_result)
        assert result is None

    @pytest.mark.parametrize("confidence_value,expected", [
        (0.92, 0.92),
        (None, None),
        ("invalid", None),
    ])
    def test_extract_confidence_from_dict_various_values(self, confidence_value, expected):
        """Extract confidence from dict with various value types."""
        mock_result = {"confidence": confidence_value}
        result = _extract_confidence(mock_result)
        assert result == expected

    def test_extract_confidence_dict_without_confidence_key(self):
        """Dict without confidence key returns None."""
        mock_result = {"other_key": "value"}
        result = _extract_confidence(mock_result)
        assert result is None
