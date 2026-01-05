"""Tests for circuit breaker."""
import pytest
import time
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from api.circuit_breaker import CircuitBreaker


@pytest.mark.asyncio
async def test_circuit_breaker_records_success_outside_try():
    """Test that success is recorded even when save succeeds."""
    breaker = CircuitBreaker(max_failures=5, timeout_seconds=300)

    # Simulate successful save
    await breaker.record_success()
    assert breaker._failure_count == 0
    assert breaker._disabled_until is None


@pytest.mark.asyncio
async def test_circuit_breaker_records_failure_on_exception():
    """Test that failure is recorded on exception."""
    breaker = CircuitBreaker(max_failures=5, timeout_seconds=300)

    # Simulate failure
    await breaker.record_failure()
    assert breaker._failure_count == 1


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
    breaker = CircuitBreaker(max_failures=3, timeout_seconds=1)

    # Record 3 failures to open circuit
    for _ in range(3):
        await breaker.record_failure()

    assert await breaker.should_attempt() is False

    # Wait for timeout
    time.sleep(1.1)

    # Should allow attempt now (half-open)
    assert await breaker.should_attempt() is True


@pytest.mark.asyncio
async def test_save_history_success_records_success_outside_try():
    """Test that success recording is outside try-except in _save_history_async."""
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
