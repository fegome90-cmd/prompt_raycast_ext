# Infrastructure Error Handling Framework

> **Status:** Design Phase | **Created:** 2026-01-15 | **Priority:** High

## Executive Summary

This document describes a systematic refactoring of the infrastructure layer's error handling patterns. The current codebase has **7 critical issues** related to broad exception catching, silent failures, and inadequate error context.

**Goal:** Implement a contracts-first error handling framework that:
1. Eliminates broad exception catching (`except Exception`)
2. Makes error states explicit in the type system (Result types)
3. Provides full error context for debugging (Error IDs, structured logging)
4. Enables gradual migration via feature flags
5. Maintains API stability and hexagonal architecture principles

**Success Criteria:**
- ✅ Zero `except Exception` in infrastructure layer
- ✅ All errors have Error IDs for Sentry tracking
- ✅ Test coverage >80% for error handling paths
- ✅ No silent failures (returning `False` without context)

---

## Architecture

### Three-Layer Framework

```
┌─────────────────────────────────────────────────────────────┐
│                    API Layer                                 │
│  api/errors/ - Maps domain errors to HTTP status codes       │
│  400 (ValidationError) → 503 (ServiceUnavailable)           │
└─────────────────────────────────────────────────────────────┘
                              ▲
                              │
┌─────────────────────────────────────────────────────────────┐
│                Infrastructure Layer                          │
│  infrastructure/errors/ - ExceptionMapper                   │
│  Converts low-level exceptions → DomainError                │
│  Returns Result[T, Error] instead of raising                │
└─────────────────────────────────────────────────────────────┘
                              ▲
                              │
┌─────────────────────────────────────────────────────────────┐
│                    Domain Layer                              │
│  domain/errors/ - Pure error definitions (frozen dataclass) │
│  domain/types/result.py - Result[T, E] type                 │
└─────────────────────────────────────────────────────────────┘
```

### Key Innovation: Result Type

Instead of `Optional[dict]` that conflates "not found" and "error":
```python
# Old (ambiguous)
def cache_prompt(...) -> bool:  # True=success, False=??? (error? not found?)

# New (explicit)
def cache_prompt(...) -> Result[bool, CacheError]:
    # Success(bool) | Failure(CacheError)
    # Forces caller to handle both cases
```

---

## Core Components

### 1. Domain Error Types

**Location:** `hemdov/domain/errors/__init__.py`

```python
from dataclasses import dataclass
from enum import Enum

class ErrorCategory(Enum):
    LLM_PROVIDER = "llm_provider"       # ConnectionError, TimeoutError → 503
    CACHE_OPERATION = "cache_operation" # Cache failures → degrade gracefully
    DATA_CORRUPTION = "data_corruption" # Invalid JSON/Schema → 500
    DATABASE = "database"               # aiosqlite.Error → 503/500
    FILE_IO = "file_io"                 # File operations → 400/503
    VALIDATION = "validation"           # Invalid input → 400

@dataclass(frozen=True)
class DomainError:
    """Base domain error - pure, no IO, no infrastructure deps."""
    category: ErrorCategory
    message: str
    error_id: str  # For Sentry tracking
    context: dict[str, str]  # Structured logging context

    def to_dict(self) -> dict:
        return {
            "category": self.category.value,
            "message": self.message,
            "error_id": self.error_id,
            **self.context
        }

# Specific error types
@dataclass(frozen=True)
class LLMProviderError(DomainError):
    provider: str
    model: str
    original_exception: str

@dataclass(frozen=True)
class CacheError(DomainError):
    cache_key: str
    operation: str

@dataclass(frozen=True)
class DatabaseError(DomainError):
    operation: str
    db_path: str
```

### 2. Result Type

**Location:** `hemdov/domain/types/result.py`

```python
from typing import TypeVar, Generic

T = TypeVar('T')
E = TypeVar('E', bound=DomainError)

@dataclass(frozen=True)
class Success(Generic[T]):
    value: T

@dataclass(frozen=True)
class Failure(Generic[E]):
    error: E

Result = Success[T] | Failure[E]

def is_success(result: Result[T, E]) -> bool:
    return isinstance(result, Success)

def is_failure(result: Result[T, E]) -> bool:
    return isinstance(result, Failure)
```

### 3. Error ID Registry

**Location:** `api/errors/ids.py`

```python
class ErrorIds:
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

### 4. Exception Mapper

**Location:** `hemdov/infrastructure/errors/mapper.py`

```python
from aiosqlite import Error as AiosqliteError
import logging

