"""
LiteLLM DSPy Adapter

Reusable adapter for multiple LLM providers (Ollama, Gemini, DeepSeek, etc.)
Based on HemDov patterns - 100% reusable across projects.
"""

import os
from typing import Optional

import dspy


class LiteLLMDSPyAdapter(dspy.LM):
    """
    DSPy adapter for LiteLLM - unified interface to multiple LLM providers.

    Supports:
    - Ollama (local models)
    - Gemini (Google)
    - DeepSeek (API)
    - OpenAI (API)
    - And any other LiteLLM-supported provider
    """

    def __init__(
        self,
        model: str,
        api_base: Optional[str] = None,
        api_key: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 2000,
        **kwargs,
    ):
        super().__init__(model, api_base=api_base, **kwargs)
        self.model = model
        self.api_base = api_base
        self.api_key = api_key or os.getenv("LITELLM_API_KEY")
        self.temperature = temperature
        self.max_tokens = max_tokens

        # Configure LiteLLM
        import litellm

        self.litellm = litellm

        # Set default parameters
        self.default_params = {
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        if api_base:
            self.default_params["api_base"] = api_base
        if api_key:
            self.default_params["api_key"] = api_key

    def basic_request(self, prompt: str, **kwargs) -> str:
        """Make a basic request to the LLM."""
        try:
            # Merge with default params
            params = {**self.default_params, **kwargs}

            # Call LiteLLM
            response = self.litellm.completion(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                **params,
            )

            return response.choices[0].message.content

        except Exception as e:
            raise dspy.LMError(f"LiteLLM request failed: {str(e)}")

    def __call__(self, prompt: str, **kwargs) -> str:
        """Main entry point for DSPy."""
        return self.basic_request(prompt, **kwargs)


# Factory functions for common providers
def create_ollama_adapter(
    model: str = "hf.co/mradermacher/Novaeus-Promptist-7B-Instruct-i1-GGUF:Q5_K_M",
    base_url: str = "http://localhost:11434",
    **kwargs,
) -> LiteLLMDSPyAdapter:
    """Create Ollama adapter for local models."""
    return LiteLLMDSPyAdapter(model=f"ollama/{model}", api_base=base_url, **kwargs)


def create_gemini_adapter(
    model: str = "gemini-pro", api_key: Optional[str] = None, **kwargs
) -> LiteLLMDSPyAdapter:
    """Create Gemini adapter."""
    return LiteLLMDSPyAdapter(
        model=f"gemini/{model}",
        api_key=api_key or os.getenv("GEMINI_API_KEY"),
        **kwargs,
    )


def create_deepseek_adapter(
    model: str = "deepseek-chat", api_key: Optional[str] = None, **kwargs
) -> LiteLLMDSPyAdapter:
    """Create DeepSeek adapter."""
    return LiteLLMDSPyAdapter(
        model=f"deepseek/{model}",
        api_key=api_key or os.getenv("DEEPSEEK_API_KEY"),
        **kwargs,
    )


def create_openai_adapter(
    model: str = "gpt-4o", api_key: Optional[str] = None, **kwargs
) -> LiteLLMDSPyAdapter:
    """Create OpenAI adapter."""
    return LiteLLMDSPyAdapter(
        model=f"openai/{model}",
        api_key=api_key or os.getenv("OPENAI_API_KEY"),
        **kwargs,
    )
