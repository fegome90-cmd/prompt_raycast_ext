"""Test ExceptionMapper for error context preservation."""

import asyncio
import pytest
from aiosqlite import Error as AiosqliteError, IntegrityError, OperationalError
from hemdov.infrastructure.errors.mapper import ExceptionMapper
from hemdov.infrastructure.errors.ids import ErrorIds
from hemdov.domain.errors import ErrorCategory, LLMProviderError, PersistenceError, CacheError


class TestExceptionMapperLLM:
    def test_map_connection_error_includes_full_context(self):
        """ConnectionError maps to LLM_CONNECTION_FAILED with full context."""
        error = ConnectionError("Network unreachable")
        result = ExceptionMapper.map_llm_error(
            error,
            provider="anthropic",
            model="claude-haiku-4-5",
            prompt_length=1000
        )

        assert isinstance(result, LLMProviderError)
        assert result.category == ErrorCategory.LLM_PROVIDER
        assert result.error_id == ErrorIds.LLM_CONNECTION_FAILED
        assert result.provider == "anthropic"
        assert result.model == "claude-haiku-4-5"
        assert result.original_exception == "ConnectionError"
        assert result.context["provider"] == "anthropic"
        assert result.context["model"] == "claude-haiku-4-5"
        assert result.context["prompt_length"] == "1000"
        assert "traceback" in result.context

    def test_map_asyncio_timeout_error_maps_correctly(self):
        """asyncio.TimeoutError maps to LLM_TIMEOUT (CLAUDE.md compliance for 504)."""
        error = asyncio.TimeoutError("Async operation timed out")
        result = ExceptionMapper.map_llm_error(
            error,
            provider="openai",
            model="gpt-4"
        )

        assert result.error_id == ErrorIds.LLM_TIMEOUT
        # Spec requires: asyncio.TimeoutError sets error_type = "asyncio.TimeoutError"
        assert result.original_exception == "asyncio.TimeoutError"
        assert result.context["original_exception"] == "asyncio.TimeoutError"

    def test_map_builtin_timeout_error_maps_correctly(self):
        """builtin TimeoutError (non-async) also maps to LLM_TIMEOUT.

        Note: In Python 3.11+, asyncio.TimeoutError IS TimeoutError (same class),
        so TimeoutError() instances match the first isinstance check and are
        labeled as "asyncio.TimeoutError". This is correct behavior per the spec.
        """
        error = TimeoutError("Operation timed out")
        result = ExceptionMapper.map_llm_error(
            error,
            provider="ollama",
            model="llama2"
        )

        assert result.error_id == ErrorIds.LLM_TIMEOUT
        # In Python 3.11+, TimeoutError IS asyncio.TimeoutError, so it gets
        # the async label (matches first isinstance check per spec)
        assert result.original_exception == "asyncio.TimeoutError"

    def test_map_unknown_error_maps_to_unknown_error_id(self):
        """Unexpected exceptions map to LLM_UNKNOWN_ERROR."""
        error = RuntimeError("Unexpected error")
        result = ExceptionMapper.map_llm_error(
            error,
            provider="test",
            model="test-model"
        )

        assert result.error_id == ErrorIds.LLM_UNKNOWN_ERROR
        assert result.original_exception == "RuntimeError"


class TestExceptionMapperDatabase:
    def test_map_permission_error_includes_db_path(self):
        """PermissionError maps to DB_PERMISSION_DENIED with db_path in context."""
        error = PermissionError("Access denied to /data/metrics.db")
        result = ExceptionMapper.map_database_error(
            error,
            operation="initialize",
            db_path="/data/metrics.db",
            entity_type="Metrics"
        )

        assert isinstance(result, PersistenceError)
        assert result.error_id == ErrorIds.DB_PERMISSION_DENIED
        assert result.entity_type == "Metrics"
        assert result.operation == "initialize"
        assert result.context["db_path"] == "/data/metrics.db"
        assert result.context["original_exception"] == "PermissionError"
        assert "traceback" in result.context

    def test_map_operational_error_maps_correctly(self):
        """aiosqlite.OperationalError maps to DB_OPERATIONAL_ERROR."""
        error = OperationalError("Database is locked")
        result = ExceptionMapper.map_database_error(
            error,
            operation="query",
            db_path="/data/prompts.db",
            entity_type="PromptHistory"
        )

        assert result.error_id == ErrorIds.DB_OPERATIONAL_ERROR
        assert result.context["original_exception"] == "OperationalError"

    def test_map_database_error_maps_to_corruption(self):
        """aiosqlite.DatabaseError maps to DB_CORRUPTION."""
        from aiosqlite import DatabaseError
        error = DatabaseError("Database disk image is malformed")
        result = ExceptionMapper.map_database_error(
            error,
            operation="open",
            db_path="/data/cache.db",
            entity_type="CacheEntry"
        )

        assert result.error_id == ErrorIds.DB_CORRUPTION


class TestExceptionMapperCache:
    def test_map_integrity_error_maps_to_constraint_violation(self):
        """aiosqlite.IntegrityError maps to CACHE_CONSTRAINT_VIOLATION."""
        error = IntegrityError("UNIQUE constraint failed")
        result = ExceptionMapper.map_cache_error(
            error,
            operation="set",
            cache_key="abc123def456",
            prompt_id="prompt_1"
        )

        assert isinstance(result, CacheError)
        assert result.error_id == ErrorIds.CACHE_CONSTRAINT_VIOLATION
        assert result.cache_key == "abc123def456"
        assert result.operation == "set"
        assert result.context["cache_key"] == "abc123de"  # Truncated to 8 chars
        assert "traceback" in result.context
