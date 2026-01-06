# tests/test_strategies/test_simple_strategy.py
from unittest.mock import Mock, patch
import dspy
from eval.src.strategies.simple_strategy import SimpleStrategy


def test_simple_strategy_has_name():
    strategy = SimpleStrategy()
    assert strategy.name == "simple"


def test_simple_strategy_produces_short_output():
    strategy = SimpleStrategy()
    # Mock the DSPy improver to avoid needing actual LM configuration
    mock_prediction = dspy.Prediction(
        improved_prompt="You are a helpful assistant designed to engage in meaningful conversations.",
        role="Helpful Assistant",
        directive="Be helpful and concise",
        framework="General assistance",
        guardrails=["Be polite", "Stay on topic"]
    )
    strategy.improver = Mock(return_value=mock_prediction)

    result = strategy.improve("hola mundo", "")
    assert len(result.improved_prompt) <= 800
    assert hasattr(result, 'role')
    assert hasattr(result, 'directive')


def test_simple_strategy_truncates_long_output():
    """Test that long outputs are truncated at sentence boundaries."""
    strategy = SimpleStrategy(max_length=100)

    # Create a mock prediction that exceeds the max length
    long_text = "This is sentence one. " * 20  # Much longer than 100 chars
    mock_prediction = dspy.Prediction(
        improved_prompt=long_text,
        role="Assistant",
        directive="Help",
        framework="General",
        guardrails=["Be polite"]
    )
    strategy.improver = Mock(return_value=mock_prediction)

    result = strategy.improve("test", "")
    # Should be truncated to <= 100 chars
    assert len(result.improved_prompt) <= 100
    # Should end with ... if no clean sentence boundary found
    # or end at a sentence boundary if one exists
