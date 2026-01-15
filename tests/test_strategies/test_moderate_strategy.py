# tests/test_strategies/test_moderate_strategy.py
from unittest.mock import Mock

import dspy

from eval.src.strategies.moderate_strategy import ModerateStrategy


def test_moderate_strategy_has_name():
    strategy = ModerateStrategy()
    assert strategy.name == "moderate"


def test_moderate_strategy_allows_more_length():
    strategy = ModerateStrategy()
    # Mock the DSPy improver
    mock_prediction = dspy.Prediction(
        improved_prompt="Create a comprehensive prompt for software quality evaluation with metrics, testing strategies, and best practices.",
        role="Quality Specialist",
        directive="Design quality framework",
        framework="Software Quality Assurance",
        guardrails=["Be thorough", "Include examples"]
    )
    strategy.improver = Mock(return_value=mock_prediction)

    result = strategy.improve("crea un prompt para evaluar calidad de software", "")
    # Moderate allows up to 2000 chars
    assert len(result.improved_prompt) <= 2000
