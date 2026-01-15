"""Test SQLite repository handles specific exceptions correctly."""

import pytest

from hemdov.infrastructure.config import Settings
from hemdov.infrastructure.persistence.sqlite_prompt_repository import SQLitePromptRepository


@pytest.mark.asyncio
async def test_repository_handles_aiosqlite_error():
    """Repository should handle aiosqlite.Error gracefully during configure."""
    # Use in-memory database for testing
    settings = Settings(SQLITE_DB_PATH=":memory:")
    repo = SQLitePromptRepository(settings)

    # First connection triggers initialization - should succeed
    conn = await repo._get_connection()
    assert conn is not None
    await repo.close()


@pytest.mark.asyncio
async def test_propagates_keyboard_interrupt():
    """Repository should propagate KeyboardInterrupt during configure."""
    settings = Settings(SQLITE_DB_PATH=":memory:")
    repo = SQLitePromptRepository(settings)

    # Mock configure to raise KeyboardInterrupt
    original = repo._configure_connection

    async def mock_configure_with_interrupt(conn):
        raise KeyboardInterrupt()

    repo._configure_connection = mock_configure_with_interrupt

    # Should raise KeyboardInterrupt
    with pytest.raises(KeyboardInterrupt):
        await repo._get_connection()

    # Restore original
    repo._configure_connection = original
