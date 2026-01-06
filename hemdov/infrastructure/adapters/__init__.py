"""
LLM Adapters for DSPy.

Contains adapters for various LLM providers (Ollama, Gemini, etc.).
"""

from hemdov.infrastructure.adapters.litellm_dspy_adapter import (
    LiteLLMDSPyAdapter,
    create_ollama_adapter,
    create_gemini_adapter,
    create_deepseek_adapter,
)

__all__ = [
    "LiteLLMDSPyAdapter",
    "create_ollama_adapter",
    "create_gemini_adapter",
    "create_deepseek_adapter",
]
