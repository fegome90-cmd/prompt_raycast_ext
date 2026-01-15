# hemdov/domain/repositories/prompt_repository.py
from abc import ABC, abstractmethod

from hemdov.domain.entities.prompt_history import PromptHistory


class PromptRepository(ABC):
    """
    Repository interface for prompt history persistence.

    Follows Dependency Inversion Principle - domain defines interface,
    infrastructure provides implementation.
    """

    @abstractmethod
    async def save(self, history: PromptHistory) -> int:
        """
        Save a prompt history record.

        Returns:
            int: The ID of the saved record
        """
        pass

    @abstractmethod
    async def find_by_id(self, history_id: int) -> PromptHistory | None:
        """Find a prompt history by ID."""
        pass

    @abstractmethod
    async def find_recent(
        self,
        limit: int = 50,
        offset: int = 0,
        provider: str | None = None,
        backend: str | None = None,
    ) -> list[PromptHistory]:
        """Find recent prompts with optional filters."""
        pass

    @abstractmethod
    async def search(self, query: str, limit: int = 20) -> list[PromptHistory]:
        """Search prompts by text content."""
        pass

    @abstractmethod
    async def delete_old_records(self, days: int) -> int:
        """
        Delete records older than specified days.

        Returns:
            int: Number of records deleted
        """
        pass

    @abstractmethod
    async def get_statistics(self) -> dict:
        """Get usage statistics."""
        pass

    @abstractmethod
    async def close(self):
        """Close database connections and cleanup resources."""
        pass
