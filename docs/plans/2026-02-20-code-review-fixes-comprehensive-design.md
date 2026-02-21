# Code Review Fixes - Comprehensive Design

> Design document for addressing findings from comprehensive 7-agent code review
> Date: 2026-02-20
> Scope: 11 validated items (3 critical, 8 important) across 4 domains

## Summary

Following a comprehensive 7-agent code review, 47 findings were initially identified.
After sub-agent validation, 30 false positives were removed, leaving **11 actionable items**.

**Sequencing**: Tests → Backend → Frontend → Infrastructure

---

## Domain 1: Tests (4 items)

### 1.1 Create `tests/test_exception_utils.py`

**Priority**: HIGH
**Effort**: Low

Test the new `validation_error_handler` that converts Pydantic 422 → 400:

```python
# Test cases needed:
- test_create_exception_handlers_returns_dict
- test_validation_error_handler_returns_400
- test_validation_error_handler_logs_warning
- test_handle_file_operation_error_file_not_found
```

### 1.2 Add health simulate tests to `tests/test_api_integration.py`

**Priority**: MEDIUM
**Effort**: Low

Test the new `simulate` query parameter on `/health`:

```python
# Test cases needed:
- test_health_simulate_unavailable_returns_503
- test_health_simulate_degraded_returns_degraded_status
```

### 1.3 Create `tests/test_feature_flags.py`

**Priority**: HIGH
**Effort**: Low

Test `FeatureFlags` save/load operations:

```python
# Test cases needed:
- test_parse_bool_true_values
- test_parse_bool_false_values
- test_feature_flags_defaults
- test_feature_flags_save_success
- test_feature_flags_load_missing_file_returns_defaults
- test_feature_flags_load_json_decode_error_reraises
```

### 1.4 Add edge cases to `tests/test_request_id_middleware.py`

**Priority**: LOW
**Effort**: Low

Add missing edge case tests:

```python
# Test cases needed:
- test_request_id_is_8_characters
- test_request_id_propagates_to_downstream
- test_empty_string_request_id_is_replaced
- test_multiple_requests_have_unique_ids
```

---

## Domain 2: Backend (3 items)

### 2.1 Add asyncio.Lock for race condition

**File**: `api/prompt_improver_api.py`
**Lines**: 253-278
**Priority**: CRITICAL

The global `_strategy_selector` dict is accessed without locking in async context.
Multiple concurrent requests could race to initialize selectors.

**Fix**:
```python
_strategy_selector_lock = asyncio.Lock()

async def get_strategy_selector(settings: Settings, use_nlac: bool = False) -> StrategySelector:
    selector_key = "nlac" if use_nlac else "legacy"
    async with _strategy_selector_lock:
        if selector_key not in _strategy_selector:
            # ... create selector
    return _strategy_selector[selector_key]
```

### 2.2 Add RuntimeError to metrics init exception handling

**File**: `api/main.py`
**Line**: 100
**Priority**: IMPORTANT

`SQLiteMetricsRepository.initialize()` could raise `RuntimeError` (e.g., schema validation failure).

**Fix**:
```python
except (ConnectionError, OSError, RuntimeError) as e:
    logger.warning(f"Failed to initialize metrics repository: {type(e).__name__}: {e}")
```

### 2.3 Add production env check for health simulate

**File**: `api/main.py`
**Lines**: 148-154
**Priority**: IMPORTANT

The `simulate` parameter could be abused in production to fake unhealthy status.

**Fix**:
```python
@app.get("/health")
async def health_check(
    simulate: HealthState = Query(default=HealthState.HEALTHY, ...)
):
    if simulate != HealthState.HEALTHY and os.getenv("ENVIRONMENT") == "production":
        raise HTTPException(status_code=403, detail="Simulation not allowed in production")
    # ... rest of handler
```

---

## Domain 3: Frontend (3 items)

### 3.1 Extract toPercentage helper + add clamping

**File**: `dashboard/src/core/design/typography.ts`
**Lines**: 17-21, 35-39
**Priority**: IMPORTANT

Confidence score conversion (`score * 100`) is duplicated in both `confidence()` and `confidenceIcon()`.
Also lacks input validation - values >1 produce confusing output.

**Fix**:
```typescript
private static toPercentage(score: number): number {
  // Clamp to 0-1 range, then convert to percentage
  const clamped = Math.max(0, Math.min(1, score));
  return Math.round(clamped * 100);
}

static confidence(score: number): string {
  const rounded = Typography.toPercentage(score);
  // ... rest of implementation
}
```

### 3.2 Extract CopyStartCommandAction component

**File**: `dashboard/src/core/errors/handlers.tsx`
**Lines**: 16-22, 42-48, 81-87
**Priority**: IMPORTANT

"Copy Start Command" action is duplicated 3 times across error handlers.

**Fix**:
```typescript
const CopyStartCommandAction = () => (
  <Action
    title="Copy Start Command"
    onAction={async () => {
      await Clipboard.copy(BACKEND_START_COMMAND);
      await showHUD("✓ Command copied! Paste in terminal");
    }}
  />
);
```

### 3.3 Add .tmp cleanup function

**File**: `dashboard/src/core/promptStorage.ts`
**Lines**: 139-142
**Priority**: IMPORTANT

Atomic write creates `.tmp` files. If process crashes before rename, orphaned files accumulate.

**Fix**:
```typescript
async function cleanupOrphanedTempFiles(): Promise<void> {
  try {
    const files = await fs.readdir(STORAGE_DIR);
    for (const file of files) {
      if (file.endsWith('.tmp')) {
        const filePath = join(STORAGE_DIR, file);
        const stat = await fs.stat(filePath);
        // Remove files older than 1 hour
        if (Date.now() - stat.mtimeMs > 3600000) {
          await fs.unlink(filePath);
        }
      }
    }
  } catch (error) {
    if (!isENOENT(error)) console.warn(`${LOG_PREFIX} Failed to cleanup temp files:`, error);
  }
}

// Call at module load or in ensureStorageDir()
```

---

## Domain 4: Infrastructure (1 item - optional)

### 4.1 Extract port check helper in Makefile

**File**: `Makefile`
**Priority**: LOW (optional)

Port checking logic with `lsof` is duplicated in `dev` and `status` targets.

**Fix**: Extract to helper variable or target (deferred - low priority cleanup).

---

## Validation Summary

| Metric | Original | After Validation |
|--------|----------|------------------|
| Total findings | 47 | 11 |
| Critical | 3 | 2 |
| Important | 17 | 6 |
| Suggestions | 27+ | 3 |

**False positives removed**: 30 items (already handled, not recommended, or adequate)

---

## Next Steps

1. Create implementation plan via `writing-plans` skill
2. Execute in domain order: Tests → Backend → Frontend → Infrastructure
3. One PR per domain for easier review
