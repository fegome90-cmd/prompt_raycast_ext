"""
Tests for exception handling in PromptMetricsCalculator.

Tests that invalid framework strings are logged before defaulting.
"""

import pytest
from hemdov.domain.metrics.evaluators import PromptMetricsCalculator, PromptImprovementResult


def test_invalid_framework_logs_warning(caplog):
    """Test that invalid framework strings are logged before defaulting."""
    result = PromptImprovementResult(
        improved_prompt="Test improved prompt",
        role="Developer",
        directive="Write code",
        framework="invalid-framework-value",  # Invalid
        guardrails=["guardrail1"],
        latency_ms=1000,
        provider="anthropic",
        model="claude-haiku-4-5",
        backend="zero-shot"
    )

    calculator = PromptMetricsCalculator()

    with caplog.at_level("WARNING"):
        metrics = calculator.calculate(
            original_idea="Test idea",
            result=result
        )

    # Verify warning was logged
    assert any(
        "Invalid framework" in record.message
        for record in caplog.records
    ), "Expected warning log for invalid framework"

    # Verify it defaulted to CHAIN_OF_THOUGHT
    from hemdov.domain.metrics.dimensions import FrameworkType
    assert metrics.framework == FrameworkType.CHAIN_OF_THOUGHT


def test_valid_framework_parses_correctly():
    """Test that valid framework strings parse correctly."""
    from hemdov.domain.metrics.dimensions import FrameworkType

    for framework_val in [f.value for f in FrameworkType]:
        result = PromptImprovementResult(
            improved_prompt="Test improved prompt",
            role="Developer",
            directive="Write code",
            framework=framework_val,
            guardrails=["guardrail1"],
            latency_ms=1000,
            provider="anthropic",
            model="claude-haiku-4-5",
            backend="zero-shot"
        )

        calculator = PromptMetricsCalculator()
        metrics = calculator.calculate(
            original_idea="Test idea",
            result=result
        )

        assert metrics.framework.value == framework_val
