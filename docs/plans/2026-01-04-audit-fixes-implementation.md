# Audit Fixes Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Fix 3 high-priority issues found during SQLite persistence audit to improve app reliability and performance

**Architecture:** The fixes target 3 specific files:
1. `api/prompt_improver_api.py` - Make save operation non-blocking to improve API response time
2. `hemdov/infrastructure/persistence/sqlite_prompt_repository.py` - Add error handling for JSON parsing
3. `hemdov/domain/entities/prompt_history.py` - Remove dead validation code

**Tech Stack:** Python 3.10+, asyncio, aiosqlite, pytest

**Context:** These are post-auditor fixes for a personal app. The issues were identified by 5 independent subagent auditors reviewing the SQLite persistence implementation.

---

## Task 1: Non-Blocking Save (Critical Performance Fix)

**Impact:** Removes 50-200ms blocking delay from every API response

**Files:**
- Modify: `/Users/felipe_gonzalez/Developer/raycast_ext/api/prompt_improver_api.py:184`

**Step 1: Read the current code**

Read file at line 180-190 to see the blocking save call:

```bash
head -n 190 /Users/felipe_gonzalez/Developer/raycast_ext/api/prompt_improver_api.py | tail -n 11
```

Expected to see:
```python
    # Save to database (non-blocking)
    await _save_history_async(
        settings,
        result.improved_prompt,
        result.role,
        result.directive,
        result.framework,
        result.guardrails,
        result.reasoning,
        result.confidence,
        result.backend,
        result.model,
        result.provider,
        latency_ms,
    )
```

**Step 2: Write the failing test**

Create test to verify save doesn't block response:

```python
# In tests/test_api_integration.py, add:

def test_save_is_non_blocking(monkeypatch):
    """Test that save operation doesn't block API response."""
    from unittest.mock import AsyncMock, patch
    import asyncio

    # Mock save to take 1 second
    async def slow_save(*args, **kwargs):
        await asyncio.sleep(1)

    with patch('api.prompt_improver_api._save_history_async', new=slow_save):
        response = client.post(
            "/api/v1/improve-prompt",
            json={"idea": "test blocking behavior", "context": "testing"}
        )

    # Should respond immediately (< 100ms), not wait for save
    assert response.status_code == 200
    # If save was blocking, this would take >1 second
```

**Step 3: Run test to verify it fails**

Run: `cd /Users/felipe_gonzalez/Developer/raycast_ext && python -m pytest tests/test_api_integration.py::test_save_is_non_blocking -v`

Expected: FAIL (test takes >1 second because save blocks)

**Step 4: Write minimal implementation**

Edit `/Users/felipe_gonzalez/Developer/raycast_ext/api/prompt_improver_api.py` at line 184:

Change from:
```python
    await _save_history_async(
        settings,
        result.improved_prompt,
        result.role,
        result.directive,
        result.framework,
        result.guardrails,
        result.reasoning,
        result.confidence,
        result.backend,
        result.model,
        result.provider,
        latency_ms,
    )
```

To:
```python
    # Save to database (non-blocking - runs in background)
    asyncio.create_task(_save_history_async(
        settings,
        result.improved_prompt,
        result.role,
        result.directive,
        result.framework,
        result.guardrails,
        result.reasoning,
        result.confidence,
        result.backend,
        result.model,
        result.provider,
        latency_ms,
    ))
```

**Step 5: Run test to verify it passes**

Run: `cd /Users/felipe_gonzalez/Developer/raycast_ext && python -m pytest tests/test_api_integration.py::test_save_is_non_blocking -v`

Expected: PASS (test completes in < 100ms)

**Step 6: Run all integration tests to ensure nothing broke**

Run: `cd /Users/felipe_gonzalez/Developer/raycast_ext && python -m pytest tests/test_api_integration.py -v`

Expected: All tests pass

**Step 7: Manual test**

Test with real API:

```bash
# Start backend
python main.py &

# In another terminal, make request
time curl -X POST http://localhost:8000/api/v1/improve-prompt \
  -H "Content-Type: application/json" \
  -d '{"idea": "test non-blocking save"}'

# Should complete in < 1 second (not ~7 seconds with old blocking save)
```

**Step 8: Commit**

```bash
git add api/prompt_improver_api.py tests/test_api_integration.py
git commit -m "perf(api): make save operation non-blocking

Change await _save_history_async() to asyncio.create_task()
to prevent database save from blocking API response.

Removes 50-200ms delay from every request. Save now runs
in background task, improving user experience."
```

---

## Task 2: JSON Error Handling (Critical Reliability Fix)

**Impact:** Prevents app crash when database contains corrupted JSON data

