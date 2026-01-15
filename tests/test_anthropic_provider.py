"""Tests for Anthropic provider initialization."""
import os
from unittest.mock import patch

import pytest


@pytest.mark.asyncio
async def test_anthropic_provider_initializes_with_key():
    """Test that Anthropic provider can be initialized with API key."""
    from hemdov.infrastructure.adapters.litellm_dspy_adapter import create_anthropic_adapter

    # Skip if no API key
    api_key = os.getenv("HEMDOV_ANTHROPIC_API_KEY") or os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        pytest.skip("No Anthropic API key configured")

    lm = create_anthropic_adapter(
        model="claude-haiku-4-5-20251001",
        api_key=api_key,
        base_url="https://api.anthropic.com",
        temperature=0.0
    )

    assert lm is not None
    assert hasattr(lm, 'model')
    assert lm.model.startswith("anthropic/")


@pytest.mark.asyncio
async def test_anthropic_adapter_fallback_to_env_keys():
    """Test that Anthropic adapter falls back to environment variables."""
    from hemdov.infrastructure.adapters.litellm_dspy_adapter import create_anthropic_adapter

    # Test with explicit None - should use env vars
    with patch.dict(os.environ, {
        "HEMDOV_ANTHROPIC_API_KEY": "test-key-hemdov",
        "ANTHROPIC_API_KEY": "test-key-anthropic"
    }):
        lm = create_anthropic_adapter(
            model="claude-haiku-4-5-20251001",
            api_key=None,  # Should use env vars
            base_url="https://api.anthropic.com",
            temperature=0.0
        )

        assert lm is not None
        # ANTHROPIC_API_KEY takes precedence over HEMDOV_ANTHROPIC_API_KEY
        assert lm.api_key == "test-key-anthropic"


@pytest.mark.asyncio
async def test_anthropic_adapter_precedence_of_keys():
    """Test API key precedence: explicit > ANTHROPIC_API_KEY > HEMDOV_ANTHROPIC_API_KEY."""
    from hemdov.infrastructure.adapters.litellm_dspy_adapter import create_anthropic_adapter

    # Test explicit key overrides env vars
    with patch.dict(os.environ, {
        "HEMDOV_ANTHROPIC_API_KEY": "test-key-hemdov",
        "ANTHROPIC_API_KEY": "test-key-anthropic"
    }):
        lm = create_anthropic_adapter(
            model="claude-haiku-4-5-20251001",
            api_key="explicit-key",  # Should override env vars
            base_url="https://api.anthropic.com",
            temperature=0.0
        )

        assert lm is not None
        assert lm.api_key == "explicit-key"


def test_anthropic_adapter_model_format():
    """Test that Anthropic adapter formats model name correctly."""
    from hemdov.infrastructure.adapters.litellm_dspy_adapter import create_anthropic_adapter

    with patch.dict(os.environ, {"HEMDOV_ANTHROPIC_API_KEY": "test-key"}):
        lm = create_anthropic_adapter(
            model="claude-haiku-4-5-20251001",
        )

        assert lm.model == "anthropic/claude-haiku-4-5-20251001"


@pytest.mark.asyncio
async def test_anthropic_provider_in_main_lifespan_when_implemented():
    """
    Test that Anthropic provider is handled in main.py lifespan.

    NOTE: This test documents the expected behavior once the Anthropic
    handler is added to main.py. Currently, main.py only supports:
    - ollama, gemini, deepseek, openai

    The Anthropic handler should be added between 'openai' and 'else':
    ```python
    elif provider == "anthropic":
        lm = create_anthropic_adapter(
            model=settings.LLM_MODEL,
            api_key=settings.ANTHROPIC_API_KEY or settings.HEMDOV_ANTHROPIC_API_KEY or settings.LLM_API_KEY,
            base_url=settings.LLM_BASE_URL,
            temperature=temp,
        )
    ```
    """
    from hemdov.infrastructure.adapters.litellm_dspy_adapter import create_anthropic_adapter

    # Verify the adapter function exists and works
    with patch.dict(os.environ, {"HEMDOV_ANTHROPIC_API_KEY": "test-key"}):
        lm = create_anthropic_adapter(
            model="claude-haiku-4-5-20251001",
            api_key="test-key",
            base_url="https://api.anthropic.com",
            temperature=0.0
        )

        assert lm is not None
        assert lm.model.startswith("anthropic/")


@pytest.mark.asyncio
async def test_anthropic_default_temperature():
    """Test that Anthropic adapter uses temperature parameter correctly."""
    from hemdov.infrastructure.adapters.litellm_dspy_adapter import create_anthropic_adapter

    with patch.dict(os.environ, {"HEMDOV_ANTHROPIC_API_KEY": "test-key"}):
        # Temperature should default to 0.3 from LiteLLMDSPyAdapter
        lm = create_anthropic_adapter(
            model="claude-haiku-4-5-20251001",
        )

        # Check that temperature is set (stored in default_params, not kwargs)
        assert lm.temperature == 0.3
        assert lm.default_params["temperature"] == 0.3

        # Test explicit temperature override
        lm2 = create_anthropic_adapter(
            model="claude-haiku-4-5-20251001",
            temperature=0.0,
        )
        assert lm2.temperature == 0.0
        assert lm2.default_params["temperature"] == 0.0
