"""
LiteLLM DSPy Adapter (PromptImprover)

Parallel adapter to avoid impacting the HemDov production adapter.
Compatible with DSPy v3 call signatures.
"""

from typing import Any, Optional
import os

import dspy
import litellm


class PromptImproverLiteLLMAdapter(dspy.LM):
    """LiteLLM adapter compatible with DSPy v3 prompt/messages calls."""

    def __init__(
        self,
        model: str,
        api_base: Optional[str] = None,
        api_key: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 2000,
        **kwargs,
    ) -> None:
        super().__init__(model, api_base=api_base, **kwargs)
        self.model = model
        self.api_base = api_base
        self.api_key = api_key or os.getenv("LITELLM_API_KEY")
        self.litellm = litellm
        self.kwargs = {
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if api_base:
            self.kwargs["api_base"] = api_base
        if api_key:
            self.kwargs["api_key"] = api_key

    def __call__(
        self,
        prompt: Optional[str] = None,
        messages: Optional[list[dict[str, Any]]] = None,
        **kwargs,
    ) -> list[str]:
        if messages is None:
            if prompt is None:
                raise ValueError("LiteLLM adapter requires prompt or messages")
            messages = [{"role": "user", "content": prompt}]

        params = {**self.kwargs, **kwargs}
        requested_n = int(params.pop("n", 1))

        try:
            response = self.litellm.completion(
                model=self.model,
                messages=messages,
                **params,
            )
        except Exception as exc:
            raise RuntimeError(f"LiteLLM request failed: {str(exc)}") from exc

        outputs: list[str] = []
        for choice in response.choices:
            if hasattr(choice, "message"):
                outputs.append(choice.message.content)
            else:
                outputs.append(choice["text"])

        if not outputs:
            outputs = [""]

        if requested_n > len(outputs):
            outputs.extend([outputs[0]] * (requested_n - len(outputs)))

        return outputs


def create_ollama_adapter(
    model: str = "llama3.1", base_url: str = "http://localhost:11434", **kwargs
) -> PromptImproverLiteLLMAdapter:
    """Create Ollama adapter for local models."""
    return PromptImproverLiteLLMAdapter(
        model=f"ollama/{model}",
        api_base=base_url,
        **kwargs,
    )


def create_gemini_adapter(
    model: str = "gemini-pro", api_key: Optional[str] = None, **kwargs
) -> PromptImproverLiteLLMAdapter:
    """Create Gemini adapter."""
    return PromptImproverLiteLLMAdapter(
        model=f"gemini/{model}",
        api_key=api_key or os.getenv("GEMINI_API_KEY"),
        **kwargs,
    )


def create_deepseek_adapter(
    model: str = "deepseek-chat", api_key: Optional[str] = None, **kwargs
) -> PromptImproverLiteLLMAdapter:
    """Create DeepSeek adapter."""
    return PromptImproverLiteLLMAdapter(
        model=f"deepseek/{model}",
        api_key=api_key or os.getenv("DEEPSEEK_API_KEY"),
        **kwargs,
    )


def create_openai_adapter(
    model: str = "gpt-4o", api_key: Optional[str] = None, **kwargs
) -> PromptImproverLiteLLMAdapter:
    """Create OpenAI adapter."""
    return PromptImproverLiteLLMAdapter(
        model=f"openai/{model}",
        api_key=api_key or os.getenv("OPENAI_API_KEY"),
        **kwargs,
    )
