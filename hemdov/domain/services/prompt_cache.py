"""
Prompt Cache - SHA256-based caching layer.

Stores computed prompts to avoid re-computation.
Cache key is SHA256(idea + context + mode) for deterministic lookups.
"""

import hashlib
import json
import logging
from datetime import UTC, datetime
from typing import TypedDict

import aiosqlite

from hemdov.domain.dto.nlac_models import NLaCRequest, PromptObject


class CacheStats(TypedDict):
    """Type-safe cache statistics dictionary."""
    total_entries: int
    total_hits: int
    avg_hit_count: float

logger = logging.getLogger(__name__)


class PromptCache:
    """
    SHA256-based prompt cache.

    Features:
    - Deterministic cache key from (idea, context, mode)
    - Hit count tracking for cache analytics
    - Automatic last_accessed timestamp updates
    """

    def __init__(self, repository=None):
        """
        Initialize cache with optional repository.

        Args:
            repository: Optional PromptRepository for persistent cache.
                       If None, cache is in-memory only (for testing).
        """
        self.repository = repository
        self._memory_cache: dict[str, dict] = {}  # In-memory fallback

    def generate_key(self, request: NLaCRequest) -> str:
        """
        Generate SHA256 cache key from request.

        Key format: SHA256(idea + context + mode)

        Args:
            request: NLaCRequest to hash

        Returns:
            Hexadecimal SHA256 hash
        """
        # Normalize inputs for deterministic hashing
        normalized = f"{request.idea}|{request.context}|{request.mode}"
        return hashlib.sha256(normalized.encode()).hexdigest()

    async def get(self, request: NLaCRequest) -> PromptObject | None:
        """
        Retrieve cached prompt if available.

        Updates hit_count and last_accessed on cache hit.

        Args:
            request: NLaCRequest to look up

        Returns:
            PromptObject if found, None otherwise
        """
        cache_key = self.generate_key(request)

        # Try persistent cache first
        if self.repository:
            try:
                cached = await self.repository.get_cached_prompt(cache_key)
                if cached:
                    # Update access stats
                    await self.repository.update_cache_access(cache_key)
                    logger.debug(f"Cache hit: {cache_key[:8]}...")
                    return cached
            except (aiosqlite.Error, ConnectionError, TimeoutError, json.JSONDecodeError) as e:
                logger.warning(f"Cache lookup failed: {type(e).__name__}: {e}, falling back to memory")

        # Fallback to in-memory cache
        if cache_key in self._memory_cache:
            entry = self._memory_cache[cache_key]
            entry["hit_count"] += 1
            entry["last_accessed"] = datetime.now(UTC).isoformat()
            logger.debug(f"Memory cache hit: {cache_key[:8]}...")
            return entry["prompt_obj"]

        logger.debug(f"Cache miss: {cache_key[:8]}...")
        return None

    async def put(self, request: NLaCRequest, prompt_obj: PromptObject) -> None:
        """
        Store prompt in cache.

        Args:
            request: NLaCRequest used as cache key
            prompt_obj: PromptObject to cache
        """
        cache_key = self.generate_key(request)
        now = datetime.now(UTC).isoformat()

        # ALWAYS store in memory cache first (for fast reads)
        self._memory_cache[cache_key] = {
            "prompt_obj": prompt_obj,
            "hit_count": 0,  # Starts at 0, incremented on get
            "created_at": now,
            "last_accessed": now,
        }
        logger.debug(f"Cached to memory: {cache_key[:8]}...")

        # Try persistent cache (for durability)
        if self.repository:
            try:
                await self.repository.cache_prompt(
                    cache_key=cache_key,
                    prompt_id=prompt_obj.id,
                    improved_prompt=prompt_obj.template,
                )
                logger.debug(f"Cached to repository: {cache_key[:8]}...")
            except (aiosqlite.Error, ConnectionError, TimeoutError) as e:
                logger.warning(f"Failed to persist to repository: {type(e).__name__}: {e}")

    async def invalidate(self, request: NLaCRequest) -> bool:
        """
        Remove prompt from cache.

        Args:
            request: NLaCRequest to invalidate

        Returns:
            True if entry was removed, False if not found
        """
        cache_key = self.generate_key(request)

        # Try persistent cache
        if self.repository:
            try:
                deleted = await self.repository.delete_cached_prompt(cache_key)
                if deleted:
                    logger.info(f"Invalidated cache: {cache_key[:8]}...")
                    return True
            except (aiosqlite.Error, ConnectionError, TimeoutError) as e:
                logger.warning(f"Cache invalidation failed: {type(e).__name__}: {e}")

        # Fallback to in-memory cache
        if cache_key in self._memory_cache:
            del self._memory_cache[cache_key]
            logger.info(f"Invalidated memory cache: {cache_key[:8]}...")
            return True

        return False

    async def get_stats(self) -> dict[str, object]:
        """
        Get cache statistics.

        Returns:
            Dict with cache metrics (total_entries, total_hits, etc.)
        """
        # Get stats from repository if available
        if self.repository:
            try:
                return await self.repository.get_cache_stats()
            except (aiosqlite.Error, ConnectionError, TimeoutError, json.JSONDecodeError) as e:
                logger.warning(f"Failed to get cache stats: {type(e).__name__}: {e}")

        # Fallback to in-memory stats
        total_hits = sum(e["hit_count"] for e in self._memory_cache.values())
        return {
            "total_entries": len(self._memory_cache),
            "total_hits": total_hits,
            "avg_hit_count": total_hits / len(self._memory_cache) if self._memory_cache else 0,
        }

    async def clear(self) -> int:
        """
        Clear all cache entries.

        Returns:
            Number of entries cleared
        """
        count = 0

        # Clear persistent cache
        if self.repository:
            try:
                count = await self.repository.clear_cache()
                logger.info(f"Cleared {count} cache entries from repository")
            except (aiosqlite.Error, ConnectionError, TimeoutError) as e:
                logger.warning(f"Cache clear failed: {type(e).__name__}: {e}")

        # Clear in-memory cache
        memory_count = len(self._memory_cache)
        self._memory_cache.clear()
        logger.info(f"Cleared {memory_count} cache entries from memory")

        return count + memory_count
