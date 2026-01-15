"""Tests for PromptHistory entity."""
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
    """Test that invalid framework defaults to chain-of-thought."""
    history = PromptHistory(
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
    # Should fallback to default
    assert history.framework == "chain-of-thought"


def test_validation_fallback_on_descriptive_framework():
    """Test that descriptive framework names fallback to default."""
    history = PromptHistory(
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
    # Should fallback to default
    assert history.framework == "chain-of-thought"


def test_validation_logs_warning_on_invalid_framework(caplog):
    """Test that invalid framework triggers warning log."""
    import logging
    with caplog.at_level(logging.WARNING):
        history = PromptHistory(
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

    assert "Unknown framework 'Invalid Framework Name'" in caplog.text
    assert "defaulting to 'chain-of-thought'" in caplog.text
    assert history.framework == "chain-of-thought"
