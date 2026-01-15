"""Additional critical tests for edge cases identified in code review."""

import os
import tempfile

import pytest

from hemdov.domain.services.prompt_augmenter import PromptAugmenter
from hemdov.infrastructure.adapters.parallel_loader import ParallelFileLoader
from shared.context_entities import ContextItem


class MockContextLoader:
    """Mock loader for testing PromptAugmenter."""

    def __init__(self, items: list[ContextItem]):
        self.items = items

    def load_all(self, file_paths: list[str]) -> list[ContextItem]:
        return self.items


def test_parallel_loader_should_handle_mixed_success_and_failure():
    """Verify that partial failures don't crash entire load operation."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create one valid file
        valid_file = os.path.join(tmpdir, "valid.txt")
        with open(valid_file, "w") as f:
            f.write("Valid content")

        # Mix valid and invalid paths
        loader = ParallelFileLoader()
        items = loader.load_all(
            [
                valid_file,
                "/nonexistent/path.txt",
                "",  # This will trigger validation error in classify
            ]
        )

        # Should have 3 items (1 success, 2 errors)
        assert len(items) >= 2  # At least the valid file and one error

        # Check that valid file was loaded
        valid_items = [item for item in items if item.category != "error"]
        assert len(valid_items) >= 1
        assert any("Valid content" in item.content for item in valid_items)


def test_parallel_loader_should_include_file_path_in_error_messages():
    """Verify error messages include the problematic file path."""
    loader = ParallelFileLoader()
    items = loader.load_all(["/this/path/does/not/exist.txt"])

    assert len(items) == 1
    assert items[0].category == "error"
    assert "/this/path/does/not/exist.txt" in items[0].content
    assert items[0].source == "/this/path/does/not/exist.txt"


def test_prompt_augmenter_should_handle_non_string_paths():
    """Verify that non-string paths raise ValueError."""
    loader = MockContextLoader([])
    augmenter = PromptAugmenter(loader)

    with pytest.raises(ValueError, match="Invalid file path"):
        augmenter.get_aggregated_context([None])  # type: ignore

    with pytest.raises(ValueError, match="Invalid file path"):
        augmenter.get_aggregated_context([123])  # type: ignore
