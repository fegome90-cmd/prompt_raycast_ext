# Sprint Plan: Code Review Fixes

> Generated: 2026-02-21
> Branch: feature/code-review-fixes-final
> Status: **READY FOR IMPLEMENTATION**

## Sprint Overview

| Metric | Value |
|--------|-------|
| Total Tasks | 15 |
| Completed | 0 |
| Remaining | 15 |
| Estimated Time | ~1.5-2 hours |
| Priority | P0 (blocks PR) |

## Verification Status (2026-02-21)

Ran `mypy --strict api/` and `ruff check api/` to verify current state:

**mypy:** 50+ errors (most are DSPy/Starlette stubs, but plan items remain)
**ruff:** 44 E501 + 1 I001 (import order)

---

## Sprint Backlog

### Phase 1: CRITICAL Fixes (30 min) - 4 tasks

| ID | Task | File | Status |
|----|------|------|--------|
| 1.1 | Add return type annotation to `create_exception_handlers()` | `api/exception_utils.py:55` | ❌ TODO |
| 1.2 | Add type parameters `dict[str, bool]` | `api/exception_utils.py:165` | ❌ TODO |
| 1.3 | Replace `typing.Self` → `typing_extensions.Self` | `hemdov/infrastructure/config/feature_flags.py:12` | ❌ TODO |
| 1.4 | Add `from None` to exception chaining (3 locations) | `api/prompt_improver_api.py:483-498` | ❌ TODO |

<details>
<summary>Implementation Details</summary>

#### 1.1 Return type annotation
```python
# Before
def create_exception_handlers():

# After
def create_exception_handlers() -> dict[type[Exception], Callable[[Request, Exception], Awaitable[JSONResponse]]]:
```

#### 1.2 Dict type parameters
```python
# Before
degradation_flags: dict,

# After
degradation_flags: dict[str, bool],
```

#### 1.3 typing_extensions.Self
```python
# Before
from typing import Self

# After
from typing_extensions import Self
```

#### 1.4 Exception chaining
```python
# Before
except asyncio.TimeoutError:
    raise HTTPException(status_code=504, detail="...")

# After
except asyncio.TimeoutError:
    raise HTTPException(status_code=504, detail="...") from None
```
</details>

---

### Phase 2: Import Order (15 min) - 2 tasks

| ID | Task | File | Status |
|----|------|------|--------|
| 2.1 | Fix import order (I001 error) | `api/main.py` | ❌ TODO |
| 2.2 | Move imports to top | `api/prompt_improver_api.py` | ❌ TODO |

<details>
<summary>Implementation Details</summary>

Run `ruff check --fix api/main.py` for auto-fix, then verify with `ruff check api/main.py`.

Import order: stdlib → third-party → local
</details>

---

### Phase 3: Deprecation Fix (5 min) - 1 task

| ID | Task | File | Status |
|----|------|------|--------|
| 3.1 | Use `collections.abc.Awaitable` | `api/middleware/request_id.py:4` | ❌ TODO |

<details>
<summary>Implementation Details</summary>

```python
# Before
from typing import Awaitable

# After
from collections.abc import Awaitable
```
</details>

---

### Phase 4: Security Hardening (30 min) - 3 tasks

| ID | Task | File | Status |
|----|------|------|--------|
| 4.1 | Add CORS_ORIGINS environment variable | `api/main.py` + `hemdov/infrastructure/config/__init__.py` | ❌ TODO |
| 4.2 | Add health check security docstring | `api/main.py` health endpoint | ❌ TODO |
| 4.3 | Validate request ID header with regex | `api/middleware/request_id.py:19-24` | ❌ TODO |

<details>
<summary>Implementation Details</summary>

#### 4.1 CORS environment variable
```python
# Add to Settings (hemdov/infrastructure/config/__init__.py)
CORS_ORIGINS: str = Field(default="*", description="Comma-separated CORS origins")

# Update middleware (api/main.py)
cors_origins = settings.CORS_ORIGINS.split(",") if settings.CORS_ORIGINS != "*" else ["*"]
```

#### 4.2 Health check docstring
Add to health endpoint:
```python
"""
Health check endpoint with state simulation for testing.

Security note: In production, consider rate limiting this endpoint
to prevent DoS attacks. Use nginx rate limiting or similar.
"""
```

#### 4.3 Request ID validation
```python
import re

REQUEST_ID_PATTERN = re.compile(r'^[a-zA-Z0-9-]{1,36}$')

client_id = request.headers.get("X-Request-ID")
if client_id and REQUEST_ID_PATTERN.match(client_id):
    request_id = client_id
else:
    request_id = uuid.uuid4().hex[:8]
```
</details>

---

### Phase 5: Line Length (20 min) - 1 task

| ID | Task | File | Status |
|----|------|------|--------|
| 5.1 | Fix E501 errors (44 lines > 100 chars) | `api/*.py` (multiple files) | ❌ TODO |

<details>
<summary>Files with E501 errors</summary>

| File | Count |
|------|-------|
| `api/circuit_breaker.py` | 1 |
| `api/exception_utils.py` | 5 |
| `api/main.py` | 4 |
| `api/quality_gates.py` | 26 |
| `api/prompt_improver_api.py` | 8 |

**Strategy:** Break long f-strings and function signatures across multiple lines.
</details>

---

### Phase 6: Dependencies (10 min) - 2 tasks

| ID | Task | File | Status |
|----|------|------|--------|
| 6.1 | Add `typing_extensions>=4.0.0` to dependencies | `pyproject.toml` | ❌ TODO |
| 6.2 | Add CORS_ORIGINS to Settings export | `hemdov/infrastructure/config/__init__.py` | ❌ TODO |

---

## Verification Checklist

Run after all phases complete:

```bash
# Type checking
mypy --strict api/

# Linting
ruff check api/

# Tests
make test

# Manual verification
make dev && make health
```

### Success Criteria

- [ ] `mypy --strict api/` passes (or only DSPy/Starlette stub errors)
- [ ] `ruff check api/` passes with 0 errors
- [ ] All tests pass (`make test`)
- [ ] Backend starts (`make dev`)
- [ ] Health endpoint responds (`make health`)

---

## Risks & Mitigations

| Risk | Mitigation | Impact |
|------|------------|--------|
| typing_extensions not installed | Already pydantic dependency | Low |
| CORS change breaks frontend | Test with Raycast locally | Medium |
| Import reordering causes circular import | Run tests after each change | Low |
| Line length fixes break string formatting | Manual review of f-strings | Low |

---

## Sprint Timeline

```
[ ] Phase 1: CRITICAL (30 min)
[ ] Phase 2: Import Order (15 min)
[ ] Phase 3: Deprecation (5 min)
[ ] Phase 4: Security (30 min)
[ ] Phase 5: Line Length (20 min)
[ ] Phase 6: Dependencies (10 min)
[ ] Verification (10 min)
─────────────────────────────────
Total: ~2 hours
```

---

## Status

- [x] Plan created
- [x] Verification status documented
- [ ] User approved
- [ ] Implementation started
- [ ] All phases complete
- [ ] Verified with mypy/ruff
- [ ] Ready for PR
