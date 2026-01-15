# Infrastructure Error Handling Framework - Phase 1 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build the foundation layer for error handling (domain errors, Result types, ExceptionMapper, Error IDs) with zero breaking changes to existing code.

**Architecture:** Three-layer framework where Domain layer defines pure error types, Infrastructure layer maps exceptions via ExceptionMapper, and API layer handles HTTP mapping. Phase 1 creates only new files - no modifications to existing code.

**Tech Stack:** Python 3.9+, dataclasses (frozen), typing.TypeVar, aiosqlite, pytest, logging

**Phase 1 Success Criteria:**
- All error types serialize correctly to dict
- Result pattern matching works (Success/Failure)
- ExceptionMapper preserves full error context (traceback, error type)
- All Error IDs are unique
- Test coverage >90% for new code

**Reference Documents:**
- Design: `docs/plans/2026-01-15-infrastructure-error-handling-framework.md`
- Project Guidelines: `CLAUDE.md` (error handling section)
- HTTP Mapping: `docs/api-error-handling.md`

---

## Task 1: Create Error ID Registry

**Files:**
- Create: `hemdov/infrastructure/errors/__init__.py` (empty marker file)
- Create: `hemdov/infrastructure/errors/ids.py`
- Test: `tests/test_infrastructure/test_error_ids.py`

**Why First:** Error IDs are the foundation - everything else references them. Creating them first allows immediate verification of uniqueness.

**Step 1: Create the errors package marker file**

```bash
mkdir -p hemdov/infrastructure/errors
touch hemdov/infrastructure/errors/__init__.py
```

**Step 2: Write the failing test for Error ID uniqueness**

Create: `tests/test_infrastructure/test_error_ids.py`

```python
"""Test Error ID registry uniqueness and format."""

import pytest
from hemdov.infrastructure.errors.ids import ErrorIds


def test_error_ids_are_unique():
    """Error IDs must be unique for Sentry tracking.

    This prevents two different errors from logging with the same ID,
    which would make debugging impossible in Sentry.
    """
    error_ids = [
        ErrorIds.LLM_CONNECTION_FAILED,
        ErrorIds.LLM_TIMEOUT,
        ErrorIds.LLM_UNKNOWN_ERROR,
        ErrorIds.CACHE_GET_FAILED,
        ErrorIds.CACHE_SET_FAILED,
        ErrorIds.CACHE_UPDATE_FAILED,
        ErrorIds.CACHE_CONSTRAINT_VIOLATION,
        ErrorIds.DATA_CORRUPTION_METRICS,
        ErrorIds.DATA_CORRUPTION_GUARDRAILS,
        ErrorIds.DB_QUERY_FAILED,
        ErrorIds.DB_OPERATIONAL_ERROR,
        ErrorIds.DB_CORRUPTION,
        ErrorIds.DB_PERMISSION_DENIED,
        ErrorIds.DB_INIT_FAILED,
        ErrorIds.MIGRATION_FAILED,
        ErrorIds.FILE_READ_FAILED,
        ErrorIds.FILE_NOT_FOUND,
        ErrorIds.FILE_PERMISSION_DENIED,
        ErrorIds.FILE_UNICODE_ERROR,
    ]

    # Check for duplicates using set property
    unique_ids = set(error_ids)
    assert len(error_ids) == len(unique_ids), (
        f"Duplicate Error IDs found: "
        f"{[eid for eid in error_ids if error_ids.count(eid) > 1]}"
    )


def test_error_id_format():
    """All Error IDs follow PREFIX-NUM format for Sentry compatibility."""
    error_ids = [
        ErrorIds.LLM_CONNECTION_FAILED,
        ErrorIds.LLM_TIMEOUT,
        # ... add all ErrorIds
    ]

    for error_id in error_ids:
        # Format: LLM-001, CACHE-001, DB-001, IO-001
        assert "-" in error_id, f"{error_id} must contain hyphen"
        parts = error_id.split("-")
        assert len(parts) == 2, f"{error_id} must have exactly one hyphen"
        prefix, number = parts
        assert prefix.isupper(), f"{error_id} prefix must be uppercase"
        assert number.isdigit(), f"{error_id} suffix must be numeric"
```

