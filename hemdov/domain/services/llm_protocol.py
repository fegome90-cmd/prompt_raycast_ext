"""
LLM Client Protocol - Type-safe interface for LLM providers.

Defines the expected interface for LLM clients used across domain services.
"""
from typing import Any, Protocol


class LLMClient(Protocol):
    """
    Protocol for LLM client interface.

    Any LLM provider (OpenAI, DeepSeek, Ollama, etc.) must implement
    this interface to be compatible with domain services.
    """

    def generate(self, prompt: str, **kwargs: Any) -> str:
        """
        Generate response from prompt.

        Args:
            prompt: The input prompt to send to the LLM
            **kwargs: Additional provider-specific parameters (temp, max_tokens, etc.)

        Returns:
            Generated response text
        """
        ...