logger = logging.getLogger(__name__)

class ExceptionMapper:
    """Converts low-level exceptions to domain errors with full context."""

    @staticmethod
    def map_database_error(
        e: Exception,
        operation: str,
        db_path: str,
        query_context: str = ""
    ) -> DatabaseError:
        """Map aiosqlite errors to DatabaseError with specific types."""
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
            error_id = ErrorIds.DB_QUERY_FAILED
            error_type = type(e).__name__

        context = {
            "operation": operation,
            "db_path": str(db_path),
            "original_exception": error_type,
            "query_context": query_context[:200] if query_context else ""
        }

        logger.error(
            f"Database error in {operation}: {error_type}: {e}. "
            f"Error ID: {error_id}",
            extra=context
        )

        return DatabaseError(
            category=ErrorCategory.DATABASE,
            message=f"Database {operation} failed: {e}",
            error_id=error_id,
            context=context,
            operation=operation,
            db_path=db_path
        )

    @staticmethod
    def map_llm_error(
        e: Exception,
        provider: str,
        model: str,
        prompt_length: int = 0
    ) -> LLMProviderError:
        """Map LLM provider errors to LLMProviderError."""
        if isinstance(e, ConnectionError):
            error_id = ErrorIds.LLM_CONNECTION_FAILED
            error_type = "ConnectionError"
        elif isinstance(e, TimeoutError):
            error_id = ErrorIds.LLM_TIMEOUT
            error_type = "TimeoutError"
        else:
            error_id = ErrorIds.LLM_UNKNOWN_ERROR
            error_type = type(e).__name__

        context = {
            "provider": provider,
            "model": model,
            "prompt_length": str(prompt_length),
            "original_exception": error_type
        }

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
        """Map cache operation errors to CacheError."""
        if isinstance(e, aiosqlite.IntegrityError):
            error_id = ErrorIds.CACHE_CONSTRAINT_VIOLATION
            error_type = "IntegrityError"
        else:
            error_id = ErrorIds.CACHE_SET_FAILED
            error_type = type(e).__name__

        context = {
            "operation": operation,
            "cache_key": cache_key[:8],  # First 8 chars for logging
            "prompt_id": prompt_id,
            "original_exception": error_type
        }

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

---

## Migration Strategy

### Phase 1: Foundation (No Breaking Changes)

**Files to create:**
1. `hemdov/domain/errors/__init__.py` - Domain error types
2. `hemdov/domain/types/result.py` - Result type
3. `hemdov/infrastructure/errors/mapper.py` - ExceptionMapper
4. `api/errors/ids.py` - Error ID registry
5. `tests/test_domain/test_result.py` - Result type tests
6. `tests/test_infrastructure/test_exception_mapper.py` - Mapper tests

**Success criteria:**
- All error types serialize correctly
- Result pattern matching works
- ExceptionMapper preserves error context

### Phase 2: Migrate Critical Paths (Feature Flag Controlled)

**Migration Order:**
1. `parallel_loader.py` (highest user impact - blocks Ctrl+C)
2. `sqlite_prompt_repository.py` cache operations
3. `metrics_repository.py`
4. LiteLLM adapters
5. `migrations.py`

**Per-Module Pattern:**

```python
# config/feature_flags.py - Add migration flags
enable_result_types_parallel_loader: bool = _parse_bool(getenv("ENABLE_RESULT_PARALLEL_LOADER", "false"))
enable_result_types_cache: bool = _parse_bool(getenv("ENABLE_RESULT_CACHE", "false"))
enable_result_types_metrics: bool = _parse_bool(getenv("ENABLE_RESULT_METRICS", "false"))
enable_result_types_adapters: bool = _parse_bool(getenv("ENABLE_RESULT_ADAPTERS", "false"))

# Old method (preserved for compatibility)
async def cache_prompt(self, cache_key: str, prompt_id: str, improved_prompt: str) -> bool:
    """Legacy cache method - returns False on error."""
    if FeatureFlags.enable_result_types_cache:
        return await self.cache_prompt_v2(cache_key, prompt_id, improved_prompt)
    # Old implementation...
    try:
        await conn.execute(...)
        return True
    except Exception as e:
        logger.error(f"Failed to cache prompt: {e}")
        return False

# New method (Result-based)
async def cache_prompt_v2(
    self, cache_key: str, prompt_id: str, improved_prompt: str
) -> Result[bool, CacheError]:
    """New cache method - returns Result."""
    # New implementation...
```

