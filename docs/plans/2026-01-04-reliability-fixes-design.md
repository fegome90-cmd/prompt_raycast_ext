# Reliability Fixes - Design Document

**Date:** 2026-01-04
**Source:** Multi-agent PR review (41 issues identified)
**Scope:** 5 critical reliability fixes
**Approach:** Hybrid (group by category)

---

## Overview

This design addresses 5 critical reliability issues identified by multi-agent code review that are causing:
- **500 errors** when LLM returns unexpected framework names
- **Memory leaks** from unclosed SQLite connections
- **Silent failures** from circuit breaker paradox
- **App crashes** when using Anthropic provider

**Attack Strategy:** Hybrid approach - group fixes by category (SQLite first, then API) for focused testing and easier rollback.

---

## Phase 1: SQLite Fixes (2 issues)

### Fix 1: Connection Leak on Init Failure

**File:** `hemdov/infrastructure/persistence/sqlite_prompt_repository.py:34-42`

**Problem:** If `__init__` fails after creating connection object but before configuration completes, the connection is never closed, causing memory leak.

**Solution:**
```python
async def __init__(self, db_path: str):
    self.db_path = Path(db_path)
    self._connection = None
    try:
        self._connection = await aiosqlite.connect(self.db_path)
        await self._configure_connection(self._connection)
    except Exception:
        if self._connection:
            await self._connection.close()
        self._connection = None
        raise
```

**Error Handling:** Log error, close connection, re-raise for API to fail correctly

---

### Fix 2: JSON Deserialization Error

**File:** `hemdov/infrastructure/persistence/sqlite_prompt_repository.py:220`

**Problem:** `json.loads()` can fail if data is corrupted, currently no error handling.

**Solution:**
```python
try:
    guardrails = json.loads(row["guardrails"])
except (json.JSONDecodeError, TypeError) as e:
    logger.error(f"Corrupted guardrails in record {row['id']}: {e}")
    guardrails = []
```

**Error Handling:** Log warning, use empty array as fallback, continue operating

---

## Phase 1: Basic Tests

### Test 1: Connection Leak Prevention

**File:** `tests/test_sqlite_repository.py` (new)

```python
@pytest.mark.asyncio
async def test_init_closes_connection_on_failure():
    """Test that failed init doesn't leak connections."""
    repo = SQLitePromptRepository("/invalid/path/nonexistent.db")
    with pytest.raises(Exception):
        await repo.initialize()
    assert repo._connection is None
```

---

### Test 2: JSON Error Handling

**File:** `tests/test_sqlite_repository.py`

```python
@pytest.mark.asyncio
async def test_handles_corrupted_guardrails():
    """Test that corrupted JSON is handled gracefully."""
    repo = await SQLitePromptRepository(db_path=":memory:")
    await repo._connection.execute(
        "INSERT INTO prompt_history (guardrails) VALUES (?)",
        ("{invalid json",)
    )
    history = await repo.get_all(limit=10)
    assert isinstance(history, list)
```

---

## Phase 2: API Fixes (3 issues)

### Fix 3: Framework Validation with Fallback

**File:** `hemdov/domain/entities/prompt_history.py:56-63`

**Problem:** Strict validation causes 500 errors when LLM returns descriptive framework name instead of enum value.

**Solution:**
```python
def __post_init__(self):
    allowed_frameworks = {
        "chain-of-thought",
        "tree-of-thoughts",
        "decomposition",
        "role-playing"
    }
    if self.framework not in allowed_frameworks:
        logger.warning(f"Unknown framework '{self.framework}', defaulting to 'chain-of-thought'")
        object.__setattr__(self, 'framework', 'chain-of-thought')
```

**Error Handling:** Log warning, default to "chain-of-thought", continue

---

### Fix 4: Circuit Breaker Paradox

**File:** `api/prompt_improver_api.py:252-259`

**Problem:** `record_success()` inside try-except means if recording fails, the entire request is marked as failed.

**Solution:**
```python
try:
    # ... request processing ...
except Exception as e:
    logger.error(f"Request failed: {e}")
    await _circuit_breaker.record_failure()
    raise
finally:
    # Record success OUTSIDE try-except
    if response.status_code == 200:
        await _circuit_breaker.record_success()
```

