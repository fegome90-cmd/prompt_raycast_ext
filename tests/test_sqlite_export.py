"""Tests for SQLite to DSPy export functionality."""

import pytest
import json
from pathlib import Path
import tempfile
import aiosqlite
from datetime import datetime, timezone


@pytest.fixture
def temp_db_with_data():
    """Create a temporary SQLite database with test data."""
    db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    db_path = db.name
    db.close()

    async def setup():
        async with aiosqlite.connect(db_path) as conn:
            await conn.execute("""
                CREATE TABLE prompt_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at TEXT,
                    original_idea TEXT,
                    context TEXT,
                    improved_prompt TEXT,
                    role TEXT,
                    directive TEXT,
                    framework TEXT,
                    guardrails TEXT,
                    reasoning TEXT,
                    confidence REAL,
                    backend TEXT,
                    model TEXT,
                    provider TEXT,
                    latency_ms INTEGER
                )
            """)

            # Use fixed timestamps to ensure consistent ordering
            timestamp1 = "2024-01-01T10:00:00+00:00"
            timestamp2 = "2024-01-02T10:00:00+00:00"

            # Insert test data (note: timestamp2 > timestamp1, so idea 2 comes first when DESC)
            await conn.execute(
                """
                INSERT INTO prompt_history
                (original_idea, context, improved_prompt, role, directive, framework,
                 guardrails, reasoning, confidence, backend, model, provider, latency_ms, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                ("test idea 1", "test context", "improved 1", "role1", "directive1",
                 "framework1", "[]", "reasoning1", 0.9, "backend1", "model1", "provider1", 100,
                 timestamp1)
            )

            await conn.execute(
                """
                INSERT INTO prompt_history
                (original_idea, context, improved_prompt, role, directive, framework,
                 guardrails, reasoning, confidence, backend, model, provider, latency_ms, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                ("test idea 2", None, "improved 2", "role2", "directive2",
                 "framework2", "[]", "reasoning2", 0.8, "backend2", "model2", "provider2", 200,
                 timestamp2)
            )

            await conn.commit()

    import asyncio
    asyncio.run(setup())

    yield db_path

    # Cleanup
    Path(db_path).unlink(missing_ok=True)


def test_export_script_exists():
    """Test that export script exists."""
    script_path = Path(__file__).parent.parent / "scripts" / "data" / "export_sqlite_to_dspy.py"
    assert script_path.exists(), f"Export script not found at {script_path}"


def test_export_format(temp_db_with_data, tmp_path):
    """Test that export produces correct DSPy format."""
    import sys
    import asyncio

    # Import the export function
    sys.path.insert(0, str(Path(__file__).parent.parent / "scripts" / "data"))
    from export_sqlite_to_dspy import export_sqlite_to_dspy

    output_path = tmp_path / "output.json"

    # Run export
    examples = asyncio.run(export_sqlite_to_dspy(
        str(temp_db_with_data),
        str(output_path),
        limit=10
    ))

    # Verify structure
    assert len(examples) == 2
    assert all("input" in e for e in examples)
    assert all("output" in e for e in examples)
    assert all("metadata" in e for e in examples)

    # Verify content (ordered by created_at DESC, so idea 2 comes first)
    assert "test idea 2" in examples[0]["input"]
    assert "improved 2" == examples[0]["output"]
    assert examples[0]["metadata"]["role"] == "role2"

    # Second example should have context in input
    assert "test idea 1" in examples[1]["input"]
    assert "Context: test context" in examples[1]["input"]


def test_export_writes_file(temp_db_with_data, tmp_path):
    """Test that export writes JSON file."""
    import sys
    import asyncio

    sys.path.insert(0, str(Path(__file__).parent.parent / "scripts" / "data"))
    from export_sqlite_to_dspy import export_sqlite_to_dspy

    output_path = tmp_path / "test_output.json"

    asyncio.run(export_sqlite_to_dspy(
        str(temp_db_with_data),
        str(output_path),
        limit=10
    ))

    # Verify file exists and is valid JSON
    assert output_path.exists()

    with open(output_path, 'r') as f:
        data = json.load(f)

    assert isinstance(data, list)
    assert len(data) == 2


def test_export_with_limit(temp_db_with_data, tmp_path):
    """Test that limit parameter works."""
    import sys
    import asyncio

    sys.path.insert(0, str(Path(__file__).parent.parent / "scripts" / "data"))
    from export_sqlite_to_dspy import export_sqlite_to_dspy

    output_path = tmp_path / "limited.json"

    examples = asyncio.run(export_sqlite_to_dspy(
        str(temp_db_with_data),
        str(output_path),
        limit=1  # Only export 1
    ))

    assert len(examples) == 1


def test_metadata_preservation(temp_db_with_data, tmp_path):
    """Test that metadata is properly preserved."""
    import sys
    import asyncio

    sys.path.insert(0, str(Path(__file__).parent.parent / "scripts" / "data"))
    from export_sqlite_to_dspy import export_sqlite_to_dspy

    output_path = tmp_path / "metadata_test.json"

    examples = asyncio.run(export_sqlite_to_dspy(
        str(temp_db_with_data),
        str(output_path),
        limit=1
    ))

    metadata = examples[0]["metadata"]

    # Check all metadata fields (idea 2 comes first due to DESC ordering)
    assert metadata["role"] == "role2"
    assert metadata["directive"] == "directive2"
    assert metadata["framework"] == "framework2"
    assert metadata["confidence"] == 0.8
    assert metadata["backend"] == "backend2"
    assert metadata["model"] == "model2"
    assert metadata["provider"] == "provider2"
    assert metadata["latency_ms"] == 200


def test_empty_database(tmp_path):
    """Test behavior with empty database."""
    import tempfile
    import asyncio
    import sys

    # Create empty database
    db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    db_path = db.name
    db.close()

    async def setup():
        async with aiosqlite.connect(db_path) as conn:
            await conn.execute("""
                CREATE TABLE prompt_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at TEXT,
                    original_idea TEXT,
                    context TEXT,
                    improved_prompt TEXT,
                    role TEXT,
                    directive TEXT,
                    framework TEXT,
                    guardrails TEXT,
                    reasoning TEXT,
                    confidence REAL,
                    backend TEXT,
                    model TEXT,
                    provider TEXT,
                    latency_ms INTEGER
                )
            """)
            await conn.commit()

    asyncio.run(setup())

    sys.path.insert(0, str(Path(__file__).parent.parent / "scripts" / "data"))
    from export_sqlite_to_dspy import export_sqlite_to_dspy

    output_path = tmp_path / "empty.json"

    examples = asyncio.run(export_sqlite_to_dspy(
        db_path,
        str(output_path),
        limit=10
    ))

    assert len(examples) == 0

    # Cleanup
    Path(db_path).unlink(missing_ok=True)


def test_combined_input_with_context(temp_db_with_data, tmp_path):
    """Test that context is properly combined with original_idea."""
    import sys
    import asyncio

    sys.path.insert(0, str(Path(__file__).parent.parent / "scripts" / "data"))
    from export_sqlite_to_dspy import export_sqlite_to_dspy

    output_path = tmp_path / "combined_test.json"

    examples = asyncio.run(export_sqlite_to_dspy(
        str(temp_db_with_data),
        str(output_path),
        limit=1
    ))

    # First example (most recent) is idea 2 which has no context
    assert "test idea 2" in examples[0]["input"]
    assert "Context:" not in examples[0]["input"]


def test_input_output_only_for_dspy(temp_db_with_data, tmp_path):
    """Test that format is compatible with DSPy KNNFewShot."""
    import sys
    import asyncio

    sys.path.insert(0, str(Path(__file__).parent.parent / "scripts" / "data"))
    from export_sqlite_to_dspy import export_sqlite_to_dspy

    output_path = tmp_path / "dspy_format.json"

    examples = asyncio.run(export_sqlite_to_dspy(
        str(temp_db_with_data),
        str(output_path),
        limit=10
    ))

    # DSPy KNNFewShot needs input/output pairs
    # Verify we can create DSPy Example objects from this
    for example in examples:
        assert "input" in example
        assert "output" in example
        assert isinstance(example["input"], str)
        assert isinstance(example["output"], str)
