# Sprint Plan: Code Review Fixes

> Generated: 2026-02-21
> Branch: feature/code-review-fixes-final
> Status: **✅ COMPLETED**

## Sprint Overview

| Metric | Value |
|--------|-------|
| Total Tasks | 15 |
| Completed | 15 |
| Remaining | 0 |
| Actual Time | ~1.5 hours |
| Priority | P0 (blocks PR) |

## Verification Status (2026-02-21 - FINAL)

**ruff:** 0 errors ✅
**mypy:** DSPy/Starlette stub errors only (expected)
**tests:** 19/20 passing (1 preexisting failure unrelated to this sprint)

---

## Sprint Backlog

### Phase 1: CRITICAL Fixes (30 min) - 4 tasks ✅

| ID | Task | File | Status |
|----|------|------|--------|
| 1.1 | Add return type annotation to `create_exception_handlers()` | `api/exception_utils.py:55` | ✅ DONE |
| 1.2 | Add type parameters `dict[str, bool]` | `api/exception_utils.py:165` | ✅ DONE |
| 1.3 | Replace `typing.Self` → `typing_extensions.Self` | `hemdov/infrastructure/config/feature_flags.py:12` | ✅ DONE |
| 1.4 | Add `from None` to exception chaining (3 locations) | `api/prompt_improver_api.py:483-498` | ✅ DONE |

---

### Phase 2: Import Order (15 min) - 2 tasks ✅

| ID | Task | File | Status |
|----|------|------|--------|
| 2.1 | Fix import order (I001 error) | `api/main.py` | ✅ DONE |
| 2.2 | Move imports to top | `api/prompt_improver_api.py` | ✅ DONE |

---

### Phase 3: Deprecation Fix (5 min) - 1 task ✅

| ID | Task | File | Status |
|----|------|------|--------|
| 3.1 | Use `collections.abc.Awaitable` | `api/middleware/request_id.py:4` | ✅ DONE |

---

### Phase 4: Security Hardening (30 min) - 3 tasks ✅

| ID | Task | File | Status |
|----|------|------|--------|
| 4.1 | Add CORS_ORIGINS environment variable | `api/main.py` + `hemdov/infrastructure/config/__init__.py` | ✅ DONE |
| 4.2 | Add health check security docstring | `api/main.py` health endpoint | ✅ DONE |
| 4.3 | Validate request ID header with regex | `api/middleware/request_id.py:19-24` | ✅ DONE |

---

### Phase 5: Line Length (20 min) - 1 task ✅

| ID | Task | File | Status |
|----|------|------|--------|
| 5.1 | Fix E501 errors (43 lines > 100 chars) | `api/*.py` (multiple files) | ✅ DONE |

**Files fixed:**
- `api/circuit_breaker.py` (1)
- `api/exception_utils.py` (5)
- `api/main.py` (3)
- `api/metrics_api.py` (7)
- `api/prompt_improver_api.py` (12)
- `api/quality_gates.py` (15)

---

### Phase 6: Dependencies (10 min) - 2 tasks ✅

| ID | Task | File | Status |
|----|------|------|--------|
| 6.1 | Add `typing_extensions>=4.0.0` to dependencies | `pyproject.toml` | ✅ DONE |
| 6.2 | Add CORS_ORIGINS to Settings export | `hemdov/infrastructure/config/__init__.py` | ✅ DONE |

---

## Files Modified

| File | Changes |
|------|---------|
| `api/exception_utils.py` | Type annotations, import collections.abc, line length |
| `api/middleware/request_id.py` | collections.abc.Awaitable, regex validation for X-Request-ID |
| `api/main.py` | CORS_ORIGINS env var, health docstring, import order, line length |
| `api/prompt_improver_api.py` | Import order (moved all to top), line length, `from None` chaining |
| `api/quality_gates.py` | Line length, variable naming (l → line) |
| `api/metrics_api.py` | Line length |
| `api/circuit_breaker.py` | Line length |
| `hemdov/infrastructure/config/__init__.py` | CORS_ORIGINS setting |
| `hemdov/infrastructure/config/feature_flags.py` | typing_extensions.Self |
| `pyproject.toml` | typing-extensions>=4.0.0 dependency |

---

## Status

- [x] Plan created
- [x] Verification status documented
- [x] User approved
- [x] Implementation started
- [x] All phases complete
- [x] Verified with ruff (0 errors)
- [x] Ready for PR

---

## Next Steps

1. `git add .` - Stage all changes
2. `git commit -m "fix: code review fixes - types, security, line length"` - Commit
3. Create PR to merge `feature/code-review-fixes-final` → `main`