**Error Handling:** Separate failure/success recording paths

---

### Fix 5: Anthropic Handler Missing

**File:** `main.py:71-89`

**Problem:** Anthropic adapter exists but not registered in lifespan, app crashes with `LLM_PROVIDER=anthropic`.

**Solution:**
```python
elif provider == "anthropic":
    lm = create_anthropic_adapter(
        model=settings.LLM_MODEL,
        api_key=settings.ANTHROPIC_API_KEY or settings.HEMDOV_ANTHROPIC_API_KEY,
        temperature=temp,
    )
```

**Error Handling:** If no API key, fallback to DeepSeek

---

## Phase 2: Basic Tests

### Test 3: Framework Fallback

**File:** `tests/test_prompt_history.py` (new)

```python
def test_validation_invalid_framework_fallback():
    """Test that invalid framework defaults to chain-of-thought."""
    history = PromptHistory(
        idea="test",
        improved_prompt="test",
        framework="Invalid Framework Name",
        guardrails=["test"]
    )
    assert history.framework == "chain-of-thought"
```

---

### Test 4: Circuit Breaker Success Recording

**File:** `tests/test_circuit_breaker.py` (new)

```python
@pytest.mark.asyncio
async def test_circuit_breaker_records_success_outside_try():
    """Test that success is recorded even when request succeeds."""
    async with mock_circuit_breaker() as breaker:
        response = Mock(status_code=200)
        assert breaker.success_count == 1
```

---

### Test 5: Anthropic Provider Initialization

**File:** `tests/test_anthropic_provider.py` (new)

```python
@pytest.mark.asyncio
async def test_anthropic_provider_initializes():
    """Test that Anthropic provider can be initialized."""
    from main import create_anthropic_adapter
    if not os.getenv("HEMDOV_ANTHROPIC_API_KEY"):
        pytest.skip("No Anthropic API key")
    lm = create_anthropic_adapter(
        model="claude-haiku-4-5-20251001",
        api_key=os.getenv("HEMDOV_ANTHROPIC_API_KEY", ""),
        temperature=0.0
    )
    assert lm is not None
```

---

## Error Handling Patterns

| Fix | Pattern | Rationale |
|-----|---------|-----------|
| Connection leak | Log + close + re-raise | Fatal error (cannot continue without DB) |
| JSON deserialization | Log + fallback `[]` | Recoverable (empty guardrails is safe) |
| Framework validation | Log + fallback to default | Recoverable (default framework is safe) |
| Circuit breaker | Separate paths | Success/failure are independent operations |
| Anthropic handler | Log + fallback to DeepSeek | Recoverable (use primary provider) |

---

## Commit Strategy

**One commit per fix** (fine-grained for surgical rollback):

```bash
# Phase 1 - SQLite
git commit -m "fix(sqlite): prevent connection leak on init failure"
git commit -m "fix(sqlite): handle corrupted guardrails JSON gracefully"

# Phase 2 - API
git commit -m "fix(validation): fallback to default framework on invalid value"
git commit -m "fix(circuit-breaker): move record_success outside try-except"
git commit -m "feat(anthropic): add Anthropic provider handler"
```

**Rollback Plan:**
- Each commit is independent
- Revert individually: `git revert <sha>`
- Tests validate no regression

---

## Validation Strategy

**Per Phase:**

- **Phase 1**: Run SQLite tests + verify no memory leaks (check open connections)
- **Phase 2**: Run API tests + make real request to `/api/v1/improve-prompt`

**Success Criteria:**
- All tests pass
- No 500 errors from framework validation
- No connection leaks in logs
- Anthropic provider initializes correctly
- Circuit breaker records success/failure independently

---

## Risk Assessment

| Risk | Mitigation |
|------|------------|
| Break existing prompts | Tests validate basic functionality |
| Framework default too generic | "chain-of-thought" is safest option |
| Connection close fails | Try-except around close, ignore errors |
| Anthropic key missing | Fallback to DeepSeek |
| Circuit breaker state corruption | Separate recording paths |

---

## Next Steps

1. ✅ Design approved
2. ⏳ Create detailed implementation plan (superpowers:writing-plans)
3. ⏳ Execute using subagent-driven development
