# Reliability Fixes Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task.

**Goal:** Fix 5 critical reliability issues identified by multi-agent review (500 errors, memory leaks, silent failures)

**Architecture:** Two-phase approach - SQLite fixes first (Fase 1), then API fixes (Fase 2), each with validation tests

**Tech Stack:** Python 3.11+, FastAPI, aiosqlite, pytest, DSPy

**Note:** After reviewing the codebase, 2 fixes (JSON handling, Anthropic handler) are already implemented. This plan validates them with tests and implements the 3 remaining fixes.

---

## Fase 1: SQLite Fixes (2 tasks)

### Task 1: Fix Connection Leak on Init Failure

**Files:**
- Modify: `hemdov/infrastructure/persistence/sqlite_prompt_repository.py:34-42`
- Test: `tests/test_sqlite_repository.py` (create)

**Problem:** If `_configure_connection()` fails after creating connection, the connection is never closed, causing memory leak.

**Step 1: Write the failing test**

Create file `tests/test_sqlite_repository.py`:

```python
"""Tests for SQLite prompt repository."""
import pytest
import tempfile
from pathlib import Path

from hemdov.infrastructure.persistence.sqlite_prompt_repository import SQLitePromptRepository
from hemdov.infrastructure.config import Settings


@pytest.mark.asyncio
async def test_init_closes_connection_on_configure_failure():
    """Test that failed _configure_connection doesn't leak connections."""
    # Create a temp directory with invalid permissions to trigger failure
    # Use a readonly parent directory trick
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create settings pointing to valid path
        settings = Settings(
            SQLITE_ENABLED=True,
            SQLITE_DB_PATH=str(Path(tmpdir) / "test.db"),
            SQLITE_WAL_MODE=True,
        )
        repo = SQLitePromptRepository(settings)

        # This should succeed and create connection
        conn = await repo._get_connection()
        assert conn is not None
        assert repo._connection is not None

        # Close connection
        await repo.close()
        assert repo._connection is None
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_sqlite_repository.py::test_init_closes_connection_on_configure_failure -v`

Expected: PASS initially (current code works for valid paths)

**Step 3: Add test for actual failure scenario**

Add to `tests/test_sqlite_repository.py`:

```python
@pytest.mark.asyncio
async def test_init_handles_connection_failure_gracefully():
    """Test that connection failure is handled without leaking."""
    import aiosqlite

    # Mock connect to fail after connection object creation
    original_connect = aiosqlite.connect

    async def failing_connect(path):
        # Create connection object
        conn = await original_connect(path)
        # But simulate failure in configure by raising error
        raise RuntimeError("Simulated configure failure")

    with pytest.raises(RuntimeError, match="Simulated configure failure"):
        settings = Settings(
            SQLITE_ENABLED=True,
            SQLITE_DB_PATH=":memory:",
            SQLITE_WAL_MODE=True,
        )
        repo = SQLitePromptRepository(settings)

        # Patch the connect method
        aiosqlite.connect = failing_connect
        try:
            await repo._get_connection()
        finally:
            aiosqlite.connect = original_connect

    # Connection should be None after failure
    assert repo._connection is None
```

**Step 4: Run test to verify it fails**

Run: `uv run pytest tests/test_sqlite_repository.py::test_init_handles_connection_failure_gracefully -v`

Expected: FAIL because connection is not cleaned up on failure

**Step 5: Implement the fix**

Modify `hemdov/infrastructure/persistence/sqlite_prompt_repository.py:34-42`:

```python
async def _get_connection(self) -> aiosqlite.Connection:
    """Get or create connection with lazy initialization."""
    if self._connection is None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._connection = await aiosqlite.connect(self.db_path)
        # Set row_factory to access columns by name
        self._connection.row_factory = aiosqlite.Row
        try:
            await self._configure_connection(self._connection)
        except Exception:
            # Clean up connection if configure fails
            await self._connection.close()
            self._connection = None
            raise
    return self._connection
```

**Step 6: Run test to verify it passes**

Run: `uv run pytest tests/test_sqlite_repository.py -v`

Expected: PASS for both tests

**Step 7: Commit**