### Phase 3: Deprecation & Cleanup

Once all callers use `_v2` methods:
1. Remove old methods
2. Remove `_v2` suffix (rename to original names)
3. Remove feature flags
4. Update all callers

---

## PR Workflow

### Per-Module PR Template

```bash
# Branch naming: fix/error-handling-<module>
git checkout -b fix/error-handling-parallel-loader

# 1. Create Result-based implementation
# 2. Add tests for error paths
# 3. Enable via feature flag (default off)
# 4. Update documentation

git commit -am "feat: add Result-based error handling to parallel_loader

- Add load_all_v2() returning Result[List[ContextItem], FileIOError]
- Add ExceptionMapper for file I/O errors
- Add tests for all error paths (FileNotFoundError, PermissionError, etc.)
- Feature flag: ENABLE_RESULT_PARALLEL_LOADER
- Error IDs: IO-001, IO-002, IO-003, IO-004

Fixes: #<issue-if-any>

Co-Authored-By: Claude <noreply@anthropic.com>"

git push origin fix/error-handling-parallel-loader
gh pr create --title "feat: Result-based error handling for parallel_loader" \
             --body "See PR template in design doc"
```

### PR Description Template

```markdown
## Summary
- Adds Result-based error handling to `<module>` module
- Preserves existing API (gradual migration)
- Feature flag controlled (default: disabled)

## Changes
- Added `<method>_v2()` returning `Result[T, Error]`
- Added ExceptionMapper for specific error types
- Added tests for all error paths
- Feature flag: `ENABLE_RESULT_<MODULE>`

## Test plan
- [x] Unit tests for new error paths
- [x] Integration tests with feature flag enabled
- [x] Verified Error IDs appear in logs
- [ ] Manual testing with flag enabled in staging

## Rollback plan
Disable feature flag: `ENABLE_RESULT_<MODULE>=false`

## Monitoring
Check Sentry for new Error IDs: `IO-001`, `IO-002`, etc.
```

### Post-Merge Workstation Cleanup

```bash
# After PR is merged and verified
git checkout main
git pull

# Delete local branch
git branch -d fix/error-handling-<module>

# Delete remote branch
git push origin --delete fix/error-handling-<module>

# Clean up worktrees
git worktree list
# If worktree exists:
git worktree remove ../raycast_ext-<module>

# Clean untracked files
git clean -fd

# Verify clean state
git status  # Should show clean
```

**Automation Script:** `scripts/cleanup-after-pr.sh`

```bash
#!/bin/bash
BRANCH_NAME=$1

if [ -z "$BRANCH_NAME" ]; then
    echo "Usage: $0 <branch-name>"
    exit 1
fi

git checkout main
git pull

git branch -d "$BRANCH_NAME" 2>/dev/null || echo "Local branch already deleted"
git push origin --delete "$BRANCH_NAME" 2>/dev/null || echo "Remote branch already deleted"

WORKTREE_PATH=$(git worktree list | grep "$BRANCH_NAME" | awk '{print $1}')
if [ -n "$WORKTREE_PATH" ]; then
    git worktree remove "$WORKTREE_PATH"
    echo "Removed worktree: $WORKTREE_PATH"
fi

git clean -fd

echo "✅ Cleanup complete. Ready for next task."
git status
```

---

## Testing Strategy

### Unit Tests for ExceptionMapper

```python
# tests/test_infrastructure/test_exception_mapper.py

class TestExceptionMapper:
    def test_map_connection_error_includes_full_context(self):
        """All context captured (provider, model, error_id)."""
        error = ConnectionError("Network unreachable")
        result = ExceptionMapper.map_llm_error(
            error, provider="anthropic", model="claude-haiku-4-5"
        )
        assert result.category == ErrorCategory.LLM_PROVIDER
        assert result.error_id == ErrorIds.LLM_CONNECTION_FAILED
        assert result.context["original_exception"] == "ConnectionError"

    def test_map_uses_specific_error_types(self):
        """Uses specific Error ID, not generic."""
        error = PermissionError("Access denied")
        result = ExceptionMapper.map_database_error(
            error, operation="initialize", db_path="/data/metrics.db"
        )
        assert result.error_id == ErrorIds.DB_PERMISSION_DENIED
```

### Result Type Tests

