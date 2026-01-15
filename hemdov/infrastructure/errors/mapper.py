"""Exception mapper for converting low-level exceptions to domain errors.

This mapper preserves full error context including:
- Original exception type
- Stack trace (for debugging)
- All relevant parameters (provider, model, db_path, etc.)
- Structured logging context for Sentry

CLAUDE.md compliance:
- Uses specific exception types (never catches Exception)
- Logs errors with full context (type, message, traceback)
- asyncio.TimeoutError maps to 504 (Gateway Timeout)
"""

import asyncio
import traceback
from aiosqlite import Error as AiosqliteError, IntegrityError, OperationalError, DatabaseError
import logging

from hemdov.domain.errors import ErrorCategory, LLMProviderError, PersistenceError, CacheError
from hemdov.infrastructure.errors.ids import ErrorIds

logger = logging.getLogger(__name__)


class ExceptionMapper:
    """Converts low-level exceptions to domain errors with full context.

    This class provides static methods for mapping different categories of
    exceptions to their corresponding domain error types. All methods:
    - Catch specific exception types (never Exception)
    - Preserve full context including stack trace
    - Log with structured context for Sentry
    - Return frozen domain errors (immutable)
    """

    @staticmethod
    def map_database_error(
        e: Exception,
        operation: str,
        db_path: str,
        entity_type: str = "Unknown",
        query_context: str = ""
    ) -> PersistenceError:
        """Map aiosqlite errors to PersistenceError with specific types.

        Args:
            e: The exception to map
            operation: The database operation being performed
            db_path: Path to the database file
            entity_type: Type of entity being persisted (for domain error)
            query_context: Optional SQL query context for debugging

        Returns:
            PersistenceError with full context and appropriate Error ID
        """
        # Map specific aiosqlite errors to specific Error IDs
        if isinstance(e, OperationalError):
            error_id = ErrorIds.DB_OPERATIONAL_ERROR
            error_type = "OperationalError"
        elif isinstance(e, DatabaseError):
            error_id = ErrorIds.DB_CORRUPTION
            error_type = "DatabaseError"
        elif isinstance(e, PermissionError):
            error_id = ErrorIds.DB_PERMISSION_DENIED
            error_type = "PermissionError"
        else:
            # Unknown database error
            error_id = ErrorIds.DB_QUERY_FAILED
            error_type = type(e).__name__

        # Build context dict with all debugging information
        context = {
            "operation": operation,
            "db_path": str(db_path),  # Infrastructure detail in context
            "original_exception": error_type,
            "query_context": query_context[:200] if query_context else "",
            "traceback": traceback.format_exc(limit=10)  # Stack trace for debugging
        }

        # Log with structured context for Sentry
        logger.error(
            f"Database error in {operation}: {error_type}: {e}. "
            f"Error ID: {error_id}",
            extra=context
        )

        return PersistenceError(
            category=ErrorCategory.DATABASE,
            message=f"Database {operation} failed: {e}",
            error_id=error_id,
            context=context,
            entity_type=entity_type,  # Domain concept
            operation=operation  # Domain concept
        )

    @staticmethod
    def map_llm_error(
        e: Exception,
        provider: str,
        model: str,
        prompt_length: int = 0
    ) -> LLMProviderError:
        """Map LLM provider errors to LLMProviderError.

        CLAUDE.md compliance: asyncio.TimeoutError maps to HTTP 504.

        Args:
            e: The exception to map
            provider: LLM provider name ("anthropic", "openai", "ollama")
            model: Model identifier ("claude-haiku-4-5", "gpt-4")
            prompt_length: Length of prompt being sent

        Returns:
            LLMProviderError with full context and appropriate Error ID
        """
        # Check asyncio.TimeoutError FIRST (maps to HTTP 504)
        if isinstance(e, asyncio.TimeoutError):
            error_id = ErrorIds.LLM_TIMEOUT
            error_type = "asyncio.TimeoutError"
        elif isinstance(e, ConnectionError):
            error_id = ErrorIds.LLM_CONNECTION_FAILED
            error_type = "ConnectionError"
        elif isinstance(e, TimeoutError):  # builtin TimeoutError (non-async)
            error_id = ErrorIds.LLM_TIMEOUT
            error_type = "TimeoutError"
        else:
            # Unknown LLM error
            error_id = ErrorIds.LLM_UNKNOWN_ERROR
            error_type = type(e).__name__

        # Build context dict
        context = {
            "provider": provider,
            "model": model,
            "prompt_length": str(prompt_length),
            "original_exception": error_type,
            "traceback": traceback.format_exc(limit=10)
        }

        # Log with structured context
        logger.error(
            f"LLM error for {provider}/{model}: {error_type}: {e}. "
            f"Error ID: {error_id}",
            extra=context
        )

        return LLMProviderError(
            category=ErrorCategory.LLM_PROVIDER,
            message=f"LLM request failed: {e}",
            error_id=error_id,
            context=context,
            provider=provider,
            model=model,
            original_exception=error_type
        )

    @staticmethod
    def map_cache_error(
        e: Exception,
        operation: str,
        cache_key: str,
        prompt_id: str = ""
    ) -> CacheError:
        """Map cache operation errors to CacheError.

        Args:
            e: The exception to map
            operation: Cache operation ("get", "set", "update", "delete")
            cache_key: The cache key being accessed
            prompt_id: Optional prompt ID for context

        Returns:
            CacheError with full context and appropriate Error ID
        """
        # Map specific cache errors
        if isinstance(e, IntegrityError):
            error_id = ErrorIds.CACHE_CONSTRAINT_VIOLATION
            error_type = "IntegrityError"
        else:
            error_id = ErrorIds.CACHE_SET_FAILED
            error_type = type(e).__name__

        # Build context dict
        context = {
            "operation": operation,
            "cache_key": cache_key[:8],  # First 8 chars for logging
            "prompt_id": prompt_id,
            "original_exception": error_type,
            "traceback": traceback.format_exc(limit=10)
        }

        # Log with structured context
        logger.error(
            f"Cache {operation} failed for {cache_key[:8]}: {error_type}: {e}. "
            f"Error ID: {error_id}",
            extra=context
        )

        return CacheError(
            category=ErrorCategory.CACHE_OPERATION,
            message=f"Cache {operation} failed: {e}",
            error_id=error_id,
            context=context,
            cache_key=cache_key,
            operation=operation
        )
