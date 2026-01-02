"""Example pool for few-shot learning."""
from typing import List, Dict


class ExamplePool:
    """Pool of examples for few-shot learning."""

    def __init__(self):
        self.examples: List[Dict] = []
        self.domains: set = set()

    def build(self, train_examples: List[Dict]) -> None:
        """Build example pool from training set.

        Args:
            train_examples: List of training examples
        """
        self.examples = train_examples
        self.domains = {ex['metadata']['domain'] for ex in train_examples}

    def has_domain(self, domain: str) -> bool:
        """Check if domain exists in pool."""
        return domain in self.domains

    def get_examples_by_domain(self, domain: str) -> List[Dict]:
        """Get examples for specific domain."""
        return [ex for ex in self.examples if ex['metadata']['domain'] == domain]
