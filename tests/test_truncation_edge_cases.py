# tests/test_truncation_edge_cases.py
"""
Edge case tests for truncation logic in strategies.

Tests for:
- No sentence boundaries
- Boundary before/after 70% threshold
- Exactly at 70% threshold
- Multiple boundaries
"""
from unittest.mock import Mock

import dspy
import pytest

from eval.src.strategies.moderate_strategy import ModerateStrategy
from eval.src.strategies.simple_strategy import SimpleStrategy


def test_truncation_with_no_sentence_boundaries():
    """Test truncation when there are no period or newline boundaries."""
    strategy = SimpleStrategy(max_length=100)

    # Mock prediction with no sentence boundaries
    long_text_no_boundaries = "a" * 200  # No periods or newlines
    mock_prediction = dspy.Prediction(
        improved_prompt=long_text_no_boundaries,
        role="Test",
        directive="Test",
        framework="test",
        guardrails=["test"]
    )
    strategy.improver = Mock(return_value=mock_prediction)

    result = strategy.improve("test", "test")

    # Should hard truncate at max_length and add "..."
    # Result is max_length + "..." = 100 + 3 = 103 chars
    assert len(result.improved_prompt) == 103
    # With SimpleStrategy, should end with "..."
    assert result.improved_prompt.endswith("...")


def test_truncation_period_before_70_percent():
    """Test truncation when period appears before 70% threshold."""
    strategy = SimpleStrategy(max_length=100)

    # Period at position 50 (< 70% of 100 = 70)
    text_with_early_period = "a" * 50 + "." + "b" * 100
    mock_prediction = dspy.Prediction(
        improved_prompt=text_with_early_period,
        role="Test",
        directive="Test",
        framework="test",
        guardrails=["test"]
    )
    strategy.improver = Mock(return_value=mock_prediction)

    result = strategy.improve("test", "test")

    # Should NOT use period (before threshold), hard truncate with "..."
    # Result is max_length + "..." = 100 + 3 = 103 chars
    assert len(result.improved_prompt) == 103
    # Since period is before 70%, hard truncation is used
    assert result.improved_prompt.endswith("...")


def test_truncation_period_after_70_percent():
    """Test truncation when period appears after 70% threshold."""
    strategy = SimpleStrategy(max_length=100)

    # Period at position 80 (> 70% of 100 = 70)
    text_with_late_period = "a" * 80 + "." + "b" * 50
    mock_prediction = dspy.Prediction(
        improved_prompt=text_with_late_period,
        role="Test",
        directive="Test",
        framework="test",
        guardrails=["test"]
    )
    strategy.improver = Mock(return_value=mock_prediction)

    result = strategy.improve("test", "test")

    # Should use period (after threshold)
    assert len(result.improved_prompt) <= 100
    # Should include the period
    assert "." in result.improved_prompt
    # Should NOT have "..." since we used period boundary
    assert not result.improved_prompt.endswith("...")


def test_truncation_newline_vs_period_priority():
    """Test that period takes priority over newline."""
    strategy = SimpleStrategy(max_length=100)

    # Both period and newline after 70%, period comes first
    text_with_both = "a" * 75 + "." + "b" * 10 + "\n" + "c" * 50
    mock_prediction = dspy.Prediction(
        improved_prompt=text_with_both,
        role="Test",
        directive="Test",
        framework="test",
        guardrails=["test"]
    )
    strategy.improver = Mock(return_value=mock_prediction)

    result = strategy.improve("test", "test")

    # Period should take priority (appears at 75)
    # Result should end at period, not include newline
    assert "." in result.improved_prompt
    # Should be truncated at or before the period
    assert result.improved_prompt.index(".") < len(result.improved_prompt)


def test_moderate_strategy_no_ellipsis_suffix():
    """Test that ModerateStrategy doesn't add '...' suffix."""
    strategy = ModerateStrategy(max_length=100)

    # No boundaries
    long_text = "a" * 200
    mock_prediction = dspy.Prediction(
        improved_prompt=long_text,
        role="Test",
        directive="Test",
        framework="test",
        guardrails=["test"]
    )
    strategy.improver = Mock(return_value=mock_prediction)

    result = strategy.improve("test", "test")

    # Should truncate at max_length
    assert len(result.improved_prompt) <= 100
    # Should NOT have "..." suffix (different from SimpleStrategy)
    assert not result.improved_prompt.endswith("...")


def test_truncation_exactly_at_max_length():
    """Test when text is exactly at max_length."""
    strategy = SimpleStrategy(max_length=100)

    # Exactly 100 chars, no boundaries
    exact_text = "a" * 100
    mock_prediction = dspy.Prediction(
        improved_prompt=exact_text,
        role="Test",
        directive="Test",
        framework="test",
        guardrails=["test"]
    )
    strategy.improver = Mock(return_value=mock_prediction)

    result = strategy.improve("test", "test")

    # Should return exactly 100 chars (no truncation needed)
    assert len(result.improved_prompt) == 100
    # Should NOT add "..." since no truncation
    assert not result.improved_prompt.endswith("...")


def test_truncation_with_multiple_periods():
    """Test when there are multiple periods, should use last suitable one."""
    strategy = SimpleStrategy(max_length=100)

    # Periods at 40, 85, 95 positions
    # Should use period at 85 (> 70%)
    text_with_periods = "a" * 40 + "." + "b" * 45 + "." + "c" * 10 + "." + "d" * 50
    mock_prediction = dspy.Prediction(
        improved_prompt=text_with_periods,
        role="Test",
        directive="Test",
        framework="test",
        guardrails=["test"]
    )
    strategy.improver = Mock(return_value=mock_prediction)

    result = strategy.improve("test", "test")

    # Should use last period after 70% (position 85)
    # Result length should be around 86 (85 + 1 for period)
    assert len(result.improved_prompt) <= 100
    # Should have period
    assert "." in result.improved_prompt


def test_truncation_input_validation():
    """Test that truncation validates input type."""
    strategy = SimpleStrategy(max_length=100)

    with pytest.raises(TypeError, match="text must be string"):
        strategy._truncate_at_sentence(123, 100)  # type: ignore

    with pytest.raises(TypeError, match="text must be string"):
        strategy._truncate_at_sentence(None, 100)  # type: ignore
