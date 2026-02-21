"""Tests for PromptHistory entity."""
import pytest

from hemdov.domain.entities.prompt_history import PromptHistory


def test_validation_accepts_valid_frameworks():
    """Test that all valid framework names are accepted."""
    valid_frameworks = [
        "chain-of-thought",
        "tree-of-thoughts",
        "decomposition",
        "role-playing"
    ]

    for framework in valid_frameworks:
        history = PromptHistory(
            original_idea="test idea",
            context="test context",
            improved_prompt="test prompt",
            role="test role",
            directive="test directive",
            framework=framework,
            guardrails=["guardrail1"],
            backend="zero-shot",
            model="test-model",
            provider="test-provider"
        )
        assert history.framework == framework


def test_validation_fallback_on_invalid_framework():
    """Test that invalid framework is rejected."""
    with pytest.raises(ValueError, match="Invalid framework"):
        PromptHistory(
            original_idea="test idea",
            context="test context",
            improved_prompt="test prompt",
            role="test role",
            directive="test directive",
            framework="Invalid Framework Name",
            guardrails=["guardrail1"],
            backend="zero-shot",
            model="test-model",
            provider="test-provider"
        )


def test_validation_fallback_on_descriptive_framework():
    """Test that descriptive framework names are rejected."""
    with pytest.raises(ValueError, match="Invalid framework"):
        PromptHistory(
            original_idea="test idea",
            context="test context",
            improved_prompt="test prompt",
            role="test role",
            directive="test directive",
            framework="Chain of Thought Reasoning",
            guardrails=["guardrail1"],
            backend="zero-shot",
            model="test-model",
            provider="test-provider"
        )


def test_validation_raises_on_invalid_framework_without_fallback():
    """Invalid framework should fail fast instead of silently defaulting."""
    with pytest.raises(ValueError, match="Invalid framework"):
        PromptHistory(
            original_idea="test idea",
            context="test context",
            improved_prompt="test prompt",
            role="test role",
            directive="test directive",
            framework="Invalid Framework Name",
            guardrails=["guardrail1"],
            backend="zero-shot",
            model="test-model",
            provider="test-provider"
        )