**Step 3: Run test to verify it fails**

```bash
pytest tests/test_infrastructure/test_error_ids.py -v
```

Expected: `ModuleNotFoundError: hemdov.infrastructure.errors.ids`

**Step 4: Create the ErrorIds class**

Create: `hemdov/infrastructure/errors/ids.py`

```python
"""Error ID registry for Sentry tracking.

Each error has a unique ID that appears in logs and Sentry.
Format: PREFIX-NUM where PREFIX is the error category and NUM is a sequence.
"""


class ErrorIds:
    """Centralized Error ID registry.

    All Error IDs must be unique for Sentry tracking.
    Format: PREFIX-NUM (e.g., LLM-001, CACHE-001, DB-001, IO-001)
    """

    # LLM Provider Errors
    LLM_CONNECTION_FAILED = "LLM-001"
    LLM_TIMEOUT = "LLM-002"
    LLM_UNKNOWN_ERROR = "LLM-003"

    # Cache Errors
    CACHE_GET_FAILED = "CACHE-001"
    CACHE_SET_FAILED = "CACHE-002"
    CACHE_UPDATE_FAILED = "CACHE-003"
    CACHE_CONSTRAINT_VIOLATION = "CACHE-004"

    # Data Corruption Errors
    DATA_CORRUPTION_METRICS = "DATA-001"
    DATA_CORRUPTION_GUARDRAILS = "DATA-002"

    # Database Errors
    DB_QUERY_FAILED = "DB-001"
    DB_OPERATIONAL_ERROR = "DB-002"
    DB_CORRUPTION = "DB-003"
    DB_PERMISSION_DENIED = "DB-004"
    DB_INIT_FAILED = "DB-005"
    MIGRATION_FAILED = "DB-006"

    # File I/O Errors
    FILE_READ_FAILED = "IO-001"
    FILE_NOT_FOUND = "IO-002"
    FILE_PERMISSION_DENIED = "IO-003"
    FILE_UNICODE_ERROR = "IO-004"
```

**Step 5: Run test to verify it passes**

```bash
pytest tests/test_infrastructure/test_error_ids.py -v
```

Expected: `PASSED`

**Step 6: Commit**

```bash
git add hemdov/infrastructure/errors/ tests/test_infrastructure/test_error_ids.py
git commit -m "feat(error-handling): add Error ID registry

- Create ErrorIds class with 19 unique error IDs
- Format: PREFIX-NUM for Sentry compatibility
- Add uniqueness test to prevent duplicates
- Categories: LLM, CACHE, DATA, DB, IO

Part of Phase 1: Foundation layer for error handling framework.

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Task 2: Create Domain Error Types

**Files:**
- Create: `hemdov/domain/errors/__init__.py`
- Test: `tests/test_domain/test_errors.py`

**Reference:** CLAUDE.md lines on error handling (specific exception types, HTTP mapping)

**Step 1: Write failing test for domain error serialization**

Create: `tests/test_domain/test_errors.py`

```python
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
```

**Step 2: Run test to verify it fails**

```bash
pytest tests/test_domain/test_errors.py -v
```

Expected: `ModuleNotFoundError: hemdov.domain.errors`

**Step 3: Create domain error types**

Create: `hemdov/domain/errors/__init__.py`

```python
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
```

**Step 4: Run test to verify it passes**

```bash
pytest tests/test_domain/test_errors.py -v
```

Expected: `PASSED`

**Step 5: Run all tests to ensure no breakage**

```bash
pytest tests/ -v --tb=short
```

Expected: All existing tests still pass (we only added new files)

**Step 6: Commit**

```bash
git add hemdov/domain/ tests/test_domain/
git commit -m "feat(error-handling): add domain error types