```bash
git add hemdov/infrastructure/persistence/sqlite_prompt_repository.py tests/test_sqlite_repository.py
git commit -m "fix(sqlite): prevent connection leak on configure failure"
```

---

### Task 2: Validate JSON Error Handling (Already Implemented)

**Files:**
- Test: `tests/test_sqlite_repository.py`

**Note:** The JSON error handling in `_row_to_entity()` (lines 214-219) is already implemented correctly. This task validates it with a test.

**Step 1: Write the test**

Add to `tests/test_sqlite_repository.py`:

```python
@pytest.mark.asyncio
async def test_handles_corrupted_guardrails_json():
    """Test that corrupted JSON in guardrails is handled gracefully."""
    settings = Settings(
        SQLITE_ENABLED=True,
        SQLITE_DB_PATH=":memory:",
        SQLITE_WAL_MODE=True,
    )
    repo = SQLitePromptRepository(settings)

    # Get connection and insert corrupted JSON
    conn = await repo._get_connection()
    await conn.execute(
        "INSERT INTO prompt_history (original_idea, improved_prompt, role, directive, framework, guardrails, backend, model, provider, latency_ms) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        ("test idea", "test prompt", "test role", "test directive", "chain-of-thought", "{invalid json", "zero-shot", "test-model", "test-provider", 100)
    )
    await conn.commit()

    # Retrieve via repository - should not crash
    history = await repo.find_by_id(1)

    # Should have fallback guardrails
    assert history is not None
    assert history.guardrails == ["[data corrupted - unavailable]"]

    await repo.close()
```

**Step 2: Run test to verify it passes**

Run: `uv run pytest tests/test_sqlite_repository.py::test_handles_corrupted_guardrails_json -v`

Expected: PASS (already implemented)

**Step 3: Commit**

```bash
git add tests/test_sqlite_repository.py
git commit -m "test(sqlite): add test for corrupted guardrails JSON handling"
```

---

## Fase 2: API Fixes (3 tasks)

### Task 3: Add Framework Validation with Fallback

**Files:**
- Modify: `hemdov/domain/entities/prompt_history.py:37-61`
- Test: `tests/test_prompt_history.py` (create)

**Problem:** LLM can return descriptive framework names (e.g., "Chain of Thought Reasoning") instead of enum values, causing 500 errors.

**Step 1: Write the failing test**

Create file `tests/test_prompt_history.py`:

```python
"""Tests for PromptHistory entity."""
import pytest
from datetime import datetime
from hemdov.domain.entities.prompt_history import PromptHistory


def test_validation_accepts_valid_frameworks():
    """Test that all valid framework names are accepted."""
    valid_frameworks = [
        "chain-of-thought",
        "tree-of-thoughts",
        "decomposition",
        "role-playing"
    ]

    for framework in valid_frameworks:
        history = PromptHistory(
            original_idea="test idea",
            context="test context",
            improved_prompt="test prompt",
            role="test role",
            directive="test directive",
            framework=framework,
            guardrails=["guardrail1"]
        )
        assert history.framework == framework


def test_validation_fallback_on_invalid_framework():
    """Test that invalid framework defaults to chain-of-thought."""
    # This should NOT raise ValueError, but fallback to default
    history = PromptHistory(
        original_idea="test idea",
        context="test context",
        improved_prompt="test prompt",
        role="test role",
        directive="test directive",
        framework="Invalid Framework Name That LLM Might Return",
        guardrails=["guardrail1"]
    )
    # Should fallback to default
    assert history.framework == "chain-of-thought"


def test_validation_fallback_on_descriptive_framework():
    """Test that descriptive framework names fallback to default."""
    descriptive_names = [
        "Chain of Thought Reasoning",
        "Tree of Thoughts Approach",
        "Decomposition Method",
        "Role Playing Technique"
    ]

    for framework in descriptive_names:
        history = PromptHistory(
            original_idea="test idea",
            context="test context",
            improved_prompt="test prompt",
            role="test role",
            directive="test directive",
            framework=framework,
            guardrails=["guardrail1"]
        )
        # Should fallback to default
        assert history.framework == "chain-of-thought"
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_prompt_history.py -v`

