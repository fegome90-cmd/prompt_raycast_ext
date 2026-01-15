"""
Context Loader Port - Hexagonal Architecture.
Defines the protocol for loading context data into the domain.
"""

from typing import Protocol, List
from shared.context_entities import ContextItem


class ContextLoader(Protocol):
    """
    Contract for loading context documents.
    Provided by the infrastructure layer.
    """

    def load_all(self, file_paths: List[str]) -> List[ContextItem]:
        """
        Loads multiple context files and returns a list of ContextItems.
        Must be synchronous to keep the domain simple.
        """
        ...