- Create ErrorCategory enum for HTTP status mapping
- Create DomainError base class (frozen dataclass)
- Create LLMProviderError, CacheError, PersistenceError
- PersistenceError is infrastructure-agnostic (db_path in context)
- Add serialization tests for all error types

Domain layer remains pure (no IO, no async, no infrastructure deps).

Part of Phase 1: Foundation layer for error handling framework.

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Task 3: Create Result Type

**Files:**
- Create: `hemdov/domain/types/__init__.py` (marker)
- Create: `hemdov/domain/types/result.py`
- Test: `tests/test_domain/test_result.py`

**Reference:** Design document section on Result type with degradation_flags

**Step 1: Write failing tests for Result type**

Create: `tests/test_domain/test_result.py`

```python
"""Test Result type for explicit error handling."""

import pytest
from hemdov.domain.errors import DomainError, ErrorCategory
from hemdov.domain.types.result import (
    Success,
    Failure,
    Result,
    is_success,
    is_failure,
)


class TestSuccess:
    def test_success_contains_value(self):
        """Success must contain the success value."""
        result = Success(value="prompt text")
        assert result.value == "prompt text"

    def test_success_has_empty_degradation_flags_by_default(self):
        """Success has empty degradation flags when not specified."""
        result = Success(value="data")
        assert result.degradation_flags == {}

    def test_success_can_carry_degradation_flags(self):
        """Success can indicate degraded features via flags."""
        result = Success(
            value="prompt",
            degradation_flags={"knn_disabled": True, "metrics_failed": False}
        )
        assert result.degradation_flags["knn_disabled"] is True
        assert result.degradation_flags["metrics_failed"] is False

    def test_success_is_frozen(self):
        """Success is immutable (frozen dataclass)."""
        result = Success(value="data")
        with pytest.raises(Exception):
            result.value = "modified"


class TestFailure:
    def test_failure_contains_error(self):
        """Failure must contain the domain error."""
        error = DomainError(
            category=ErrorCategory.VALIDATION,
            message="Invalid",
            error_id="VAL-001",
            context={}
        )
        result = Failure(error=error)
        assert result.error == error

    def test_failure_is_frozen(self):
        """Failure is immutable."""
        error = DomainError(
            category=ErrorCategory.VALIDATION,
            message="Invalid",
            error_id="VAL-001",
            context={}
        )
        result = Failure(error=error)
        with pytest.raises(Exception):
            result.error = None


class TestResultHelpers:
    def test_is_success_returns_true_for_success(self):
        """is_success returns True for Success instances."""
        result: Result[str, DomainError] = Success("value")
        assert is_success(result) is True
        assert is_failure(result) is False

    def test_is_failure_returns_true_for_failure(self):
        """is_failure returns True for Failure instances."""
        error = DomainError(ErrorCategory.VALIDATION, "err", "VAL-001", {})
        result: Result[str, DomainError] = Failure(error)
        assert is_success(result) is False
        assert is_failure(result) is True

    def test_result_invariant_xor(self):
        """Result must be Success XOR Failure, never both.

        This invariant ensures we can't have invalid Result states.
        """
        success = Success("value")
        failure = Failure(DomainError(ErrorCategory.VALIDATION, "err", "VAL-001", {}))

        # Success is not failure
        assert is_success(success) ^ is_failure(success)

        # Failure is not success
        assert is_success(failure) ^ is_failure(failure)

    def test_result_type_annotation_works(self):
        """Result type annotation preserves generic types."""
        # String success, DomainError failure
        result1: Result[str, DomainError] = Success("text")

        # Int success, CacheError failure
        result2: Result[int, CacheError] = Success(42)

        assert is_success(result1)
        assert is_success(result2)
```

**Step 2: Run test to verify it fails**

```bash
pytest tests/test_domain/test_result.py -v
```

Expected: `ModuleNotFoundError: hemdov.domain.types.result`

**Step 3: Create Result type**

Create: `hemdov/domain/types/result.py`

