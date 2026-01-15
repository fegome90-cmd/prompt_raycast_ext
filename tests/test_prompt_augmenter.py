"""
Unit tests for the PromptAugmenter domain service.
Following the architecture proposal: No IO, pure domain logic testing.
"""

from dataclasses import FrozenInstanceError

import pytest

from hemdov.domain.services.prompt_augmenter import PromptAugmenter
from shared.context_entities import ContextItem


class MockContextLoader:
    """Mock implementation of ContextLoader port."""

    def __init__(self, items: list[ContextItem]):
        self.items = items
        self.loaded_paths = []

    def load_all(self, file_paths: list[str]) -> list[ContextItem]:
        self.loaded_paths = file_paths
        return self.items


def test_context_item_should_raise_frozen_error_when_mutated():
    """Verify ContextItem is frozen and raises error when mutated."""
    item = ContextItem(source="test.md", content="test")
    with pytest.raises(FrozenInstanceError):
        item.priority = 10  # type: ignore


def test_prompt_augmenter_should_aggregate_sorted_by_priority():
    """Verify that PromptAugmenter aggregates content sorted by priority (highest first)."""
    items = [
        ContextItem(source="rules.md", content="Rule 1", priority=5),
        ContextItem(source="agent.md", content="Agent 1", priority=1),
    ]
    loader = MockContextLoader(items)
    augmenter = PromptAugmenter(loader)

    result = augmenter.get_aggregated_context(["rules.md", "agent.md"])

    assert "Rule 1" in result
    assert "Agent 1" in result
    assert result.index("Rule 1") < result.index("Agent 1")  # High priority first
    assert "CONTEXT SOURCE: rules.md" in result


def test_prompt_augmenter_should_return_empty_string_when_no_context():
    """Verify handling of empty context."""
    loader = MockContextLoader([])
    augmenter = PromptAugmenter(loader)

    result = augmenter.get_aggregated_context([])
    assert result == ""


def test_prompt_augmenter_should_raise_on_invalid_path():
    """Verify that invalid file paths raise ValueError."""
    loader = MockContextLoader([])
    augmenter = PromptAugmenter(loader)

    with pytest.raises(ValueError, match="Invalid file path"):
        augmenter.get_aggregated_context([""])

    with pytest.raises(ValueError, match="Invalid file path"):
        augmenter.get_aggregated_context(["  "])  # whitespace only


def test_prompt_augmenter_should_filter_error_items():
    """Verify that items with category='error' are filtered out."""
    items = [
        ContextItem(source="good.md", content="Good", priority=5),
        ContextItem(source="bad.md", content="ERROR: ...", priority=1, category="error"),
    ]
    loader = MockContextLoader(items)
    augmenter = PromptAugmenter(loader)

    result = augmenter.get_aggregated_context(["good.md", "bad.md"])

    assert "Good" in result
    assert "ERROR" not in result
    assert "bad.md" not in result
