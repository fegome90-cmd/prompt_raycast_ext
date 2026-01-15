"""
Prompt Augmenter Service - Pure Domain Layer.
Responsible for orchestrating the context retrieval and integration.
"""

from typing import List
from shared.context_entities import ContextItem
from hemdov.domain.ports.context_loader import ContextLoader


class PromptAugmenter:
    """
    Pure domain service for prompt augmentation.
    Injected with a ContextLoader port.
    """

    def __init__(self, loader: ContextLoader):
        self.loader = loader

    def get_aggregated_context(self, file_paths: List[str]) -> str:
        """
        Loads and aggregates context from multiple sources.
        Sorts by priority (highest first).
        """
        items: List[ContextItem] = self.loader.load_all(file_paths)

        # Sort by priority DESC (5 is highest)
        sorted_items = sorted(items, key=lambda x: x.priority, reverse=True)

        # Aggregate content with separators
        aggregated = []
        for item in sorted_items:
            header = f"### CONTEXT SOURCE: {item.source} (Category: {item.category})"
            aggregated.append(f"{header}\n{item.content}")

        return "\n\n---\n\n".join(aggregated)
