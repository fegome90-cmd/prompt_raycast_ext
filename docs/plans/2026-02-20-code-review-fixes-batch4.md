# Code Review Fixes - Batch 4

> Post-review fixes for mr-quick findings

**Goal:** Fix all HIGH+CRITICAL issues identified in code review before commit.

---

## CRITICAL Issues

### Task 1: Fix Inconsistent Confidence Thresholds

**File:** `dashboard/src/core/design/typography.ts`
**Confidence:** 95%

**Issue:**
```typescript
// confidence() uses:
if (rounded >= 80) return `◉ ${rounded}%`;  // HIGH
if (rounded >= 60) return `◎ ${rounded}%`;  // MEDIUM

// confidenceIcon() uses:
if (rounded >= 70) return "◉";  // HIGH - DIFFERENT!
```

**Fix:** Extract shared thresholds:
```typescript
// Module-level constants
const CONFIDENCE = {
  HIGH_THRESHOLD: 80,
  MEDIUM_THRESHOLD: 60,
  LOW_THRESHOLD: 40,
  ICON_HIGH_THRESHOLD: 70,  // Different for icons - document why
} as const;
```

Or unify thresholds if they should be the same.

**Tests to update:** `typography.test.ts` - verify consistency

---

## HIGH Issues

### Task 2: Add Test for Default Environment

**File:** `tests/test_api_integration.py`
**Confidence:** 85%

**Add test:**
```python
def test_health_simulate_allowed_when_environment_unset(self, client, monkeypatch):
    """Simulate parameter should be allowed when ENVIRONMENT is not set."""
    monkeypatch.delenv("ENVIRONMENT", raising=False)

    response = client.get("/health?simulate=unavailable")

    assert response.status_code == 503  # Simulation works
```

---

### Task 3: Fix Race Condition in Temp File Cleanup

**File:** `dashboard/src/core/promptStorage.ts`
**Confidence:** 75%

**Current issue:** Cleanup runs during `ensureStorageDir()` which is called by multiple operations.

**Fix options:**
1. Use unique temp file names with timestamp prefix
2. Skip files newer than 5 minutes (grace period)
3. Only cleanup on explicit command, not on every operation

**Recommended:** Add grace period:
```typescript
const GRACE_PERIOD_MS = 300000; // 5 minutes

// Only remove files older than grace period
if (Date.now() - stat.mtimeMs > GRACE_PERIOD_MS) {
  await fs.unlink(filePath);
}
```

---

## MEDIUM Issues

### Task 4: Extract Duplicate Symbols Constant

**File:** `dashboard/src/core/design/typography.ts`

**Fix:**
```typescript
const COUNT_SYMBOLS: Record<string, string> = {
  Questions: "?",
  Assumptions: "◐",
  Characters: "#",
  Words: "¶",
} as const;
```

---

### Task 5: Move ONE_HOUR_MS to Module Level

**File:** `dashboard/src/core/promptStorage.ts`

**Fix:**
```typescript
const MAX_HISTORY = 20;
const TEMP_FILE_MAX_AGE_MS = 3600000; // 1 hour
```

---

## Execution Order

1. Task 1 (Critical - thresholds)
2. Task 2 (High - test)
3. Task 3 (High - race condition)
4. Task 4 (Medium - symbols)
5. Task 5 (Medium - constant)

---

## Commit Plan

```bash
# After all fixes
git add -A
git commit -m "fix: address code review findings - thresholds, tests, cleanup safety"
```
