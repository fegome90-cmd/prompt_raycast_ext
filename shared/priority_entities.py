"""Priority classification entities."""

from dataclasses import dataclass


@dataclass(frozen=True)
class PriorityRule:
    """Rule for determining context item priority."""

    keywords: tuple[str, ...]
    priority: int
    category: str
