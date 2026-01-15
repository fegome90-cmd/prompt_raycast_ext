"""
Unit tests for the PromptAugmenter domain service.
Following the architecture proposal: No IO, pure domain logic testing.
"""

import pytest
from dataclasses import FrozenInstanceError
from shared.context_entities import ContextItem
from hemdov.domain.services.prompt_augmenter import PromptAugmenter


class MockContextLoader:
    """Mock implementation of ContextLoader port."""

    def __init__(self, items: list[ContextItem]):
        self.items = items
        self.loaded_paths = []

    def load_all(self, file_paths: list[str]) -> list[ContextItem]:
        self.loaded_paths = file_paths
        return self.items


def test_context_item_immutability():
    """Verify ContextItem is frozen."""
    item = ContextItem(source="test.md", content="test")
    with pytest.raises(FrozenInstanceError):
        item.priority = 10  # type: ignore


def test_prompt_augmenter_aggregation():
    """Verify that PromptAugmenter aggregates content correctly."""
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


def test_prompt_augmenter_empty_context():
    """Verify handling of empty context."""
    loader = MockContextLoader([])
    augmenter = PromptAugmenter(loader)

    result = augmenter.get_aggregated_context([])
    assert result == ""
