# tests/conftest.py
import asyncio
from pathlib import Path

import pytest


@pytest.fixture
def temp_db_path(tmp_path: Path) -> str:
    """Provide temporary database path for tests."""
    return str(tmp_path / "test_prompt_history.db")

@pytest.fixture
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()
