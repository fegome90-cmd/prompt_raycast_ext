"""
HemDov Infrastructure Settings

Configuration management for DSPy modules and adapters.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional
import os


class Settings(BaseSettings):
    """Global settings for HemDov DSPy integration."""

    # LLM Provider Settings
    LLM_PROVIDER: str = "ollama"  # ollama, gemini, deepseek, openai
    LLM_MODEL: str = "llama3.1"
    LLM_BASE_URL: Optional[str] = "http://localhost:11434"
    LLM_API_KEY: Optional[str] = None
    GEMINI_API_KEY: Optional[str] = None
    DEEPSEEK_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None

    # DSPy Settings
    DSPY_MAX_BOOTSTRAPPED_DEMOS: int = 5
    DSPY_MAX_LABELED_DEMOS: int = 3
    DSPY_COMPILED_PATH: Optional[str] = None

    # API Settings
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_RELOAD: bool = True

    # Quality Settings
    MIN_CONFIDENCE_THRESHOLD: float = 0.7
    MAX_LATENCY_MS: int = 30000

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )


# Global settings instance
settings = Settings()