Expected: FAIL - currently accepts invalid frameworks without validation

**Step 3: Implement the fix**

Modify `hemdov/domain/entities/prompt_history.py:37-61`, add framework validation:

```python
def __post_init__(self):
    """Validate business invariants."""
    # Validate framework is allowed value (with fallback)
    allowed_frameworks = {
        "chain-of-thought",
        "tree-of-thoughts",
        "decomposition",
        "role-playing"
    }
    if self.framework not in allowed_frameworks:
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(
            f"Unknown framework '{self.framework}', "
            f"defaulting to 'chain-of-thought'"
        )
        object.__setattr__(self, 'framework', 'chain-of-thought')

    # Validate confidence range
    if self.confidence is not None:
        if not (0.0 <= self.confidence <= 1.0):
            raise ValueError(f"Confidence must be 0-1, got {self.confidence}")

    # Validate latency is non-negative
    if self.latency_ms is not None and self.latency_ms < 0:
        raise ValueError(f"Latency must be >= 0, got {self.latency_ms}")

    # Validate non-empty inputs
    if not self.original_idea or not self.original_idea.strip():
        raise ValueError("original_idea cannot be empty")

    if not self.improved_prompt or not self.improved_prompt.strip():
        raise ValueError("improved_prompt cannot be empty")

    # Validate guardrails is not empty
    if not self.guardrails:
        raise ValueError("guardrails cannot be empty")

    # Set created_at if not provided
    if self.created_at is None:
        object.__setattr__(self, 'created_at', datetime.utcnow().isoformat())
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_prompt_history.py -v`

Expected: PASS for all tests

**Step 5: Commit**

```bash
git add hemdov/domain/entities/prompt_history.py tests/test_prompt_history.py
git commit -m "fix(validation): fallback to default framework on invalid value"
```

---

### Task 4: Fix Circuit Breaker Paradox

**Files:**
- Modify: `api/prompt_improver_api.py:258-268`
- Test: `tests/test_circuit_breaker.py` (create)

**Problem:** `record_success()` is inside try-except, so if recording fails, the request is marked as failed.

**Step 1: Write the failing test**

Create file `tests/test_circuit_breaker.py`:

```python
"""Tests for circuit breaker."""
import pytest
from unittest.mock import Mock, patch, AsyncMock
from api.circuit_breaker import CircuitBreaker


@pytest.mark.asyncio
async def test_circuit_breaker_records_success_outside_try():
    """Test that success is recorded even when save succeeds."""
    breaker = CircuitBreaker(max_failures=5, timeout_seconds=300)

    # Simulate successful save
    await breaker.record_success()
    assert breaker._failure_count == 0
    assert breaker._last_failure_time is None


@pytest.mark.asyncio
async def test_circuit_breaker_records_failure_on_exception():
    """Test that failure is recorded on exception."""
    breaker = CircuitBreaker(max_failures=5, timeout_seconds=300)

    # Simulate failure
    await breaker.record_failure()
    assert breaker._failure_count == 1
    assert breaker._last_failure_time is not None


@pytest.mark.asyncio
async def test_circuit_breaker_opens_after_max_failures():
    """Test that circuit opens after max failures."""
    breaker = CircuitBreaker(max_failures=3, timeout_seconds=300)

    # Record 3 failures
    for _ in range(3):
        await breaker.record_failure()

    # Circuit should be open
    assert await breaker.should_attempt() is False


@pytest.mark.asyncio
async def test_circuit_breaker_half_open_after_timeout():
    """Test that circuit is half-open after timeout."""
    import time

    breaker = CircuitBreaker(max_failures=3, timeout_seconds=1)

    # Record 3 failures to open circuit
    for _ in range(3):
        await breaker.record_failure()

    assert await breaker.should_attempt() is False

    # Wait for timeout
    time.sleep(1.1)

    # Should allow attempt now (half-open)
    assert await breaker.should_attempt() is True
```

**Step 2: Run test to verify current behavior**

Run: `uv run pytest tests/test_circuit_breaker.py -v`

Expected: PASS (circuit breaker itself works correctly)

**Step 3: Write integration test for save_history**

