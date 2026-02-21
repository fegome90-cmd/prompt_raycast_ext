# Code Review Fixes Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Fix 11 validated code review findings across Tests, Backend, Frontend, and Infrastructure domains.

**Architecture:** Domain-based approach - Tests first (safety net), then Backend (critical race condition), Frontend (duplication), Infrastructure (cleanup). Each task follows TDD: write test, verify fail, implement, verify pass, commit.

**Tech Stack:** Python (pytest, mypy, ruff), TypeScript (Vitest), FastAPI, React/Raycast

---

## Domain 1: Tests (4 tasks)

### Task 1: Create test_exception_utils.py

**Files:**
- Create: `tests/test_exception_utils.py`
- Reference: `api/exception_utils.py`

**Step 1: Write the failing test**

```python
# tests/test_exception_utils.py
"""Tests for api/exception_utils.py exception handlers."""

import pytest
from fastapi.exceptions import RequestValidationError
from fastapi import Request
from unittest.mock import MagicMock

from api.exception_utils import create_exception_handlers


class TestCreateExceptionHandlers:
    """Tests for create_exception_handlers function."""

    def test_returns_dict_with_expected_keys(self):
        """Should return dict with all expected exception type keys."""
        handlers = create_exception_handlers()

        expected_keys = {
            ValueError, KeyError, TypeError, AttributeError,
            ConnectionError, OSError, TimeoutError, ZeroDivisionError,
        }
        assert expected_keys.issubset(handlers.keys())


class TestValidationErrorHandler:
    """Tests for validation_error_handler (422 → 400 conversion)."""

    @pytest.mark.asyncio
    async def test_returns_400_status(self):
        """Should return 400 status code for validation errors."""
        handlers = create_exception_handlers()
        handler = handlers.get(object)  # Will need RequestValidationError

        # Create mock request and error
        mock_request = MagicMock(spec=Request)
        mock_request.url = MagicMock()
        mock_request.url.path = "/test"

        # Create a minimal validation error
        from pydantic import ValidationError
        from pydantic_core import ErrorDetails

        # Mock the RequestValidationError
        exc = MagicMock(spec=RequestValidationError)
        exc.errors.return_value = [
            {"loc": ("body", "field"), "msg": "Field required", "type": "missing"}
        ]

        # This will fail until we get the right handler key
        result = await handler(mock_request, exc)

        assert result.status_code == 400

    @pytest.mark.asyncio
    async def test_includes_field_in_error_message(self):
        """Should include field path in error message."""
        handlers = create_exception_handlers()

        mock_request = MagicMock(spec=Request)
        mock_request.url = MagicMock()
        mock_request.url.path = "/api/v1/test"

        exc = MagicMock(spec=RequestValidationError)
        exc.errors.return_value = [
            {"loc": ("body", "mode"), "msg": "Input should be 'legacy' or 'nlac'", "type": "literal_error"}
        ]

        # Get the validation error handler
        from fastapi.exceptions import RequestValidationError as RVE
        handler = handlers.get(RVE)

        result = await handler(mock_request, exc)
        body = json.loads(result.body)

        assert "'body.mode'" in body["detail"]
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_exception_utils.py -v`
Expected: FAIL (file doesn't exist yet)

**Step 3: Run test to verify it fails (after file creation)**

Run: `pytest tests/test_exception_utils.py -v`
Expected: Some tests fail (handler key lookup, etc.)

**Step 4: Fix imports and complete test**

```python
# tests/test_exception_utils.py
"""Tests for api/exception_utils.py exception handlers."""

import json
import pytest
from fastapi.exceptions import RequestValidationError
from fastapi import Request
from unittest.mock import MagicMock

from api.exception_utils import create_exception_handlers


class TestCreateExceptionHandlers:
    """Tests for create_exception_handlers function."""

    def test_returns_dict_with_expected_keys(self):
        """Should return dict with all expected exception type keys."""
        handlers = create_exception_handlers()

        expected_keys = {
            ValueError, KeyError, TypeError, AttributeError,
            ConnectionError, OSError, TimeoutError, ZeroDivisionError,
        }
        assert expected_keys.issubset(handlers.keys())

    def test_includes_request_validation_error(self):
        """Should include RequestValidationError handler."""
        handlers = create_exception_handlers()

        assert RequestValidationError in handlers


class TestValidationErrorHandler:
    """Tests for validation_error_handler (422 → 400 conversion)."""

    @pytest.mark.asyncio
    async def test_returns_400_status(self):
        """Should return 400 status code for validation errors."""
        handlers = create_exception_handlers()
        handler = handlers[RequestValidationError]

        mock_request = MagicMock(spec=Request)
        mock_request.url = MagicMock()
        mock_request.url.path = "/api/v1/test"

        exc = MagicMock(spec=RequestValidationError)
        exc.errors.return_value = [
            {"loc": ("body", "field"), "msg": "Field required", "type": "missing"}
        ]

        result = await handler(mock_request, exc)

        assert result.status_code == 400

    @pytest.mark.asyncio
    async def test_includes_field_in_error_message(self):
        """Should include field path in error message."""
        handlers = create_exception_handlers()
        handler = handlers[RequestValidationError]

        mock_request = MagicMock(spec=Request)
        mock_request.url = MagicMock()
        mock_request.url.path = "/api/v1/test"

        exc = MagicMock(spec=RequestValidationError)
        exc.errors.return_value = [
            {"loc": ("body", "mode"), "msg": "Input should be 'legacy' or 'nlac'", "type": "literal_error"}
        ]

        result = await handler(mock_request, exc)
        body = json.loads(result.body)

        assert "body.mode" in body["detail"]

    @pytest.mark.asyncio
    async def test_handles_integer_in_loc(self):
        """Should handle integer elements in loc array (e.g., array indices)."""
        handlers = create_exception_handlers()
        handler = handlers[RequestValidationError]

        mock_request = MagicMock(spec=Request)
        mock_request.url = MagicMock()
        mock_request.url.path = "/api/v1/test"

        exc = MagicMock(spec=RequestValidationError)
        exc.errors.return_value = [
            {"loc": ("body", "items", 0, "name"), "msg": "Field required", "type": "missing"}
        ]

        result = await handler(mock_request, exc)
        body = json.loads(result.body)

        assert "body.items.0.name" in body["detail"]
```

**Step 5: Run tests to verify they pass**

Run: `pytest tests/test_exception_utils.py -v`
Expected: All tests PASS

**Step 6: Commit**

```bash
git add tests/test_exception_utils.py
git commit -m "test: add unit tests for exception_utils validation_error_handler"
```

---

### Task 2: Add health simulate tests

**Files:**
- Modify: `tests/test_api_integration.py`
- Reference: `api/main.py:148-170`

**Step 1: Write the failing test**

```python
# Add to tests/test_api_integration.py in TestHealthCheck class

def test_health_simulate_unavailable_returns_503(self, client):
    """Simulate=unavailable should return 503."""
    response = client.get("/health?simulate=unavailable")

    assert response.status_code == 503

def test_health_simulate_degraded_returns_degraded_status(self, client):
    """Simulate=degraded should return degraded status with flags."""
    response = client.get("/health?simulate=degraded")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "degraded"
    assert "degradation_flags" in data

def test_health_simulate_healthy_returns_healthy(self, client):
    """Simulate=healthy should return normal healthy status."""
    response = client.get("/health?simulate=healthy")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
```

**Step 2: Run tests to verify they fail**

Run: `pytest tests/test_api_integration.py::TestHealthCheck -v`
Expected: Tests fail (simulate param not tested)

**Step 3: Verify tests pass**

Run: `pytest tests/test_api_integration.py::TestHealthCheck -v`
Expected: All tests PASS (simulate already implemented)

**Step 4: Commit**

```bash
git add tests/test_api_integration.py
git commit -m "test: add health endpoint simulate parameter tests"
```

---

### Task 3: Create test_feature_flags.py

**Files:**
- Create: `tests/test_feature_flags.py`
- Reference: `hemdov/infrastructure/config/feature_flags.py`

**Step 1: Write the failing test**

```python
# tests/test_feature_flags.py
"""Tests for hemdov/infrastructure/config/feature_flags.py."""

import json
import pytest
from pathlib import Path
from unittest.mock import patch

from hemdov.infrastructure.config.feature_flags import FeatureFlags, _parse_bool


class TestParseBool:
    """Tests for _parse_bool helper."""

    def test_true_values(self):
        """Should return True for truthy strings."""
        assert _parse_bool("true") is True
        assert _parse_bool("TRUE") is True
        assert _parse_bool("1") is True
        assert _parse_bool("yes") is True
        assert _parse_bool("YES") is True
        assert _parse_bool("on") is True
        assert _parse_bool("ON") is True

    def test_false_values(self):
        """Should return False for falsy strings."""
        assert _parse_bool("false") is False
        assert _parse_bool("0") is False
        assert _parse_bool("no") is False
        assert _parse_bool("off") is False

    def test_none_returns_false(self):
        """Should return False for None."""
        assert _parse_bool(None) is False

    def test_empty_string_returns_false(self):
        """Should return False for empty string."""
        assert _parse_bool("") is False

    def test_other_string_returns_false(self):
        """Should return False for unrecognized strings."""
        assert _parse_bool("maybe") is False


class TestFeatureFlagsDefaults:
    """Tests for FeatureFlags default values."""

    def test_default_values(self):
        """Should have correct default values."""
        flags = FeatureFlags()

        assert flags.enable_metrics is False
        assert flags.enable_knn is False
        assert flags.max_history_items == 100


class TestFeatureFlagsSave:
    """Tests for FeatureFlags.save()."""

    def test_save_creates_file(self, tmp_path: Path):
        """Should create file with correct JSON."""
        flags = FeatureFlags(enable_metrics=True, enable_knn=True)
        save_path = tmp_path / "flags.json"

        flags.save(save_path)

        assert save_path.exists()
        data = json.loads(save_path.read_text())
        assert data["enable_metrics"] is True
        assert data["enable_knn"] is True

    def test_save_creates_parent_directory(self, tmp_path: Path):
        """Should create parent directory if it doesn't exist."""
        flags = FeatureFlags()
        save_path = tmp_path / "nested" / "dir" / "flags.json"

        flags.save(save_path)

        assert save_path.exists()


class TestFeatureFlagsLoad:
    """Tests for FeatureFlags.load()."""

    def test_load_missing_file_returns_defaults(self, tmp_path: Path):
        """Should return defaults for non-existent file."""
        load_path = tmp_path / "nonexistent.json"

        flags = FeatureFlags.load(load_path)

        assert flags.enable_metrics is False
        assert flags.enable_knn is False

    def test_load_valid_file(self, tmp_path: Path):
        """Should load values from valid JSON file."""
        load_path = tmp_path / "flags.json"
        load_path.write_text(json.dumps({"enable_metrics": True, "enable_knn": True}))

        flags = FeatureFlags.load(load_path)

        assert flags.enable_metrics is True
        assert flags.enable_knn is True

    def test_load_invalid_json_raises(self, tmp_path: Path):
        """Should raise on invalid JSON."""
        load_path = tmp_path / "invalid.json"
        load_path.write_text("{ not valid json }")

        with pytest.raises(json.JSONDecodeError):
            FeatureFlags.load(load_path)
```

**Step 2: Run tests to verify they fail**

Run: `pytest tests/test_feature_flags.py -v`
Expected: FAIL (file doesn't exist)

**Step 3: Run tests to verify they pass**

Run: `pytest tests/test_feature_flags.py -v`
Expected: All tests PASS

**Step 4: Commit**

```bash
git add tests/test_feature_flags.py
git commit -m "test: add comprehensive tests for FeatureFlags save/load"
```

---

### Task 4: Add request ID middleware edge cases

**Files:**
- Modify: `tests/test_request_id_middleware.py`
- Reference: `api/middleware/request_id.py`

**Step 1: Write the failing tests**

```python
# Add to tests/test_request_id_middleware.py

def test_request_id_is_8_characters(client):
    """Generated ID should be exactly 8 characters (from uuid4.hex[:8])."""
    response = client.get("/health")

    request_id = response.headers.get("X-Request-ID")
    assert request_id is not None
    assert len(request_id) == 8

def test_empty_string_request_id_is_replaced(client):
    """Empty string header should be replaced with generated ID."""
    response = client.get("/health", headers={"X-Request-ID": ""})

    request_id = response.headers.get("X-Request-ID")
    assert request_id is not None
    assert len(request_id) == 8
    assert request_id != ""

def test_multiple_requests_have_unique_ids(client):
    """Multiple requests should get unique IDs."""
    ids = set()
    for _ in range(10):
        response = client.get("/health")
        ids.add(response.headers.get("X-Request-ID"))

    assert len(ids) == 10  # All unique
```

**Step 2: Run tests to verify they pass**

Run: `pytest tests/test_request_id_middleware.py -v`
Expected: All tests PASS

**Step 3: Commit**

```bash
git add tests/test_request_id_middleware.py
git commit -m "test: add edge case tests for request ID middleware"
```

---

## Domain 2: Backend (3 tasks)

### Task 5: Add asyncio.Lock for race condition

**Files:**
- Modify: `api/prompt_improver_api.py:249-278`
- Test: Run existing tests

**Step 1: Write the failing test (if needed)**

The race condition is hard to test deterministically. We'll rely on code review and existing tests.

**Step 2: Add the lock**

```python
# In api/prompt_improver_api.py, add after imports:
import asyncio

# Around line 249, add lock declaration:
_strategy_selector: dict[str, StrategySelector] = {}
_strategy_selector_lock = asyncio.Lock()

# Modify get_strategy_selector function (around line 253):
async def get_strategy_selector(settings: Settings, use_nlac: bool = False) -> StrategySelector:
    """Get or create strategy selector for the given mode."""
    selector_key = "nlac" if use_nlac else "legacy"

    # Use lock to prevent race condition during lazy initialization
    async with _strategy_selector_lock:
        if selector_key not in _strategy_selector:
            if use_nlac:
                _strategy_selector[selector_key] = _create_nlac_selector(settings)
            else:
                _strategy_selector[selector_key] = _create_legacy_selector(settings)

    return _strategy_selector[selector_key]
```

**Step 3: Run existing tests**

Run: `pytest tests/ -v -k "prompt_improver"`
Expected: All tests PASS

**Step 4: Run mypy**

Run: `mypy api/prompt_improver_api.py`
Expected: No errors

**Step 5: Commit**

```bash
git add api/prompt_improver_api.py
git commit -m "fix: add asyncio.Lock to prevent race condition in strategy selector"
```

---

### Task 6: Add RuntimeError to metrics init exception handling

**Files:**
- Modify: `api/main.py:100`
- Test: Run existing tests

**Step 1: Modify the exception tuple**

```python
# In api/main.py, around line 100, change:
except (ConnectionError, OSError) as e:

# To:
except (ConnectionError, OSError, RuntimeError) as e:
```

**Step 2: Run existing tests**

Run: `pytest tests/ -v`
Expected: All tests PASS

**Step 3: Commit**

```bash
git add api/main.py
git commit -m "fix: catch RuntimeError in metrics repository initialization"
```

---

### Task 7: Add production env check for health simulate

**Files:**
- Modify: `api/main.py:148-170`
- Test: `tests/test_api_integration.py`

**Step 1: Write the failing test**

```python
# Add to tests/test_api_integration.py TestHealthCheck class:

def test_health_simulate_blocked_in_production(self, client, monkeypatch):
    """Simulate parameter should be blocked in production environment."""
    monkeypatch.setenv("ENVIRONMENT", "production")

    response = client.get("/health?simulate=unavailable")

    assert response.status_code == 403
    assert "not allowed" in response.json()["detail"].lower()

def test_health_simulate_allowed_in_development(self, client, monkeypatch):
    """Simulate parameter should be allowed in non-production."""
    monkeypatch.setenv("ENVIRONMENT", "development")

    response = client.get("/health?simulate=unavailable")

    assert response.status_code == 503
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_api_integration.py::TestHealthCheck::test_health_simulate_blocked_in_production -v`
Expected: FAIL (not implemented yet)

**Step 3: Implement the production check**

```python
# In api/main.py, modify health_check function (around line 148):

import os

@app.get("/health")
async def health_check(
    simulate: HealthState = Query(
        default=HealthState.HEALTHY,
        description="Simulate health state for testing"
    )
) -> dict:
    """
    Health check endpoint for monitoring and load balancers.

    Returns current health status and optional degradation flags.
    """
    # Block simulation in production environment
    if simulate != HealthState.HEALTHY and os.getenv("ENVIRONMENT") == "production":
        raise HTTPException(
            status_code=403,
            detail="Simulation not allowed in production environment"
        )

    # Rest of function unchanged...
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/test_api_integration.py::TestHealthCheck -v`
Expected: All tests PASS

**Step 5: Commit**

```bash
git add api/main.py tests/test_api_integration.py
git commit -m "fix: block health simulate parameter in production environment"
```

---

## Domain 3: Frontend (3 tasks)

### Task 8: Extract toPercentage helper + add clamping

**Files:**
- Modify: `dashboard/src/core/design/typography.ts`
- Test: `dashboard/src/core/design/__tests__/typography.test.ts`

**Step 1: Write the failing test**

```typescript
// dashboard/src/core/design/__tests__/typography.test.ts

import { describe, it, expect } from "vitest";
import { Typography } from "../typography";

describe("Typography", () => {
  describe("toPercentage", () => {
    it("should convert 0-1 range to 0-100", () => {
      expect(Typography["toPercentage"](0.5)).toBe(50);
      expect(Typography["toPercentage"](0.85)).toBe(85);
      expect(Typography["toPercentage"](1)).toBe(100);
    });

    it("should clamp values below 0", () => {
      expect(Typography["toPercentage"](-0.5)).toBe(0);
      expect(Typography["toPercentage"](-10)).toBe(0);
    });

    it("should clamp values above 1", () => {
      expect(Typography["toPercentage"](1.5)).toBe(100);
      expect(Typography["toPercentage"](50)).toBe(100);
    });
  });

  describe("confidence", () => {
    it("should handle edge case values", () => {
      // Values > 1 should be clamped, not produce "1%" etc.
      expect(Typography.confidence(1.5)).toContain("100%");
      expect(Typography.confidence(-0.5)).toContain("0%");
    });
  });
});
```

**Step 2: Run test to verify it fails**

Run: `cd dashboard && npm test -- typography.test.ts`
Expected: FAIL (toPercentage doesn't exist)

**Step 3: Implement the helper**

```typescript
// In dashboard/src/core/design/typography.ts

export class Typography {
  /**
   * Convert 0-1 score to 0-100 percentage with clamping.
   * Handles edge cases where score might be outside expected range.
   */
  private static toPercentage(score: number): number {
    // Clamp to 0-1 range, then convert to percentage
    const clamped = Math.max(0, Math.min(1, score));
    return Math.round(clamped * 100);
  }

  /**
   * Format confidence score for display.
   * @param score - Confidence in 0-1 range (from DSPy backend)
   */
  static confidence(score: number): string {
    // Input is 0-1 range (from DSPy backend)
    const rounded = Typography.toPercentage(score);

    if (rounded >= 80) {
      return `${rounded}% ✨`;
    } else if (rounded >= 60) {
      return `${rounded}% ✓`;
    } else {
      return `${rounded}%`;
    }
  }

  /**
   * Get confidence icon based on score.
   * @param score - Confidence in 0-1 range (from DSPy backend)
   */
  static confidenceIcon(score: number): string {
    const rounded = Typography.toPercentage(score);

    if (rounded >= 80) return "⭐";
    if (rounded >= 60) return "✅";
    if (rounded >= 40) return "⚠️";
    return "❌";
  }

  // ... rest of class unchanged
}
```

**Step 4: Run tests to verify they pass**

Run: `cd dashboard && npm test -- typography.test.ts`
Expected: All tests PASS

**Step 5: Run all frontend tests**

Run: `cd dashboard && npm test`
Expected: All tests PASS

**Step 6: Commit**

```bash
git add dashboard/src/core/design/typography.ts dashboard/src/core/design/__tests__/typography.test.ts
git commit -m "refactor: extract toPercentage helper with clamping in Typography"
```

---

### Task 9: Extract CopyStartCommandAction component

**Files:**
- Modify: `dashboard/src/core/errors/handlers.tsx`
- Test: Run existing tests

**Step 1: Extract the component**

```typescript
// In dashboard/src/core/errors/handlers.tsx

// Add at top of file after imports:
import { Clipboard } from "@raycast/api";

// Add shared action component:
const CopyStartCommandAction = () => (
  <Action
    title="Copy Start Command"
    onAction={async () => {
      await Clipboard.copy(BACKEND_START_COMMAND);
      await showHUD("✓ Command copied! Paste in terminal");
    }}
  />
);

// Replace all 3 instances of:
//   <Action
//     title="Copy Start Command"
//     onAction={async () => {
//       await Clipboard.copy(BACKEND_START_COMMAND);
//       await showHUD("✓ Command copied! Paste in terminal");
//     }}
//   />
// With:
//   <CopyStartCommandAction />
```

**Step 2: Run frontend tests**

Run: `cd dashboard && npm test -- handlers`
Expected: All tests PASS

**Step 3: Commit**

```bash
git add dashboard/src/core/errors/handlers.tsx
git commit -m "refactor: extract CopyStartCommandAction to reduce duplication"
```

---

### Task 10: Add .tmp cleanup function

**Files:**
- Modify: `dashboard/src/core/promptStorage.ts`
- Test: `dashboard/src/core/__tests__/promptStorage.test.ts`

**Step 1: Write the failing test**

```typescript
// In dashboard/src/core/__tests__/promptStorage.test.ts (create if needed)

import { describe, it, expect, beforeEach, afterEach } from "vitest";
import { promises as fs } from "fs";
import { join } from "path";
import * as promptStorage from "../promptStorage";

describe("promptStorage", () => {
  describe("cleanupOrphanedTempFiles", () => {
    it("should remove .tmp files older than 1 hour", async () => {
      // This tests the cleanup function exists and works
      // Implementation detail: files older than threshold are removed
    });
  });
});
```

**Step 2: Implement the cleanup function**

```typescript
// In dashboard/src/core/promptStorage.ts

// Add after isENOENT function:
/**
 * Clean up orphaned .tmp files from interrupted atomic writes.
 * Removes files older than 1 hour.
 */
async function cleanupOrphanedTempFiles(): Promise<void> {
  try {
    // Ensure directory exists before trying to read it
    await ensureStorageDir();

    const files = await fs.readdir(STORAGE_DIR);
    const ONE_HOUR_MS = 3600000;

    for (const file of files) {
      if (file.endsWith(".tmp")) {
        const filePath = join(STORAGE_DIR, file);
        try {
          const stat = await fs.stat(filePath);
          // Remove files older than 1 hour
          if (Date.now() - stat.mtimeMs > ONE_HOUR_MS) {
            await fs.unlink(filePath);
            console.log(`${LOG_PREFIX} Cleaned up orphaned temp file: ${file}`);
          }
        } catch (error) {
          // Ignore errors on individual files (may have been cleaned up)
          if (!isENOENT(error)) {
            console.warn(`${LOG_PREFIX} Failed to check temp file ${file}:`, error);
          }
        }
      }
    }
  } catch (error) {
    // Don't throw on cleanup errors - just log
    console.warn(`${LOG_PREFIX} Failed to cleanup temp files:`, error);
  }
}

// Modify ensureStorageDir to call cleanup:
async function ensureStorageDir(): Promise<void> {
  try {
    await fs.mkdir(STORAGE_DIR, { recursive: true });
    // Clean up orphaned temp files on initialization
    await cleanupOrphanedTempFiles();
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    console.error(`${LOG_PREFIX} Failed to create storage directory: ${message}`);
    throw new Error(`Failed to initialize storage: ${message}`);
  }
}
```

**Step 3: Run frontend tests**

Run: `cd dashboard && npm test`
Expected: All tests PASS

**Step 4: Commit**

```bash
git add dashboard/src/core/promptStorage.ts
git commit -m "fix: add cleanup for orphaned .tmp files in promptStorage"
```

---

## Domain 4: Infrastructure (1 task - optional)

### Task 11: Extract port check helper in Makefile (optional)

**Files:**
- Modify: `Makefile`

**Step 1: Extract helper (optional cleanup)**

This is a low-priority refactoring. Can be deferred.

```makefile
# Helper for port checking
PORT_LISTENERS = $$(lsof -t -iTCP:$(BACKEND_PORT) -sTCP:LISTEN 2>/dev/null | tr '\n' ' ')

.PHONY: check-port
check-port:
	@if [ -n "$(PORT_LISTENERS)" ]; then \
		printf "\033[32m● Running\033[0m (port $(BACKEND_PORT), PID(s): $(PORT_LISTENERS))\n"; \
	else \
		printf "\033[31m○ Stopped\033[0m (port $(BACKEND_PORT) not in use)\n"; \
	fi
```

**Step 2: Commit (if implemented)**

```bash
git add Makefile
git commit -m "refactor: extract port check helper in Makefile"
```

---

## Final Steps

### Run Full Test Suite

```bash
# Backend
pytest tests/ -v --cov=api --cov=hemdov

# Frontend
cd dashboard && npm test -- --coverage

# Linting
ruff check api/ hemdov/
mypy api/ hemdov/
```

### Create Summary Commit

```bash
git add docs/plans/2026-02-20-code-review-fixes-comprehensive-design.md docs/plans/2026-02-20-code-review-fixes.md
git commit -m "docs: add code review fixes implementation plan"
```

---

## Summary

| Domain | Tasks | Files Modified | Tests Added |
|--------|-------|----------------|-------------|
| Tests | 4 | 4 | ~25 test cases |
| Backend | 3 | 2 | 2 test cases |
| Frontend | 3 | 3 | ~8 test cases |
| Infrastructure | 1 | 1 | 0 |
| **Total** | **11** | **10** | **~35** |
