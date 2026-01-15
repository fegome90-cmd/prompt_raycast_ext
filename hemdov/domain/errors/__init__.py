"""Domain error types - pure, no IO, no infrastructure dependencies.

These errors are frozen dataclasses that represent business-level failures.
They contain no logging, no async operations, no external dependencies.
"""

from dataclasses import dataclass
from enum import Enum


class ErrorCategory(Enum):
    """Categories of errors for HTTP status mapping.

    See CLAUDE.md for HTTP status code mapping:
    - LLM_PROVIDER → 503 (ServiceUnavailable)
    - CACHE_OPERATION → degrade gracefully
    - DATA_CORRUPTION → 500 (InternalError)
    - DATABASE → 503/500 (depends on error type)
    - FILE_IO → 400/503 (depends on error type)
    - VALIDATION → 400 (BadRequest)
    """
    LLM_PROVIDER = "llm_provider"
    CACHE_OPERATION = "cache_operation"
    DATA_CORRUPTION = "data_corruption"
    DATABASE = "database"
    FILE_IO = "file_io"
    VALIDATION = "validation"


@dataclass(frozen=True)
class DomainError:
    """Base domain error - pure, no IO, no infrastructure deps.

    This is the foundation of our error handling framework. All domain
    errors inherit from this and must be frozen (immutable) to ensure
    error information cannot be modified after creation.

    Attributes:
        category: The type of error (maps to HTTP status codes)
        message: Human-readable error description
        error_id: Unique ID for Sentry tracking (from ErrorIds class)
        context: Structured logging context (key-value pairs for debugging)
    """
    category: ErrorCategory
    message: str
    error_id: str
    context: dict[str, str]

    def to_dict(self) -> dict:
        """Serialize error to dict for API responses.

        Returns a flat dict with all context fields at the top level,
        making it easy to include in JSON responses.
        """
        return {
            "category": self.category.value,
            "message": self.message,
            "error_id": self.error_id,
            **self.context
        }


@dataclass(frozen=True)
class LLMProviderError(DomainError):
    """Error from LLM provider (OpenAI, Anthropic, Ollama, etc.)."""
    provider: str  # "anthropic", "openai", "ollama"
    model: str  # "claude-haiku-4-5", "gpt-4"
    original_exception: str  # Exception type name (not the exception itself)


@dataclass(frozen=True)
class CacheError(DomainError):
    """Error in cache operations (get, set, update, delete)."""
    cache_key: str  # The cache key being accessed
    operation: str  # "get", "set", "update", "delete"


@dataclass(frozen=True)
class PersistenceError(DomainError):
    """Error in persistence operations - infrastructure-agnostic.

    IMPORTANT: This error does NOT contain infrastructure details like
    db_path as fields. Those go in the context dict. This ensures the
    domain layer stays pure and doesn't depend on infrastructure.

    Attributes:
        entity_type: The type of entity being persisted ("PromptHistory", "Metrics")
        operation: The persistence operation ("save", "find", "delete", "initialize")
    """
    entity_type: str  # "PromptHistory", "Metrics", "CacheEntry"
    operation: str  # "save", "find", "delete", "initialize"
    # db_path, connection details, etc. go in context dict