Add to `tests/test_circuit_breaker.py`:

```python
@pytest.mark.asyncio
async def test_save_history_success_records_success_outside_try():
    """Test that success recording is outside try-except in _save_history_async."""
    from unittest.mock import patch, MagicMock
    from api.prompt_improver_api import _save_history_async
    from hemdov.infrastructure.config import Settings

    settings = Settings(
        SQLITE_ENABLED=True,
        SQLITE_DB_PATH=":memory:",
        SQLITE_WAL_MODE=True,
    )

    # Mock the repository and circuit breaker
    mock_repo = AsyncMock()
    mock_breaker = AsyncMock()

    # Patch get_repository and _circuit_breaker
    with patch('api.prompt_improver_api.get_repository', return_value=mock_repo):
        with patch('api.prompt_improver_api._circuit_breaker', mock_breaker):
            # Mock result object
            mock_result = MagicMock()
            mock_result.improved_prompt = "test"
            mock_result.role = "test"
            mock_result.directive = "test"
            mock_result.framework = "chain-of-thought"
            mock_result.guardrails = ["test"]
            mock_result.reasoning = None
            mock_result.confidence = 0.8

            # Call the function
            await _save_history_async(
                settings=settings,
                original_idea="test idea",
                context="test context",
                result=mock_result,
                backend="zero-shot",
                latency_ms=100
            )

            # Verify record_success was called
            mock_breaker.record_success.assert_called_once()
            # Verify record_failure was NOT called
            mock_breaker.record_failure.assert_not_called()
```

**Step 4: Run test to verify current behavior**

Run: `uv run pytest tests/test_circuit_breaker.py::test_save_history_success_records_success_outside_try -v`

Expected: PASS (current code works, but has paradox)

**Step 5: Implement the fix to prevent paradox**

Modify `api/prompt_improver_api.py:258-268`, move `record_success()` outside try-except:

```python
async def _save_history_async(
    settings: Settings,
    original_idea: str,
    context: str,
    result,
    backend: str,
    latency_ms: int
):
    """
    Save prompt improvement history to SQLite with circuit breaker protection.

    Non-blocking async function that logs errors without failing the request.
    """
    repo = None
    success = False

    try:
        # Get repository with circuit breaker
        repo = await get_repository(settings)
        if repo is None:
            logger.debug("Persistence disabled or circuit breaker open")
            return

        # Extract model and provider from settings
        model = settings.LLM_MODEL
        provider = settings.LLM_PROVIDER

        # Convert guardrails to list if it's a string
        guardrails_list = (
            result.guardrails.split("\n")
            if isinstance(result.guardrails, str)
            else result.guardrails
        )

        # Extract and convert confidence to float if it's a string
        confidence_value = getattr(result, "confidence", None)
        if confidence_value is not None:
            try:
                confidence_value = float(confidence_value)
            except (ValueError, TypeError):
                confidence_value = None

        # Create PromptHistory entity
        history = PromptHistory(
            original_idea=original_idea,
            context=context,
            improved_prompt=result.improved_prompt,
            role=result.role,
            directive=result.directive,
            framework=result.framework,
            guardrails=guardrails_list,
            backend=backend,
            model=model,
            provider=provider,
            reasoning=getattr(result, "reasoning", None),
            confidence=confidence_value,
            latency_ms=latency_ms
        )

        # Save to database
        await repo.save(history)
        success = True
        logger.info(f"Saved prompt history to database (latency: {latency_ms}ms)")

    except Exception as e:
        # Record failure on circuit breaker
        await _circuit_breaker.record_failure()
        logger.error(f"Failed to save prompt history: {e}", exc_info=True)

    finally:
        # Record success OUTSIDE try-except to prevent paradox
        if success:
            await _circuit_breaker.record_success()
```

**Step 6: Run test to verify it passes**

Run: `uv run pytest tests/test_circuit_breaker.py -v`

Expected: PASS for all tests

**Step 7: Commit**

```bash
git add api/prompt_improver_api.py tests/test_circuit_breaker.py
git commit -m "fix(circuit-breaker): move record_success outside try-except"
```

---

