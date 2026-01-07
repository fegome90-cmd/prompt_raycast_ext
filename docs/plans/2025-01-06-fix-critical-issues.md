# Implementation Plan: Fix Critical Issues from Code Review

> **Date:** 2026-01-06
> **Branch:** feature/nlac-integration
> **Worktree:** .worktrees/nlac-integration

## Overview

Multi-agent code review found **15 critical issues** that need fixing before merging. This plan organizes fixes by priority to minimize risk while addressing the most urgent problems first.

## Priority Categories

### Priority 1: Deprecated APIs (Breaking in Python 3.14+)
**Risk:** Code will break in Python 3.14+
**Effort:** Low (mechanical changes)

| File | Line | Issue | Fix |
|------|------|-------|-----|
| `hemdov/domain/entities/prompt_history.py` | 78 | `datetime.utcnow()` deprecated | Replace with `datetime.now(UTC)` |
| Any other files | - | Any `utcnow()` usage | Replace with `datetime.now(UTC)` |

### Priority 2: Silent Failures (Debugging Blockers)
**Risk:** Errors are swallowed, making debugging impossible
**Effort:** Medium (need to determine appropriate logging/error handling)

| File | Location | Issue | Fix |
|------|----------|-------|-----|
| `eval/src/strategy_selector.py` | Bare `except:` | No logging on exception | Add `logger.exception()` before re-raising or handling |
| `hemdov/infrastructure/persistence/sqlite_prompt_repository.py` | Multiple `except:` | Silent failures | Add structured logging with error details |
| `hemdov/domain/services/nlac_builder.py` | Any `except:` | Missing error context | Wrap with domain-specific exceptions |
| `hemdov/domain/services/oprop_optimizer.py` | Any `except:` | Missing error context | Wrap with domain-specific exceptions |
| `hemdov/domain/services/knn_provider.py` | Any `except:` | Missing error context | Add logging for KNN failures |

### Priority 3: Type Safety (Maintainability)
**Risk:** Runtime errors, poor IDE support
**Effort:** Medium-High (requires TypedDict or dataclass design)

| File | Issue | Fix |
|------|-------|-----|
| `hemdov/domain/services/nlac_builder.py` | `Dict[str, Any]` in `strategy_meta` | Create `StrategyMetadata` TypedDict |
| `hemdov/domain/services/oprop_optimizer.py` | `Dict[str, Any]` in trajectory | Create `TrajectoryEntry` TypedDict |
| `eval/src/strategies/nlac_strategy.py` | `Dict[str, Any]` in various places | Strongly-typed DTOs |

### Priority 4: Missing Tests (Confidence)
**Risk:** Regression, edge cases not covered
**Effort:** Medium

| Component | Missing Tests | Action |
|-----------|---------------|--------|
| `KNNProvider` | Error handling paths | Add tests for empty catalog, invalid queries |
| `ReflexionService` | Edge cases in refinement loop | Add tests for max iterations, executor failures |
| `NLaCStrategy` | Missing `_validate_inputs()` method | Implement method + add validation tests |
| `OPROOptimizer` | KNN integration edge cases | Add tests for empty KNN results |

## Implementation Batches

### Batch 1: Deprecated APIs (Priority 1)
**Files:** `hemdov/domain/entities/prompt_history.py` + global search

1. Search for all `utcnow()` usage: `grep -r "utcnow" --include="*.py" .`
2. Replace with `datetime.now(UTC)`
3. Add `from datetime import UTC` if not present
4. Run tests to verify: `pytest tests/ -v`
5. Commit: `fix(deps): replace deprecated datetime.utcnow() with datetime.now(UTC)`

### Batch 2: Silent Failures - Strategy Layer (Priority 2a)
**Files:** `eval/src/strategy_selector.py`, `eval/src/strategies/nlac_strategy.py`

1. For each bare `except:` block:
   - Determine if exception should be re-raised or handled
   - Add `logger.exception()` with context
   - Wrap with domain-specific exception if needed
2. Run tests: `pytest tests/test_nlac_strategy.py tests/test_strategy_selector.py -v`
3. Commit: `fix(error-handling): add logging to strategy layer exception handlers`

### Batch 3: Silent Failures - Services Layer (Priority 2b)
**Files:** `hemdov/domain/services/*.py`, `hemdov/infrastructure/persistence/*.py`

1. Add structured logging to all bare `except:` blocks
2. Use domain-specific exceptions where appropriate
3. Run tests: `pytest tests/test_nlac_services.py tests/test_knn_provider.py -v`
4. Commit: `fix(error-handling): add logging to services layer exception handlers`

### Batch 4: Type Safety - Core Types (Priority 3a)
**Files:** `hemdov/domain/dto/nlac_models.py` (new), update services

1. Create `hemdov/domain/dto/nlac_models.py` with TypedDict definitions:
   ```python
   from typing import TypedDict, Required, NotRequired

   class StrategyMetadata(TypedDict):
       intent: str
       complexity: str
       knn_enabled: bool
       fewshot_count: int
       rar_used: NotRequired[bool]
   ```
2. Replace `Dict[str, Any]` in services
3. Run tests: `pytest tests/ -v`
4. Commit: `refactor(types): replace Dict[str, Any] with TypedDict for type safety`

### Batch 5: Missing Implementation + Tests (Priority 4)
**Files:** `eval/src/strategies/nlac_strategy.py`, `tests/`

1. Implement missing `_validate_inputs()` method in NLaCStrategy
2. Add error handling tests for KNNProvider
3. Add edge case tests for ReflexionService
4. Run all tests: `pytest tests/ -v --cov`
5. Commit: `feat(tests): add missing validation and error handling tests`

## Verification

After all batches:
1. Run full test suite: `pytest tests/ -v --cov`
2. Run quality gates: `make eval`
3. Verify code review passes: `cm-multi-review` with comprehensive preset
4. Check all 15 critical issues are resolved

## Success Criteria

- [ ] All `utcnow()` replaced with `datetime.now(UTC)`
- [ ] All bare `except:` blocks have logging
- [ ] `Dict[str, Any]` replaced with TypedDict in core services
- [ ] `_validate_inputs()` implemented in NLaCStrategy
- [ ] Error handling tests added for KNNProvider, ReflexionService
- [ ] All tests passing (20+ passed)
- [ ] Code review shows 0 critical issues

## Rollback Plan

If any batch breaks functionality:
1. Revert the specific commit: `git revert <commit-hash>`
2. Investigate failure with `superpowers:systematic-debugging`
3. Fix and re-apply the batch

## Time Estimate

- Batch 1: 15 minutes
- Batch 2: 30 minutes
- Batch 3: 45 minutes
- Batch 4: 60 minutes
- Batch 5: 45 minutes
- **Total: ~3 hours**

## References

- Multi-agent review summary (from conversation)
- Python 3.14 deprecation warnings
- DSPy documentation on error handling
- Pydantic TypedDict best practices
