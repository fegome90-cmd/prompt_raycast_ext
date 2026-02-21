# Design: Prompt History Viewer Code Review Fixes

**Date:** 2026-02-21
**Status:** Approved
**Priority:** Production Ready (all 9 fixes)
**Updated:** Added error handling findings from silent-failure-hunter agent

## Context

Code review (4 agents) identified 9 issues in the Prompt History Viewer implementation:

| # | Issue | Severity | Layer | Source |
|---|-------|----------|-------|--------|
| 1 | Container `_cleanup_hooks` access | Critical | Infrastructure | code-reviewer |
| 2 | Missing tests | Critical | All | code-reviewer |
| 3 | LIKE wildcards not escaped | Critical | Infrastructure | code-reviewer |
| 4 | Log format missing exception type | Important | API | code-reviewer |
| 5 | No rate limiting | Important | API | code-reviewer |
| 6 | No CSP headers | Important | Frontend | code-reviewer |
| 7 | Fetch errors lose response body | High | Frontend | silent-failure-hunter |
| 8 | No network error handling in JS | Medium | Frontend | silent-failure-hunter |
| 9 | Static mount without error handling | High | API | silent-failure-hunter |

## Design Approach

**Fix by Layer (inside-out):**
1. Domain/Infrastructure (Container, LIKE)
2. API (Logs, Rate Limit, Static mount)
3. Frontend (CSP, Fetch errors, Network errors)
4. Validation (Tests)

## Fix Details

### Fix 1: Container Public Method

**File:** `hemdov/interfaces.py`

Add public method to Container class:

```python
def add_cleanup_hook(self, hook: Callable) -> None:
    """Register a cleanup hook for shutdown."""
    self._cleanup_hooks.append(hook)
```

**Update:** `api/prompt_history_api.py:31`

```python
# Before:
container._cleanup_hooks.append(cleanup)

# After:
container.add_cleanup_hook(cleanup)
```

**Note:** The `_get_repo()` logic duplicates `get_repository()` from `prompt_improver_api.py`. Consider extracting to shared `api/repository_utils.py` in a future refactor (not blocking for this PR).

### Fix 2: LIKE Wildcard Escaping

**File:** `hemdov/infrastructure/persistence/sqlite_prompt_repository.py:202`

```python
# Before:
pattern = f"%{query}%"

# After:
escaped_query = query.replace("%", "\\%").replace("_", "\\_")
pattern = f"%{escaped_query}%"
```

### Fix 3: Remove Redundant Error Handling + Simplify

**File:** `api/prompt_history_api.py`

**Finding from simplification agent:** The try/catch blocks in the endpoints are redundant because `api/exception_utils.py` already has global handlers for `ConnectionError`, `OSError`, and `RuntimeError` that map to the same status codes.

**Solution:** Remove the redundant try/catch blocks and let global handlers manage errors. This simplifies endpoints significantly:

```python
# Before (with redundant try/catch):
@router.get("/")
async def list_prompts(...) -> dict:
    try:
        repo = await _get_repo()
        prompts = await repo.find_recent(...)
        return {...}
    except ConnectionError as e:
        logger.error(f"Database unavailable: {e}")
        raise HTTPException(status_code=503, detail="Database unavailable")
    except OSError as e:
        ...
    except RuntimeError as e:
        ...

# After (simplified - global handlers do the work):
@router.get("/")
async def list_prompts(...) -> dict:
    repo = await _get_repo()
    prompts = await repo.find_recent(
        limit=limit, offset=offset, provider=provider, backend=backend
    )
    return {
        "prompts": [_to_dict(p) for p in prompts],
        "count": len(prompts),
        "limit": limit,
        "offset": offset,
    }
```

Apply to all 3 endpoints: `list_prompts`, `search_prompts`, `get_stats`

### Fix 4: Rate Limiting

**File:** `api/prompt_history_api.py`

Add rate limiting using existing patterns (or slowapi):

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@router.get("/")
@limiter.limit("60/minute")
async def list_prompts(...):
    ...
```

**Alternative:** Use nginx/PM2 rate limiting if available.

### Fix 5: CSP Headers for Static Files

**File:** `api/main.py`

Add CSP headers middleware for static files:

```python
from starlette.middleware.base import BaseHTTPMiddleware

class CSPMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        if request.url.path.startswith("/static/"):
            response.headers["Content-Security-Policy"] = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' https://cdn.tailwindcss.com; "
                "style-src 'self' 'unsafe-inline' https://cdn.tailwindcss.com;"
            )
        return response

app.add_middleware(CSPMiddleware)
```

### Fix 6: Fetch Error Body Extraction + Rename

**File:** `static/viewer.html`

**Changes:**
1. Rename `fetchWithAuth` to `fetchJson` (no auth is performed - misleading name)
2. Extract error detail from response body

```javascript
// Before:
async function fetchWithAuth(url) {
    const res = await fetch(url);
    if (!res.ok) {
        throw new Error(`HTTP ${res.status}: ${res.statusText}`);
    }
    return res.json();
}

// After:
async function fetchJson(url) {
    const res = await fetch(url);
    if (!res.ok) {
        let detail = `HTTP ${res.status}: ${res.statusText}`;
        try {
            const body = await res.json();
            if (body.detail) {
                detail = body.detail;
            }
        } catch (parseError) {
            // Response body wasn't JSON, use status text
        }
        throw new Error(detail);
    }
    return res.json();
}

