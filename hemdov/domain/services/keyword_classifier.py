"""Keyword-based priority classifier implementation."""

from shared.priority_entities import PriorityRule


class KeywordBasedClassifier:
    """Default implementation using keyword matching."""

    DEFAULT_RULES = (
        PriorityRule(("instructions", "rule"), priority=5, category="instruction"),
        PriorityRule(("agent",), priority=4, category="agent"),
    )

    def __init__(self, rules: tuple[PriorityRule, ...] | None = None):
        self.rules = rules or self.DEFAULT_RULES

    def classify(self, filename: str) -> tuple[int, str]:
        """
        Classify filename using keyword rules.

        Args:
            filename: Name of file to classify

        Returns:
            Tuple of (priority, category)
        """
        basename = filename.lower()
        for rule in self.rules:
            if any(kw in basename for kw in rule.keywords):
                return rule.priority, rule.category
        return 1, "general"  # Default