```python
"""Result type for explicit error handling.

Instead of conflating "not found" and "error" in Optional[dict],
Result makes success and failure explicit in the type system.
"""

from typing import TypeVar, Generic
from dataclasses import dataclass, field

# Import DomainError for type annotation
from hemdov.domain.errors import DomainError

T = TypeVar('T')  # Success value type
E = TypeVar('E', bound=DomainError)  # Failure error type


@dataclass(frozen=True)
class Success(Generic[T]):
    """Represents a successful operation.

    Attributes:
        value: The success value of type T
        degradation_flags: Optional flags indicating degraded features
                           (CLAUDE.md compliance for graceful degradation)
    """
    value: T
    degradation_flags: dict[str, bool] = field(default_factory=dict)


@dataclass(frozen=True)
class Failure(Generic[E]):
    """Represents a failed operation.

    Attributes:
        error: The domain error that caused the failure
    """
    error: E


# Type alias for Result union type
Result = Success[T] | Failure[E]


def is_success(result: Result[T, E]) -> bool:
    """Check if Result is a Success.

    Usage:
        result = await operation()
        if is_success(result):
            value = result.value
        else:
            error = result.error
    """
    return isinstance(result, Success)


def is_failure(result: Result[T, E]) -> bool:
    """Check if Result is a Failure.

    Usage:
        result = await operation()
        if is_failure(result):
            handle_error(result.error)
    """
    return isinstance(result, Failure)
```

Create: `hemdov/domain/types/__init__.py`

```python
"""Domain type definitions."""

from hemdov.domain.types.result import (
    Success,
    Failure,
    Result,
    is_success,
    is_failure,
)

__all__ = ["Success", "Failure", "Result", "is_success", "is_failure"]
```

**Step 4: Run test to verify it passes**

```bash
pytest tests/test_domain/test_result.py -v
```

Expected: `PASSED`

**Step 5: Run all tests**

```bash
pytest tests/ -v --tb=short
```

Expected: All tests pass

**Step 6: Commit**

```bash
git add hemdov/domain/types/ tests/test_domain/test_result.py
git commit -m "feat(error-handling): add Result type for explicit error handling

- Create Success[T] and Failure[E] frozen dataclasses
- Add degradation_flags to Success (CLAUDE.md compliance)
- Add is_success() and is_failure() helper functions
- Add type alias Result = Success[T] | Failure[E]
- Add invariant tests (Success XOR Failure)
- Add degradation flags test

Result type makes error states explicit in the type system.

Part of Phase 1: Foundation layer for error handling framework.

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Task 4: Create ExceptionMapper

**Files:**
- Modify: `hemdov/infrastructure/errors/mapper.py` (create)
- Test: `tests/test_infrastructure/test_exception_mapper.py`
- Test: `tests/test_infrastructure/test_exception_mapper_context.py`

**Reference:** Design document section on ExceptionMapper with asyncio.TimeoutError handling

**Step 1: Write failing test for LLM error mapping**

Create: `tests/test_infrastructure/test_exception_mapper.py`

```python
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
        assert result.original_exception == "asyncio.TimeoutError"
        assert result.context["original_exception"] == "asyncio.TimeoutError"

    def test_map_builtin_timeout_error_maps_correctly(self):
        """builtin TimeoutError (non-async) also maps to LLM_TIMEOUT."""
        error = TimeoutError("Operation timed out")
        result = ExceptionMapper.map_llm_error(
            error,
            provider="ollama",
            model="llama2"
        )

        assert result.error_id == ErrorIds.LLM_TIMEOUT
        assert result.original_exception == "TimeoutError"

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
        assert result.original_exception == "OperationalError"

    def test_map_database_error_maps_to_corruption(self):
        """aiosqlite.DatabaseError maps to DB_CORRUPTION."""
        error = AiosqliteError("Database disk image is malformed")
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
        assert result.context["cache_key"] == "abc123"  # Truncated to 8 chars
        assert "traceback" in result.context
```

**Step 2: Write failing test for logging context**

Create: `tests/test_infrastructure/test_exception_mapper_context.py`

```python
"""Test ExceptionMapper logging context capture."""