```python
# tests/test_domain/test_result.py

class TestResultType:
    def test_success_branch_executes(self):
        """Success branch executes when Result is Success."""
        result: Result[str, DomainError] = Success("value")
        assert is_success(result)
        assert result.value == "value"

    def test_failure_branch_forces_error_handling(self):
        """Cannot access value when Result is Failure."""
        result: Result[str, DomainError] = Failure(
            DomainError(ErrorCategory.VALIDATION, "Invalid", "VAL-001", {})
        )
        assert is_failure(result)
        assert result.error.message == "Invalid"
```

### Error Path Coverage

```python
# tests/test_infrastructure/test_sqlite_prompt_repository_error_paths.py

@pytest.mark.asyncio
async def test_cache_prompt_handles_constraint_violation():
    """Returns Failure with CacheError, not exception."""
    repo = SQLitePromptRepository(":memory:")
    await repo.initialize()

    # Simulate constraint by inserting duplicate cache_key
    result: Result[bool, CacheError] = await repo.cache_prompt_v2(
        "duplicate_key", "prompt1", "improved"
    )

    assert is_failure(result)
    assert result.error.error_id == ErrorIds.CACHE_CONSTRAINT_VIOLATION
```

### Integration Tests with Feature Flags

```python
# tests/integration/test_error_handling_migration.py

@pytest.fixture
def with_result_types_enabled():
    os.environ["ENABLE_RESULT_CACHE"] = "true"
    yield
    os.unsetenv("ENABLE_RESULT_CACHE")

@pytest.mark.asyncio
async def test_cache_uses_result_when_flag_enabled(with_result_types_enabled):
    flags = FeatureFlags.load()
    assert flags.enable_result_types_cache is True
    # ... test Result-based implementation ...
```

---

## Success Metrics

### Pre-Migration Baseline

```bash
# Count broad exceptions
grep -r "except Exception" hemdov/infrastructure/ | wc -l
# Expected: 1+ (parallel_loader.py:46)

# Count silent failures
grep -r "return False" hemdov/infrastructure/persistence/ | wc -l
# Expected: 2+ (cache operations)

# Test coverage
pytest --cov=hemdov.infrastructure --cov-report=term-missing
# Current: ~65%
```

### Post-Migration Targets

```bash
# Zero broad exceptions
grep -r "except Exception" hemdov/infrastructure/ | wc -l
# Target: 0

# All errors have Error IDs
grep -r "ErrorIds\." hemdov/infrastructure/ | wc -l
# Target: 20+ (all error paths)

# Test coverage >80%
pytest tests/test_infrastructure/ --cov=hemdov.infrastructure --cov-report=term-missing
# Target: 85%
```

---

## Issues Addressed

| Issue | File | Fix |
|-------|------|-----|
| Broad exception catching | `parallel_loader.py:46` | Specific exception types with Error IDs |
| Silent cache failures | `sqlite_prompt_repository.py:368-409` | Result[bool, CacheError] |
| Missing error context | `metrics_repository.py:62-71` | ExceptionMapper with structured logging |
| Overly broad adapter errors | `litellm_dspy_adapter.py:73` | Specific error type mapping |
| Data corruption silent handling | `sqlite_prompt_repository.py:286-294` | Failure(DataCorruptionError) instead of fallback |
| Missing migration error handling | `migrations.py:112-134` | Transaction with specific error types |

---

## Constraints & Non-Goals

### Constraints (Non-negotiable)
1. **Hexagonal architecture** - Domain layer stays pure (no IO, no async)
2. **API stability** - Frontend integration must continue working
3. **Test compatibility** - Works with existing pytest fixtures
4. **Gradual migration** - Old and new coexist via feature flags

### Non-Goals
- Breaking existing API contracts
- Changing domain layer (only adding error types)
- Migrating API layer (already handles HTTP mapping correctly)
- Using external libraries beyond `typing_extensions` (for Result type if needed)

---

## Open Questions

1. **Result type implementation** - Use `typing_extensions` or custom implementation?
   - **Decision:** Custom implementation for Python 3.9+ compatibility

2. **Error ID format** - Prefix format (e.g., `LLM-001`) or hierarchical (`llm.connection_failed`)?
   - **Decision:** Prefix format for Sentry compatibility

3. **Feature flag lifecycle** - When to remove flags?
   - **Decision:** After 2 weeks of production monitoring with no issues

---

## References

- Code review findings: `/cm-multi-review` output (2026-01-15)
- Project guidelines: `CLAUDE.md` - Error handling section
- HTTP status mapping: `docs/api-error-handling.md`
