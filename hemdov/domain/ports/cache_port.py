#!/usr/bin/env python3
"""Cache port for domain layer - hexagonal architecture."""
from typing import Any, Protocol


class CachePort(Protocol):
    """Cache interface for domain layer.

    This port defines the contract for cache implementations in the hexagonal
    architecture. The domain layer depends on this Protocol, while infrastructure
    provides concrete implementations (e.g., SQLiteCache, InMemoryCache).

    Methods:
        get: Retrieve cached value
        set: Store value with TTL
        invalidate_by_version: Invalidate all entries for a catalog version
    """

    def get(self, key: str) -> Any | None:
        """Retrieve cached value.

        Args:
            key: Cache key to retrieve

        Returns:
            Cached value or None if not found/expired
        """
        ...

    def set(self, key: str, value: Any, ttl: int = 86400) -> None:
        """Store value with TTL.

        Args:
            key: Cache key to store under
            value: Value to cache (must be JSON-serializable)
            ttl: Time to live in seconds (default: 24 hours)
        """
        ...

    def invalidate_by_version(self, version: str) -> None:
        """Invalidate all entries for a specific catalog version.

        Args:
            version: Catalog version string to invalidate
        """
        ...