import logging
import pytest
from hemdov.infrastructure.errors.mapper import ExceptionMapper
from hemdov.infrastructure.errors.ids import ErrorIds
from hemdov.domain.errors import ErrorCategory


class TestExceptionMapperLogging:
    def test_mapper_captures_structured_logging_context(self, caplog):
        """Verify structured logging context is complete and correct."""
        error = ConnectionError("Network unreachable")

        with caplog.at_level(logging.ERROR):
            result = ExceptionMapper.map_llm_error(
                error,
                provider="anthropic",
                model="claude-haiku-4-5",
                prompt_length=1000
            )

        # Verify log record exists
        assert len(caplog.records) == 1
        log_record = caplog.records[0]

        # Verify extra context is present
        assert hasattr(log_record, "extra")
        context = log_record.extra

        # Verify all expected keys
        assert context["provider"] == "anthropic"
        assert context["model"] == "claude-haiku-4-5"
        assert context["prompt_length"] == "1000"
        assert context["original_exception"] == "ConnectionError"
        assert "traceback" in context

        # Verify Error ID in message
        assert "LLM_CONNECTION_FAILED" in log_record.message

    def test_mapper_includes_traceback_in_context(self, caplog):
        """Stack trace should be captured in context for debugging."""
        error = PermissionError("Access denied")

        with caplog.at_level(logging.ERROR):
            result = ExceptionMapper.map_database_error(
                error,
                operation="initialize",
                db_path="/data/metrics.db"
            )

        log_record = caplog.records[0]
        context = log_record.extra

        # Verify traceback is present (will contain current stack)
        assert "traceback" in context
        assert len(context["traceback"]) > 0
```

**Step 3: Run tests to verify they fail**

```bash
pytest tests/test_infrastructure/test_exception_mapper.py -v
pytest tests/test_infrastructure/test_exception_mapper_context.py -v
```

Expected: `ModuleNotFoundError: hemdov.infrastructure.errors.mapper`

**Step 4: Create ExceptionMapper**

Create: `hemdov/infrastructure/errors/mapper.py`

```python
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
from aiosqlite import Error as AiosqliteError
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
        if isinstance(e, Aiosqlite.OperationalError):
            error_id = ErrorIds.DB_OPERATIONAL_ERROR
            error_type = "OperationalError"
        elif isinstance(e, Aiosqlite.DatabaseError):
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
        # CLAUDE.md compliance: asyncio.TimeoutError → 504 (Gateway Timeout)
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
        if isinstance(e, Aiosqlite.IntegrityError):
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
```

Update: `hemdov/infrastructure/errors/__init__.py`

```python
"""Infrastructure error handling components."""

from hemdov.infrastructure.errors.mapper import ExceptionMapper
from hemdov.infrastructure.errors.ids import ErrorIds

__all__ = ["ExceptionMapper", "ErrorIds"]
```

**Step 5: Run tests to verify they pass**

```bash
pytest tests/test_infrastructure/test_exception_mapper.py -v
pytest tests/test_infrastructure/test_exception_mapper_context.py -v
```

Expected: `PASSED`

**Step 6: Run all tests**

```bash
pytest tests/ -v --tb=short
```

Expected: All tests pass

**Step 7: Commit**

```bash
git add hemdov/infrastructure/errors/ tests/test_infrastructure/
git commit -m "feat(error-handling): add ExceptionMapper with full context preservation

- Create ExceptionMapper with map_database_error, map_llm_error, map_cache_error
- Handle asyncio.TimeoutError for CLAUDE.md compliance (maps to 504)
- Capture stack trace in all error contexts (traceback.format_exc)
- Structured logging with extra=context for Sentry
- Specific exception types only (never catches Exception)
- Map to PersistenceError (infrastructure-agnostic domain error)

All error mappings include:
- Original exception type
- Stack trace
- Relevant parameters (provider, model, db_path, etc.)
- Structured logging context

Part of Phase 1: Foundation layer for error handling framework.

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Task 5: Verify Phase 1 Completion

