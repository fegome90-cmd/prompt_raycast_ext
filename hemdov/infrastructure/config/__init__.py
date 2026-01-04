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
    LLM_PROVIDER: str = "ollama"  # ollama, gemini, deepseek, openai, anthropic
    LLM_MODEL: str = "hf.co/mradermacher/Novaeus-Promptist-7B-Instruct-i1-GGUF:Q5_K_M"
    LLM_BASE_URL: Optional[str] = "http://localhost:11434"
    LLM_API_KEY: Optional[str] = None
    GEMINI_API_KEY: Optional[str] = None
    DEEPSEEK_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    HEMDOV_ANTHROPIC_API_KEY: Optional[str] = None

    # DSPy Settings
    DSPY_MAX_BOOTSTRAPPED_DEMOS: int = 5
    DSPY_MAX_LABELED_DEMOS: int = 3
    DSPY_COMPILED_PATH: Optional[str] = None

    # Few-Shot Settings
    DSPY_FEWSHOT_ENABLED: bool = False
    DSPY_FEWSHOT_TRAINSET_PATH: Optional[str] = None
    DSPY_FEWSHOT_K: int = 3
    DSPY_FEWSHOT_COMPILED_PATH: Optional[str] = "models/prompt_improver_fewshot.json"

    # API Settings
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_RELOAD: bool = True

    # Quality Settings
    MIN_CONFIDENCE_THRESHOLD: float = 0.7
    MAX_LATENCY_MS: int = 30000

    # SQLite Persistence Settings
    SQLITE_ENABLED: bool = True
    SQLITE_DB_PATH: str = "data/prompt_history.db"
    SQLITE_POOL_SIZE: int = 1
    SQLITE_RETENTION_DAYS: int = 30
    SQLITE_AUTO_CLEANUP: bool = True
    SQLITE_WAL_MODE: bool = True

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )


# Global settings instance
settings = Settings()
