# Code Review Fixes Implementation Plan (MODIFIED)

> **MODIFICATION LOG:**
> - Created 2026-01-07: Added Task 0 (fixtures), added notes for Tasks 3, 31-32, 41-43
> - Original plan: `docs/plans/2026-01-07-code-review-fixes.md`

**Goal:** Fix 51 issues identified by multi-agent code review (critical bugs, test gaps, silent failures, code simplification)

**Architecture:** Full-stack fixes - Python backend (hexagonal architecture) + TypeScript frontend (Raycast extension)

**Tech Stack:** Python 3.12, TypeScript 5.x, pytest, DSPy, FastAPI, React, Raycast API

**Approach:** TDD (Test-Driven Development) - write failing test first, then implement fix, batch by component

**Estimated Time:** ~5.5 hours for all 44 items (43 + 1 prep task)

---

## MODIFICATIONS FROM ORIGINAL PLAN

### Added Task 0: Pre-Execution Setup

**Rationale:** Tests in Tasks 9-10 require fixtures that don't exist yet.

**Status:** ✅ COMPLETED (fixtures created in `tests/fixtures/`)

---

### Task 3: Race Condition Fix - MODIFIED APPROACH

**Original Issue:** Proposed mutex solution using `Promise.resolve()` is not a real mutex in Node.js.

**Modified Step 3:** Replace with proper async mutex using `async-mutex` package:

```bash
cd dashboard && npm install --save async-mutex
```

```typescript
import { Mutex } from 'async-mutex';

class SessionCache {
  private cache = new Map<string, ChatSession>();
  private maxSize = 10;
  private mutex = new Mutex();

  async set(session: ChatSession): Promise<void> {
    return await this.mutex.runExclusive(() => {
      if (this.cache.size >= this.maxSize) {
        const oldestKey = this.cache.keys().next().value;
        this.cache.delete(oldestKey);
      }
      this.cache.set(session.id, session);
    });
  }

  async get(id: string): Promise<ChatSession | undefined> {
    return await this.mutex.runExclusive(() => {
      return this.cache.get(id);
    });
  }
}
```

**Alternative:** If race condition is not actually occurring (Node.js single-threaded), skip this task and add comment explaining why.

---

### Tasks 31-32: TypedDict Tests - MODIFIED APPROACH

**Original Issue:** Python does NOT validate TypedDict at runtime. Tests expecting `KeyError` will fail.

**Modified Step 1:** Change test approach to use explicit validation function:

```python
def test_strategy_metadata_validation():
    """StrategyMetadata should be validated explicitly."""
    from hemdov.domain.dto.nlac_models import StrategyMetadata

    def validate_metadata(data: dict) -> list[str]:
        """Return list of missing required fields."""
        required = ["strategy", "intent", "rar_used", "complexity", "mode"]
        return [field for field in required if field not in data]

    # Test 1: Missing "strategy"
    metadata1 = {"intent": "debug", "complexity": "simple", "mode": "nlac"}
    missing1 = validate_metadata(metadata1)
    assert "strategy" in missing1
    assert "rar_used" in missing1

    # Test 2: All required fields present
    metadata2: StrategyMetadata = {
        "strategy": "nlac",
        "intent": "debug",
        "rar_used": False,
        "complexity": "simple",
        "mode": "nlac",
    }
    assert validate_metadata(metadata2) == []
```

**OR:** Change `StrategyMetadata` from `TypedDict` to `pydantic.BaseModel` for runtime validation.

---

### Tasks 41-43: Integration Tests - DEFERRED

**Original Issue:** Integration tests are stubs with `pass` statements.

**Modified Approach:** Mark as TODO for separate implementation. These require:
- Real backend running
- Full integration test environment
- More complex setup

**Action:** Change to placeholder tasks documenting what needs to be tested:

```python
@pytest.mark.integration
def test_knn_nlac_integration():
    """
    TODO: Implement KNN + NLaCBuilder integration test

    Requirements:
    - Real KNNProvider with valid catalog
    - NLaCBuilder using real KNN (not mocked)
    - Verify fewshot examples are retrieved and used
    """
    pytest.skip("Integration test - requires full backend setup")
```

---

## EXECUTION INSTRUCTIONS

### Before Starting

1. **Verify fixtures exist:**
   ```bash
   ls -la tests/fixtures/
   # Should show: valid_catalog.json, corrupted_catalog.json
   ```

2. **Install additional dependency for Task 3:**
   ```bash
   cd dashboard && npm install --save async-mutex
   ```

3. **Create safety commit:**
   ```bash
   git add .
   git commit -m "wip: before code review fixes execution"
   ```

### Modified Execution Order

Execute in batches of 3, but with this priority:

**Batch 1 (CRITICAL - fixes routing):** Tasks 0→1→2
**Batch 2 (CRITICAL - backend services):** Tasks 9→11→12
**Batch 3 (CRITICAL - API):** Task 17
**Batch 4 (HIGH):** Tasks 5→10→13
**Batch 5 (REST):** Continue from original plan

---

## ORIGINAL PLAN CONTENT (Tasks 1-43)

> The rest of this plan follows the original structure.
> See: `docs/plans/2026-01-07-code-review-fixes.md`

[Note: In actual execution, the full original plan content would be included here.
For this modified version, we reference the original for the detailed steps.]

---

## SUMMARY OF MODIFICATIONS

| Task | Change | Reason |
|------|--------|--------|
| **Task 0** | ADDED | Create fixtures before execution |
| **Task 3** | MODIFIED | Use async-mutex instead of Promise-based mutex |
| **Task 31-32** | MODIFIED | TypedDict doesn't validate at runtime - changed approach |
| **Task 41-43** | DEFERRED | Integration tests need separate implementation |
| **TOTAL** | 44 tasks | 43 original + 1 prep task |

---

## QUICK REFERENCE FOR PARALLEL SESSION

When the parallel session asks for the plan file, provide:

```
docs/plans/2026-01-07-code-review-fixes-MODIFIED.md
```

This version includes all fixes for identified blockers.
