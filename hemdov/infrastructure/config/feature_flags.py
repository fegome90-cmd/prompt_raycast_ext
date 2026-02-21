#!/usr/bin/env python3
"""Feature flags for incremental rollout of NLaC pipeline features.

This module provides feature flags for controlling the rollout of NLaC Pipeline v3.0 features.
Flags can be set via environment variables or JSON configuration file.
"""
import json
import logging
from dataclasses import dataclass
from os import getenv
from pathlib import Path
from typing import Self

logger = logging.getLogger(__name__)


def _parse_bool(value: str | None) -> bool:
    """
    Parse environment variable as boolean.

    Args:
        value: String value to parse

    Returns:
        True if value is "true", "1", "yes", or "on" (case-insensitive)
        False otherwise (including None, empty string, or non-string values)
    """
    if not isinstance(value, str):
        return False
    return value.lower() in ("true", "1", "yes", "on")


@dataclass
class FeatureFlags:
    """Feature flags for incremental rollout of NLaC pipeline features.

    Attributes:
        enable_dspy_embeddings: Enable DSPy embeddings (Ollama/OpenAI)
        enable_cache: Enable SQLite cache layer
        enable_ifeval: Enable IFEval validation
        enable_metrics: Enable metrics collection
        enable_enhanced_rar: Enable enhanced RaR (DEFERRED - not critical)
        embedding_provider: Embedding provider ("ollama" or "openai")
    """

    # DSPy Integration
    enable_dspy_embeddings: bool = _parse_bool(getenv("ENABLE_DSPY_EMBEDDINGS", "false"))

    # Cache Layer
    enable_cache: bool = _parse_bool(getenv("ENABLE_CACHE", "true"))

    # IFEval Validation
    enable_ifeval: bool = _parse_bool(getenv("ENABLE_IFEVAL", "true"))

    # Metrics Collection
    enable_metrics: bool = _parse_bool(getenv("ENABLE_METRICS", "true"))

    # Enhanced RaR (DEFERRED - not critical)
    enable_enhanced_rar: bool = _parse_bool(getenv("ENABLE_ENHANCED_RAR", "false"))

    # Embedding Provider Selection
    embedding_provider: str = getenv("EMBEDDING_PROVIDER", "ollama")  # ollama | openai

    @classmethod
    def save(cls, path: Path = Path("config/feature_flags.json")) -> None:
        """
        Save current flags to file for debugging.

        Args:
            path: Path to save the feature flags JSON file

        Raises:
            OSError: If directory creation or file write fails
            TypeError: If JSON serialization fails due to invalid types
        """
        flags = cls()
        try:
            path.parent.mkdir(exist_ok=True)
            with open(path, "w") as f:
                json.dump({
                    "enable_dspy_embeddings": flags.enable_dspy_embeddings,
                    "enable_cache": flags.enable_cache,
                    "enable_ifeval": flags.enable_ifeval,
                    "enable_metrics": flags.enable_metrics,
                    "enable_enhanced_rar": flags.enable_enhanced_rar,
                    "embedding_provider": flags.embedding_provider,
                }, f, indent=2)
        except OSError as e:
            logger.error(
                "Failed to save feature flags",
                extra={
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "target_path": str(path),
                }
            )
            raise
        except (TypeError, ValueError) as e:
            logger.error(
                "Failed to serialize feature flags to JSON",
                extra={
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                }
            )
            raise

    @classmethod
    def load(cls, path: Path = Path("config/feature_flags.json")) -> Self:
        """
        Load flags from file if exists.

        Args:
            path: Path to load the feature flags JSON file from

        Returns:
            FeatureFlags instance with loaded values or defaults

        Raises:
            OSError: If file read fails
            json.JSONDecodeError: If file contains invalid JSON
            ValueError: If loaded data has invalid value types
        """
        if not path.exists():
            return cls()

        try:
            with open(path) as f:
                data = json.load(f)
        except OSError as e:
            logger.error(
                "Failed to read feature flags file",
                extra={
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "source_path": str(path),
                }
            )
            raise
        except json.JSONDecodeError as e:
            logger.error(
                "Failed to parse feature flags JSON",
                extra={
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "source_path": str(path),
                    "line": e.lineno,
                    "column": e.colno,
                }
            )
            raise

        # Validate data types before creating instance
        try:
            return cls(
                enable_dspy_embeddings=data.get("enable_dspy_embeddings", False),
                enable_cache=data.get("enable_cache", True),
                enable_ifeval=data.get("enable_ifeval", True),
                enable_metrics=data.get("enable_metrics", True),
                enable_enhanced_rar=data.get("enable_enhanced_rar", False),
                embedding_provider=data.get("embedding_provider", "ollama"),
            )
        except (TypeError, ValueError) as e:
            logger.error(
                "Failed to create FeatureFlags from loaded data",
                extra={
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "loaded_data": data,
                }
            )
            raise

    def __str__(self) -> str:
        """Return string representation of feature flags."""
        return f"""FeatureFlags:
  enable_dspy_embeddings: {self.enable_dspy_embeddings}
  enable_cache: {self.enable_cache}
  enable_ifeval: {self.enable_ifeval}
  enable_metrics: {self.enable_metrics}
  enable_enhanced_rar: {self.enable_enhanced_rar}
  embedding_provider: {self.embedding_provider}"""


if __name__ == "__main__":
    # Test feature flags
    flags = FeatureFlags()
    print(flags)

    # Save to file
    FeatureFlags.save()
    print("\nFeature flags saved to config/feature_flags.json")
