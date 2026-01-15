"""
Prompt Augmenter Service - Pure Domain Layer.
Responsible for orchestrating the context retrieval and integration.
"""

from operator import attrgetter

from hemdov.domain.ports.context_loader import ContextLoader
from shared.context_entities import ContextItem


class PromptAugmenter:
    """
    Pure domain service for prompt augmentation.
    Injected with a ContextLoader port.
    """

    def __init__(self, loader: ContextLoader):
        self.loader = loader

    def get_aggregated_context(self, file_paths: list[str]) -> str:
        """
        Loads and aggregates context from multiple sources.
        Sorts by priority (highest first).

        Args:
            file_paths: List of file paths to load

        Returns:
            Aggregated context string (empty if no valid items)

        Raises:
            ValueError: If file_paths contains invalid entries
        """
        if not file_paths:
            return ""

        # Validate file paths
        for path in file_paths:
            if not isinstance(path, str) or not path.strip():
                raise ValueError(f"Invalid file path: {path!r}")

        items: list[ContextItem] = self.loader.load_all(file_paths)

        if not items:
            return ""

        # Filter out error items (defensive)
        valid_items = [item for item in items if item.category != "error"]

        if not valid_items:
            return ""

        # Sort by priority DESC (5 is highest)
        sorted_items = sorted(valid_items, key=attrgetter("priority"), reverse=True)

        # Aggregate content with separators
        aggregated = []
        for item in sorted_items:
            header = f"### CONTEXT SOURCE: {item.source} (Category: {item.category})"
            aggregated.append(f"{header}\n{item.content}")

        return "\n\n---\n\n".join(aggregated)
