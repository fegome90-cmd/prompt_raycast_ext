"""
Integration tests for ParallelFileLoader adapter.
Verifies real IO operations and parallel execution logic.
"""

import os
import tempfile

import pytest

from hemdov.infrastructure.adapters.parallel_loader import ParallelFileLoader


def test_parallel_loader_real_files():
    """Verify that ParallelFileLoader can read temporary files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create some test files
        rule_file = os.path.join(tmpdir, "instructions.md")
        other_file = os.path.join(tmpdir, "general.txt")

        with open(rule_file, "w") as f:
            f.write("System Rules")
        with open(other_file, "w") as f:
            f.write("General Context")

        loader = ParallelFileLoader(max_workers=2)
        items = loader.load_all([rule_file, other_file])

        assert len(items) == 2

        # Verify content and priority
        items_dict = {os.path.basename(item.source): item for item in items}

        assert items_dict["instructions.md"].content == "System Rules"
        assert items_dict["instructions.md"].priority == 5
        assert items_dict["instructions.md"].category == "instruction"

        assert items_dict["general.txt"].content == "General Context"
        assert items_dict["general.txt"].priority == 1


def test_parallel_loader_missing_file():
    """Verify handling of missing files."""
    loader = ParallelFileLoader()
    items = loader.load_all(["non_existent_file.txt"])

    assert len(items) == 1
    assert "ERROR" in items[0].content
    assert items[0].category == "error"


def test_parallel_loader_empty_list():
    """Verify handling of empty file list."""
    loader = ParallelFileLoader()
    assert loader.load_all([]) == []


def test_parallel_loader_should_use_injected_classifier():
    """Verify that ParallelFileLoader uses injected classifier."""

    class MockClassifier:
        def classify(self, filename: str) -> tuple[int, str]:
            return 10, "mock"  # Values the default classifier would never use

    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = os.path.join(tmpdir, "test.md")
        with open(test_file, "w") as f:
            f.write("Test")

        loader = ParallelFileLoader(classifier=MockClassifier())
        items = loader.load_all([test_file])

        assert items[0].priority == 10
        assert items[0].category == "mock"


def test_parallel_loader_should_reject_invalid_max_workers():
    """Verify max_workers validation."""
    with pytest.raises(ValueError, match="max_workers must be"):
        ParallelFileLoader(max_workers=0)

    with pytest.raises(ValueError, match="max_workers too high"):
        ParallelFileLoader(max_workers=101)