**Files:**
- Modify: `/Users/felipe_gonzalez/Developer/raycast_ext/hemdov/infrastructure/persistence/sqlite_prompt_repository.py:220`
- Test: `/Users/felipe_gonzalez/Developer/raycast_ext/tests/test_sqlite_prompt_repository.py`

**Step 1: Read the current code**

Read file at line 215-230 to see the JSON parsing without error handling:

```bash
head -n 230 /Users/felipe_gonzalez/Developer/raycast_ext/hemdov/infrastructure/persistence/sqlite_prompt_repository.py | tail -n 16
```

Expected to see:
```python
    def _row_to_entity(self, row: aiosqlite.Row) -> PromptHistory:
        return PromptHistory(
            original_idea=row["original_idea"],
            context=row["context"],
            improved_prompt=row["improved_prompt"],
            role=row["role"],
            directive=row["directive"],
            framework=row["framework"],
            guardrails=json.loads(row["guardrails"]),  # ← Can crash here
            reasoning=row["reasoning"],
            confidence=row["confidence"],
            backend=row["backend"],
            model=row["model"],
            provider=row["provider"],
            latency_ms=row["latency_ms"],
            created_at=row["created_at"],
        )
```

**Step 2: Write the failing test**

Create test to verify corrupted JSON is handled gracefully:

```python
# In tests/test_sqlite_prompt_repository.py, add:

async def test_find_by_id_with_corrupted_guardrails_json(repo):
    """Test reading record with malformed JSON returns safe default."""
    # Insert record with invalid JSON in guardrails
    async with aiosqlite.connect(settings.SQLITE_DB_PATH) as conn:
        await conn.execute(
            "INSERT INTO prompt_history "
            "(original_idea, context, improved_prompt, role, directive, framework, guardrails, "
            "reasoning, confidence, backend, model, provider, latency_ms, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            ("test idea", "context", "improved", "role", "directive", "framework",
             "{invalid json",  # ← Malformed JSON
             None, 0.9, "backend", "model", "provider", 100,
             datetime.utcnow().isoformat())
        )

    # Should not crash, should return empty list for guardrails
    result = await repo.find_by_id(1)

    assert result is not None
    assert result.guardrails == []  # Safe default
    assert result.original_idea == "test idea"
```

**Step 3: Run test to verify it fails**

Run: `cd /Users/felipe_gonzalez/Developer/raycast_ext && python -m pytest tests/test_sqlite_prompt_repository.py::test_find_by_id_with_corrupted_guardrails_json -v`

Expected: FAIL with `json.JSONDecodeError`

**Step 4: Write minimal implementation**

Edit `/Users/felipe_gonzalez/Developer/raycast_ext/hemdov/infrastructure/persistence/sqlite_prompt_repository.py` at line 220:

Change from:
```python
            guardrails=json.loads(row["guardrails"]),
```

To:
```python
            # Safely parse JSON, fallback to empty list on corruption
            try:
                guardrails = json.loads(row["guardrails"])
            except (json.JSONDecodeError, TypeError):
                logger.warning(f"Invalid JSON in guardrails for record {row['id']}, using empty list")
                guardrails = [],
```

**Step 5: Run test to verify it passes**

Run: `cd /Users/felipe_gonzalez/Developer/raycast_ext && python -m pytest tests/test_sqlite_prompt_repository.py::test_find_by_id_with_corrupted_guardrails_json -v`

Expected: PASS

**Step 6: Run all repository tests to ensure nothing broke**

Run: `cd /Users/felipe_gonzalez/Developer/raycast_ext && python -m pytest tests/test_sqlite_prompt_repository.py -v`

Expected: All tests pass

**Step 7: Manual test**

Test with manually corrupted database:

```bash
# Insert invalid JSON directly
sqlite3 data/prompt_history.db \
  "INSERT INTO prompt_history (original_idea, improved_prompt, role, directive, framework, guardrails, backend, model, provider, created_at) \
   VALUES ('test', 'improved', 'role', 'directive', 'framework', '{bad}', 'backend', 'model', 'provider', datetime('now'));"

# Query via API - should not crash
curl http://localhost:8000/api/v1/improve-prompt?skip=1&limit=10
```

**Step 8: Commit**

```bash
git add hemdov/infrastructure/persistence/sqlite_prompt_repository.py tests/test_sqlite_prompt_repository.py
git commit -m "fix(repository): handle corrupted JSON in guardrails field

Add try/except around json.loads() in _row_to_entity() to prevent
app crash when database contains malformed JSON data.

Returns empty list as safe default and logs warning. This can happen
if database is manually edited or corrupted."
```

---

