"""Test domain error types."""

import pytest
from hemdov.domain.errors import (
    ErrorCategory,
    DomainError,
    LLMProviderError,
    CacheError,
    PersistenceError,
)


class TestDomainError:
    def test_domain_error_serializes_to_dict(self):
        """DomainError must serialize to dict for API responses."""
        error = DomainError(
            category=ErrorCategory.VALIDATION,
            message="Invalid input",
            error_id="VAL-001",
            context={"field": "email", "value": "invalid"}
        )

        result = error.to_dict()

        assert result["category"] == "validation"
        assert result["message"] == "Invalid input"
        assert result["error_id"] == "VAL-001"
        assert result["field"] == "email"
        assert result["value"] == "invalid"

    def test_domain_error_is_frozen(self):
        """Domain errors must be frozen (immutable)."""
        error = DomainError(
            category=ErrorCategory.VALIDATION,
            message="test",
            error_id="TEST-001",
            context={}
        )

        with pytest.raises(Exception):  # FrozenInstanceError
            error.message = "modified"


class TestLLMProviderError:
    def test_llm_error_contains_provider_info(self):
        """LLMProviderError must include provider and model."""
        error = LLMProviderError(
            category=ErrorCategory.LLM_PROVIDER,
            message="LLM failed",
            error_id="LLM-001",
            context={},
            provider="anthropic",
            model="claude-haiku-4-5",
            original_exception="ConnectionError"
        )

        assert error.provider == "anthropic"
        assert error.model == "claude-haiku-4-5"
        assert error.original_exception == "ConnectionError"


class TestCacheError:
    def test_cache_error_contains_operation_info(self):
        """CacheError must include cache_key and operation."""
        error = CacheError(
            category=ErrorCategory.CACHE_OPERATION,
            message="Cache failed",
            error_id="CACHE-001",
            context={},
            cache_key="abc123def456",
            operation="set"
        )

        assert error.cache_key == "abc123def456"
        assert error.operation == "set"


class TestPersistenceError:
    def test_persistence_error_is_infrastructure_agnostic(self):
        """PersistenceError should NOT have db_path field (goes in context)."""
        error = PersistenceError(
            category=ErrorCategory.DATABASE,
            message="Database failed",
            error_id="DB-001",
            context={"db_path": "/data/metrics.db"},  # Infrastructure detail in context
            entity_type="PromptHistory",
            operation="save"
        )

        # Domain concepts are fields
        assert error.entity_type == "PromptHistory"
        assert error.operation == "save"

        # Infrastructure details are in context
        assert error.context["db_path"] == "/data/metrics.db"

        # No db_path field on the error itself
        assert not hasattr(error, "db_path")