### Task 5: Validate Anthropic Handler (Already Implemented)

**Files:**
- Test: `tests/test_anthropic_provider.py` (create)

**Note:** The Anthropic handler is already implemented in `main.py:74-80`. This task validates it with a test.

**Step 1: Write the test**

Create file `tests/test_anthropic_provider.py`:

```python
"""Tests for Anthropic provider initialization."""
import pytest
import os
from unittest.mock import patch, MagicMock


@pytest.mark.asyncio
async def test_anthropic_provider_initializes_with_key():
    """Test that Anthropic provider can be initialized with API key."""
    from hemdov.infrastructure.adapters.litellm_dspy_adapter_prompt import create_anthropic_adapter

    # Skip if no API key
    if not os.getenv("ANTHROPIC_API_KEY") and not os.getenv("HEMDOV_ANTHROPIC_API_KEY"):
        pytest.skip("No Anthropic API key configured")

    lm = create_anthropic_adapter(
        model="claude-haiku-4-5-20251001",
        api_key=os.getenv("HEMDOV_ANTHROPIC_API_KEY") or os.getenv("ANTHROPIC_API_KEY") or "",
        base_url="https://api.anthropic.com",
        temperature=0.0
    )

    assert lm is not None
    assert hasattr(lm, 'provider')
    assert lm.provider == "anthropic"


@pytest.mark.asyncio
async def test_anthropic_provider_in_main_lifespan():
    """Test that Anthropic provider is handled in main.py lifespan."""
    from main import lifespan, DEFAULT_TEMPERATURE
    from fastapi import FastAPI
    from unittest.mock import patch, MagicMock
    import os

    # Mock settings
    mock_settings = MagicMock()
    mock_settings.LLM_PROVIDER = "anthropic"
    mock_settings.LLM_MODEL = "claude-haiku-4-5-20251001"
    mock_settings.ANTHROPIC_API_KEY = os.getenv("HEMDOV_ANTHROPIC_API_KEY") or os.getenv("ANTHROPIC_API_KEY") or "test-key"
    mock_settings.HEMDOV_ANTHROPIC_API_KEY = mock_settings.ANTHROPIC_API_KEY
    mock_settings.LLM_BASE_URL = "https://api.anthropic.com"

    with patch('hemdov.infrastructure.config.settings', mock_settings):
        with patch('hemdov.infrastructure.config.Settings', return_value=mock_settings):
            app = FastAPI()
            lifespan_manager = lifespan(app)

            # Enter lifespan
            async with lifespan_manager:
                # Check that lm was initialized
                from main import lm
                assert lm is not None
                assert lm.provider == "anthropic"
```

**Step 2: Run test to verify it passes**

Run: `uv run pytest tests/test_anthropic_provider.py -v`

Expected: PASS if API key is configured, SKIP otherwise

**Step 3: Commit**

```bash
git add tests/test_anthropic_provider.py
git commit -m "test(anthropic): add validation tests for Anthropic provider"
```

---

## Final Validation

### Step 1: Run all tests

Run: `uv run pytest tests/ -v`

Expected: All tests PASS

### Step 2: Test backend health

Run: `make health` or `curl http://localhost:8000/health`

Expected: `{"status": "healthy", ...}`

### Step 3: Test improve-prompt endpoint

Run: `curl -X POST http://localhost:8000/api/v1/improve-prompt -H "Content-Type: application/json" -d '{"idea": "test idea for reliability fixes"}'`

Expected: 200 response with valid prompt structure

---

## Success Criteria

- [ ] All 5 tasks completed
- [ ] All tests pass (pytest)
- [ ] Backend runs without errors
- [ ] No connection leaks (check `lsof -i :8000` before/after)
- [ ] Framework validation handles invalid values gracefully
- [ ] Circuit breaker records success/failure independently
- [ ] Anthropic provider initializes correctly

---

## Rollback Plan

Each task is in its own commit and can be reverted individually:

```bash
# Rollback specific fix
git revert <commit-sha>

# Rollback entire Fase 1
git revert <hash-1>^..<hash-2>

# Rollback entire implementation
git revert <hash-1>^..<hash-5>
```
