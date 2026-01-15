"""
Tests for PromptHistory validation.

Tests that invalid framework raises ValueError (breaking change).
"""

import pytest
from dataclasses import FrozenInstanceError
from hemdov.domain.entities.prompt_history import PromptHistory


def test_invalid_framework_raises_value_error():
    """
    Test that invalid framework raises ValueError.

    BREAKING CHANGE: Previously this would silently default to 'chain-of-thought'.
    After Task 2, it raises ValueError. Ensure existing data is migrated first.
    """
    with pytest.raises(ValueError) as exc_info:
        PromptHistory(
            original_idea="Test idea",
            context="",
            improved_prompt="Improved prompt",
            role="Developer",
            directive="Write code",
            framework="invalid-framework",
            guardrails=["guardrail1"],
            backend="zero-shot",
            model="claude-haiku-4-5",
            provider="anthropic",
            confidence=0.8,
            latency_ms=1000
        )

    assert "Invalid framework" in str(exc_info.value)


def test_valid_frameworks_accepted():
    """Test that all valid frameworks are accepted."""
    from hemdov.domain.metrics.dimensions import FrameworkType

    for framework in [f.value for f in FrameworkType]:
        history = PromptHistory(
            original_idea="Test idea",
            context="",
            improved_prompt="Improved prompt",
            role="Developer",
            directive="Write code",
            framework=framework,
            guardrails=["guardrail1"],
            backend="zero-shot",
            model="claude-haiku-4-5",
            provider="anthropic",
            confidence=0.8,
            latency_ms=1000
        )
        assert history.framework == framework


def test_frozen_instance_cannot_be_modified():
    """Verify PromptHistory is truly frozen."""
    history = PromptHistory(
        original_idea="Test idea",
        context="",
        improved_prompt="Improved prompt",
        role="Developer",
        directive="Write code",
        framework="chain-of-thought",
        guardrails=["guardrail1"],
        backend="zero-shot",
        model="claude-haiku-4-5",
        provider="anthropic",
        confidence=0.8,
        latency_ms=1000
    )

    with pytest.raises(FrozenInstanceError):
        history.original_idea = "Modified"