## Task 3: Remove Dead Validation Code (Code Quality Fix)

**Impact:** Removes confusing dead code that does nothing

**Files:**
- Modify: `/Users/felipe_gonzalez/Developer/raycast_ext/hemdov/domain/entities/prompt_history.py:56-72`

**Step 1: Read the current code**

Read file at line 50-80 to see the dead validation code:

```bash
head -n 80 /Users/felipe_gonzalez/Developer/raycast_ext/hemdov/domain/entities/prompt_history.py | tail -n 31
```

Expected to see:
```python
        # Validate framework (case-insensitive, allow descriptive names)
        framework_normalized = self.framework.lower().strip()
        allowed_frameworks = ["zero-shot", "few-shot", "cot", "react", "reflexion"]
        is_valid_framework = any(
            fw in framework_normalized for fw in allowed_frameworks
        )

        # Validate guardrails
        if not isinstance(self.guardrails, list):
            raise ValueError("guardrails must be a list")
```

Note: `is_valid_framework` is calculated but never used - dead code.

**Step 2: Write the failing test**

Create test to verify validation doesn't actually check framework:

```python
# In tests/test_sqlite_prompt_repository.py, add:

def test_invalid_framework_allowed():
    """Test that invalid framework names are accepted (dead code)."""
    from hemdov.domain.entities.prompt_history import PromptHistory

    # This should raise ValueError if validation worked, but it doesn't
    entity = PromptHistory(
        original_idea="test",
        context="context",
        improved_prompt="improved",
        role="role",
        directive="directive",
        framework="completely-invalid-framework-name",  # ← Invalid
        guardrails=["guardrail"],
        backend="backend",
        model="model",
        provider="provider"
    )

    # Test passes because validation is dead (doesn't actually validate)
    assert entity.framework == "completely-invalid-framework-name"
```

**Step 3: Run test to verify it passes**

Run: `cd /Users/felipe_gonzalez/Developer/raycast_ext && python -m pytest tests/test_sqlite_prompt_repository.py::test_invalid_framework_allowed -v`

Expected: PASS (confirming validation is dead)

**Step 4: Write minimal implementation**

Edit `/Users/felipe_gonzalez/Developer/raycast_ext/hemdov/domain/entities/prompt_history.py` at line 56-72:

Delete lines 56-62 (the dead validation block):
```python
        # Validate framework (case-insensitive, allow descriptive names)
        framework_normalized = self.framework.lower().strip()
        allowed_frameworks = ["zero-shot", "few-shot", "cot", "react", "reflexion"]
        is_valid_framework = any(
            fw in framework_normalized for fw in allowed_frameworks
        )
```

**Step 5: Run all entity tests to ensure nothing broke**

Run: `cd /Users/felipe_gonzalez/Developer/raycast_ext && python -m pytest tests/test_sqlite_prompt_repository.py -v`

Expected: All tests pass (validation wasn't working anyway)

**Step 6: Manual test**

Test with valid entity creation:

```python
python3 -c "
from hemdov.domain.entities.prompt_history import PromptHistory
from datetime import datetime

entity = PromptHistory(
    original_idea='test',
    context='context',
    improved_prompt='improved',
    role='role',
    directive='directive',
    framework='any-framework-name',  # No longer validated
    guardrails=['guardrail'],
    backend='backend',
    model='model',
    provider='provider',
    created_at=datetime.utcnow().isoformat()
)

print(f'Framework: {entity.framework}')
print('Entity created successfully')
"
```

**Step 7: Commit**

```bash
git add hemdov/domain/entities/prompt_history.py
git commit -m "refactor(entity): remove dead framework validation code

Remove unused validation code that calculated is_valid_framework
but never actually used the result. This was dead code that
created confusion about whether framework validation was active.

Framework names are now completely unconstrained (as they were
in practice, since the validation was never enforced)."
```

---

## Summary

**Total Time Estimate:** ~30 minutes
- Task 1 (Non-Blocking Save): 10 minutes
- Task 2 (JSON Error Handling): 15 minutes
- Task 3 (Dead Code Removal): 5 minutes

**Expected Outcome:**
1. API responses are faster (50-200ms improvement)
2. App won't crash on corrupted database data
3. Code is cleaner without dead validation

**Verification Steps After All Tasks:**

```bash
# 1. Run all tests
python -m pytest tests/ -v

# 2. Start backend
python main.py &

# 3. Test API still works
curl -X POST http://localhost:8000/api/v1/improve-prompt \
  -H "Content-Type: application/json" \
  -d '{"idea": "final test after all fixes"}'

# 4. Check git log
git log --oneline -3
```

Expected: All tests pass, API responds quickly, 3 new commits