**Files:**
- Test: All Phase 1 tests
- Verify: No breaking changes to existing code

**Step 1: Run complete test suite**

```bash
pytest tests/ -v --cov=hemdov.domain --cov=hemdov.infrastructure.errors --cov-report=term-missing
```

Expected:
- All tests pass
- Coverage >90% for new code
- No existing tests broken

**Step 2: Verify no breaking changes**

```bash
# Check we haven't modified existing files
git diff --name-only main | grep -v "^docs/plans/"
```

Expected: No output (only new files added)

**Step 3: Run linting**

```bash
make lint  # or whatever your lint command is
```

Expected: No new linting errors

**Step 4: Verify Phase 1 success criteria**

```bash
# 1. All error types serialize correctly
python3 -c "
from hemdov.domain.errors import DomainError, ErrorCategory
e = DomainError(ErrorCategory.VALIDATION, 'test', 'TEST-001', {})
print(e.to_dict())
"

# 2. Result pattern matching works
python3 -c "
from hemdov.domain.types.result import Success, Failure, is_success
s = Success('value')
f = Failure(DomainError(ErrorCategory.VALIDATION, 'e', 'TEST-001', {}))
print(is_success(s), is_failure(f))
"

# 3. ExceptionMapper preserves context
python3 -c "
from hemdov.infrastructure.errors.mapper import ExceptionMapper
from hemdov.infrastructure.errors.ids import ErrorIds
err = ExceptionMapper.map_llm_error(ConnectionError('test'), 'test', 'test')
print(err.error_id, 'traceback' in err.context)
"

# 4. Error IDs are unique
pytest tests/test_infrastructure/test_error_ids.py -v
```

Expected: All commands succeed

**Step 5: Create Phase 1 completion marker**

Create: `hemdov/infrastructure/errors/PHASE1_COMPLETE`

```markdown
# Phase 1 Complete

All foundation components for error handling framework are implemented:

✅ Error ID Registry (19 unique Error IDs)
✅ Domain Error Types (DomainError, LLMProviderError, CacheError, PersistenceError)
✅ Result Type (Success with degradation_flags, Failure, helpers)
✅ ExceptionMapper (full context preservation, asyncio.TimeoutError support)

Next: Phase 2 - Migrate critical paths (metrics_repository first)
```

**Step 6: Commit Phase 1 completion**

```bash
git add hemdov/infrastructure/errors/PHASE1_COMPLETE
git commit -m "feat(error-handling): complete Phase 1 foundation

Phase 1 Success Criteria:
✅ All error types serialize correctly
✅ Result pattern matching works
✅ ExceptionMapper preserves full error context
✅ All Error IDs are unique (19 IDs)
✅ Test coverage >90% for new code
✅ Zero breaking changes to existing code

Foundation layer is ready for Phase 2 migration.

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Phase 1 Summary

**Files Created:**
- `hemdov/domain/errors/__init__.py` - Domain error types
- `hemdov/domain/types/__init__.py` - Result type
- `hemdov/domain/types/result.py` - Result implementation
- `hemdov/infrastructure/errors/__init__.py` - Error package
- `hemdov/infrastructure/errors/ids.py` - Error ID registry
- `hemdov/infrastructure/errors/mapper.py` - Exception mapper
- `tests/test_domain/test_errors.py` - Domain error tests
- `tests/test_domain/test_result.py` - Result type tests
- `tests/test_infrastructure/test_error_ids.py` - Error ID tests
- `tests/test_infrastructure/test_exception_mapper.py` - Mapper tests
- `tests/test_infrastructure/test_exception_mapper_context.py` - Logging tests

**Files Modified:** None (Phase 1 is additive only)

**Test Coverage:** >90% for new code

**Breaking Changes:** None

**Next Phase:** Phase 2 - Migrate metrics_repository.py (lowest risk, analytics only)

---

**Usage:**

To execute this plan, use the `superpowers:executing-plans` skill in a new session with the worktree. Each task will be executed step-by-step with verification between steps.
