"""Tests for framework normalization before PromptHistory persistence."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from hemdov.infrastructure.config import Settings


@pytest.mark.asyncio
async def test_save_history_normalizes_decomposition_framework_and_persists():
    """Free-form decomposition framework should be normalized and persisted."""
    from api.prompt_improver_api import _save_history_async

    settings = Settings(
        SQLITE_ENABLED=True,
        SQLITE_DB_PATH=":memory:",
        SQLITE_WAL_MODE=True,
    )

    mock_repo = AsyncMock()
    mock_breaker = AsyncMock()

    mock_result = MagicMock()
    mock_result.improved_prompt = "improved prompt"
    mock_result.role = "Architect"
    mock_result.directive = "Design robust policy"
    mock_result.framework = "Decomposition: break down into steps"
    mock_result.guardrails = ["be concrete"]
    mock_result.reasoning = None
    mock_result.confidence = 0.9

    with patch("api.prompt_improver_api.get_repository", return_value=mock_repo):
        with patch("api.prompt_improver_api._circuit_breaker", mock_breaker):
            await _save_history_async(
                settings=settings,
                original_idea="Design retries",
                context="Need deterministic fallback",
                result=mock_result,
                backend="moderate",
                latency_ms=120,
            )

    mock_repo.save.assert_awaited_once()
    saved_history = mock_repo.save.await_args.args[0]
    assert saved_history.framework == "decomposition"
    mock_breaker.record_failure.assert_not_called()


@pytest.mark.parametrize(
    ("framework_raw", "expected"),
    [
        ("Decomposition: break down into steps", "decomposition"),
        ("chain reasoning", "chain-of-thought"),
        ("CoT with examples", "chain-of-thought"),
        ("Tree search plan", "tree-of-thoughts"),
        ("ToT beam strategy", "tree-of-thoughts"),
        ("role based orchestration", "role-playing"),
        ("role-playing", "role-playing"),
    ],
)
def test_normalize_framework_for_history_heuristics(framework_raw: str, expected: str):
    from api.prompt_improver_api import normalize_framework_for_history

    normalized, used_fallback = normalize_framework_for_history(framework_raw)
    assert normalized == expected
    assert used_fallback is False


@pytest.mark.asyncio
async def test_save_history_unknown_framework_uses_safe_fallback_and_logs_warning(caplog):
    """Unknown framework variants should fallback to decomposition and leave a trace."""
    from api.prompt_improver_api import _save_history_async

    settings = Settings(
        SQLITE_ENABLED=True,
        SQLITE_DB_PATH=":memory:",
        SQLITE_WAL_MODE=True,
    )

    mock_repo = AsyncMock()
    mock_breaker = AsyncMock()

    mock_result = MagicMock()
    mock_result.improved_prompt = "improved prompt"
    mock_result.role = "Architect"
    mock_result.directive = "Design robust policy"
    mock_result.framework = "Unrecognized Framework Name"
    mock_result.guardrails = ["be concrete"]
    mock_result.reasoning = None
    mock_result.confidence = 0.9

    with patch("api.prompt_improver_api.get_repository", return_value=mock_repo):
        with patch("api.prompt_improver_api._circuit_breaker", mock_breaker):
            with caplog.at_level("WARNING", logger="api.prompt_improver_api"):
                await _save_history_async(
                    settings=settings,
                    original_idea="Design retries",
                    context="Need deterministic fallback",
                    result=mock_result,
                    backend="moderate",
                    latency_ms=120,
                )

    mock_repo.save.assert_awaited_once()
    saved_history = mock_repo.save.await_args.args[0]
    assert saved_history.framework == "decomposition"
    assert "event=framework_normalization_fallback" in caplog.text
    assert "framework_raw='Unrecognized Framework Name'" in caplog.text
    mock_breaker.record_failure.assert_not_called()


@pytest.mark.asyncio
async def test_save_history_logs_structured_persistence_failed_on_repo_error(caplog):
    """Persistence failures should emit structured log context for operations."""
    from api.prompt_improver_api import _save_history_async

    settings = Settings(
        SQLITE_ENABLED=True,
        SQLITE_DB_PATH=":memory:",
        SQLITE_WAL_MODE=True,
    )

    mock_repo = AsyncMock()
    mock_repo.save.side_effect = ConnectionError("db unavailable")
    mock_breaker = AsyncMock()

    mock_result = MagicMock()
    mock_result.improved_prompt = "improved prompt"
    mock_result.role = "Architect"
    mock_result.directive = "Design robust policy"
    mock_result.framework = "chain-of-thought"
    mock_result.guardrails = ["be concrete"]
    mock_result.reasoning = None
    mock_result.confidence = 0.9

    with patch("api.prompt_improver_api.get_repository", return_value=mock_repo):
        with patch("api.prompt_improver_api._circuit_breaker", mock_breaker):
            with caplog.at_level("ERROR", logger="api.prompt_improver_api"):
                await _save_history_async(
                    settings=settings,
                    original_idea="Design retries",
                    context="Need deterministic fallback",
                    result=mock_result,
                    backend="moderate",
                    latency_ms=120,
                    mode="nlac",
                    request_id="req-1234",
                )

    assert "event=persistence_failed" in caplog.text
    assert "error_type=ConnectionError" in caplog.text
    assert "request_id=req-1234" in caplog.text
    assert "backend=moderate" in caplog.text
    assert "mode=nlac" in caplog.text
    mock_breaker.record_failure.assert_awaited_once()


@pytest.mark.asyncio
async def test_save_history_sqlite_disabled_does_not_emit_persistence_failed(caplog):
    """Disabled persistence by config should not be logged as a failure."""
    from api.prompt_improver_api import _save_history_async

    settings = Settings(
        SQLITE_ENABLED=False,
        SQLITE_DB_PATH=":memory:",
        SQLITE_WAL_MODE=True,
    )

    mock_breaker = AsyncMock()

    mock_result = MagicMock()
    mock_result.improved_prompt = "improved prompt"
    mock_result.role = "Architect"
    mock_result.directive = "Design robust policy"
    mock_result.framework = "chain-of-thought"
    mock_result.guardrails = ["be concrete"]
    mock_result.reasoning = None
    mock_result.confidence = 0.9

    with patch("api.prompt_improver_api._circuit_breaker", mock_breaker):
        with caplog.at_level("WARNING", logger="api.prompt_improver_api"):
            await _save_history_async(
                settings=settings,
                original_idea="Design retries",
                context="Need deterministic fallback",
                result=mock_result,
                backend="moderate",
                latency_ms=120,
                mode="legacy",
                request_id="req-4321",
            )

    assert "event=persistence_failed" not in caplog.text
    mock_breaker.record_failure.assert_not_called()