// Update all calls: fetchWithAuth(...) -> fetchJson(...)
```

### Fix 7: Network Error Handling

**File:** `static/viewer.html`

Add network-level error handling to all fetch calls:

```javascript
// In loadPrompts(), loadStats(), search():
} catch (e) {
    // Distinguish network errors from HTTP errors
    if (e instanceof TypeError && e.message.includes('fetch')) {
        showError('Cannot connect to server. Check that backend is running on port 8000.');
    } else {
        showError(`Error: ${e.message}`);
    }
}
```

### Fix 8: Static Mount Error Handling

**File:** `api/main.py`

Validate static directory exists before mounting:

```python
# Before:
app.mount("/static", StaticFiles(directory="static"), name="static")

# After:
import os
static_dir = "static"
if os.path.isdir(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")
else:
    logger.warning(f"Static directory '{static_dir}' not found, viewer will be unavailable")
```

### Fix 9: Tests

**File:** `tests/test_prompt_history_api.py` (NEW)

**Priority test cases (from test coverage analysis):**

```python
import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)

# === CRITICAL TESTS (must have before merge) ===

def test_list_prompts_returns_503_on_connection_error():
    """Database unavailable should return 503."""
    with patch('api.prompt_history_api._get_repo', side_effect=ConnectionError("DB locked")):
        response = client.get("/api/v1/history/")
        assert response.status_code == 503
        assert "unavailable" in response.json()["detail"].lower()

def test_search_sql_injection_prevention():
    """Malicious SQL should be safely handled."""
    malicious_queries = [
        "'; DROP TABLE prompt_history; --",
        "test' OR '1'='1",
    ]
    for query in malicious_queries:
        response = client.get(f"/api/v1/history/search?q={query}")
        assert response.status_code == 200  # Not 500

def test_get_repo_creates_repo_when_not_registered():
    """First call should create and register repository."""
    from api.prompt_history_api import _get_repo
    # ... implementation

# === QUERY VALIDATION TESTS ===

class TestQueryValidation:
    def test_list_limit_below_minimum_returns_422(self):
        response = client.get("/api/v1/history/?limit=0")
        assert response.status_code == 422

    def test_list_limit_above_maximum_returns_422(self):
        response = client.get("/api/v1/history/?limit=101")
        assert response.status_code == 422

    def test_search_empty_query_returns_422(self):
        response = client.get("/api/v1/history/search?q=")
        assert response.status_code == 422

# === PAGINATION TESTS ===

class TestPagination:
    def test_offset_skips_records(self):
        """Offset should skip first N records."""
        page1 = client.get("/api/v1/history/?limit=10&offset=0").json()
        page2 = client.get("/api/v1/history/?limit=10&offset=10").json()
        assert page1["count"] <= 10
        assert page2["offset"] == 10

    def test_empty_results_return_empty_list(self):
        """Offset beyond data should return empty list."""
        response = client.get("/api/v1/history/?offset=10000").json()
        assert response["prompts"] == []

# === BASIC FUNCTIONALITY ===

def test_get_stats():
    response = client.get("/api/v1/history/stats")
    assert response.status_code == 200
    data = response.json()
    assert "total_count" in data
    assert "average_confidence" in data
```

## Implementation Order

1. **Container method** (2 min) - Fix encapsulation
2. **LIKE escaping** (2 min) - Security fix
3. **Log format** (3 min) - Observability
4. **Static mount validation** (2 min) - Prevent startup errors
5. **CSP headers** (5 min) - Security
6. **Fetch error extraction** (3 min) - Better UX
7. **Network error handling** (3 min) - Robustness
8. **Rate limiting** (10 min) - DoS protection
9. **Tests** (15 min) - Validation

**Total estimated time:** ~45 minutes

## Verification

```bash
# 1. Restart backend
pm2 restart raycast-backend-8000

# 2. Test endpoints
curl http://localhost:8000/api/v1/history/stats
curl "http://localhost:8000/api/v1/history/search?q=test%25"  # Should escape %

# 3. Test error response body extraction (disconnect DB and check error message)
curl http://localhost:8000/api/v1/history/stats  # Should show "Database unavailable" not "HTTP 503"

# 4. Run tests
pytest tests/test_prompt_history_api.py -v

# 5. Check CSP headers
curl -I http://localhost:8000/static/viewer.html | grep Content-Security-Policy

# 6. Test network error handling (stop backend and check viewer message)
# Open viewer.html, stop backend, should show "Cannot connect to server"
```

## Rollback Plan

Each fix is independent. If issues arise:

| Fix | Rollback |
|-----|----------|
| Container | Remove method, use `_cleanup_hooks` directly |
| LIKE | Remove escaping |
| Logs | Revert to `{e}` format |
| Static mount | Remove `os.path.isdir` check |
| CSP | Remove middleware |
| Fetch error | Revert to simple `HTTP {status}` format |
| Network errors | Remove TypeError catch |
| Rate limit | Remove decorator |
| Tests | Delete test file |

## Quick Start Path

```
docs/plans/2026-02-21-prompt-viewer-fixes-design.md
```

To resume:
```
/read docs/plans/2026-02-21-prompt-viewer-fixes-design.md
```
