"""
Shared context entities for the PromptAugmenter system.
Following clean architecture principles: immutable, pure python, and framework-agnostic.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class ContextItem:
    """Represents a single context file or rule."""

    source: str  # e.g., "agents.md"
    content: str  # The markdown/text content
    priority: int = 1  # 1 (low) to 5 (critical)
    category: str = "general"  # "agent", "rule", "instruction"
