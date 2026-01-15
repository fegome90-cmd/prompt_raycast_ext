"""Priority Classifier Port - Hexagonal Architecture."""

from typing import Protocol


class PriorityClassifier(Protocol):
    """Determines priority and category for context files."""

    def classify(self, filename: str) -> tuple[int, str]:
        """
        Returns (priority, category) based on filename.

        Args:
            filename: Name of the file to classify

        Returns:
            Tuple of (priority: 1-5, category: str)
        """
        ...
