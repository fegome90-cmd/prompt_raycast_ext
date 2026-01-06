"""
Tests for PromptCache service.

Tests SHA256-based caching without requiring full repository setup.
"""

import pytest
from datetime import datetime, UTC

from hemdov.domain.dto.nlac_models import NLaCRequest, PromptObject, IntentType
from hemdov.domain.services.prompt_cache import PromptCache


class TestPromptCache:
    """Test PromptCache service."""

    @pytest.fixture
    def cache(self):
        """Create in-memory cache (no repository)."""
        return PromptCache(repository=None)

    @pytest.fixture
    def sample_request(self):
        """Create sample NLaCRequest."""
        return NLaCRequest(
            idea="Create a hello world function",
            context="In Python",
            mode="nlac"
        )

    @pytest.fixture
    def sample_prompt(self):
        """Create sample PromptObject."""
        return PromptObject(
            id="test-123",
            version="1.0.0",
            intent_type=IntentType.GENERATE,
            template="You are a Developer.\n\nCreate a hello world function.",
            strategy_meta={"strategy": "simple"},
            constraints={"max_tokens": 500},
            created_at=datetime.now(UTC).isoformat(),
            updated_at=datetime.now(UTC).isoformat(),
        )

    def test_generate_key_deterministic(self, cache, sample_request):
        """Same request produces same cache key."""
        key1 = cache.generate_key(sample_request)
        key2 = cache.generate_key(sample_request)

        assert key1 == key2
        assert len(key1) == 64  # SHA256 hex length

    def test_generate_key_different_inputs(self, cache):
        """Different requests produce different cache keys."""
        request1 = NLaCRequest(
            idea="Create a function",
            context="Python",
            mode="nlac"
        )
        request2 = NLaCRequest(
            idea="Create a function",
            context="JavaScript",  # Different context
            mode="nlac"
        )

        key1 = cache.generate_key(request1)
        key2 = cache.generate_key(request2)

        assert key1 != key2

    def test_generate_key_mode_sensitive(self, cache):
        """Cache key is sensitive to mode parameter."""
        request_legacy = NLaCRequest(
            idea="Test",
            context="",
            mode="legacy"
        )
        request_nlac = NLaCRequest(
            idea="Test",
            context="",
            mode="nlac"
        )

        key_legacy = cache.generate_key(request_legacy)
        key_nlac = cache.generate_key(request_nlac)

        assert key_legacy != key_nlac

    @pytest.mark.asyncio
    async def test_cache_miss_returns_none(self, cache, sample_request):
        """Cache miss returns None."""
        result = await cache.get(sample_request)
        assert result is None

    @pytest.mark.asyncio
    async def test_cache_put_and_get(self, cache, sample_request, sample_prompt):
        """Can store and retrieve cached prompt."""
        # Store in cache
        await cache.put(sample_request, sample_prompt)

        # Retrieve from cache
        result = await cache.get(sample_request)

        assert result is not None
        assert result.id == sample_prompt.id
        assert result.template == sample_prompt.template

    @pytest.mark.asyncio
    async def test_cache_hit_updates_stats(self, cache, sample_request, sample_prompt):
        """Cache hit updates hit_count and last_accessed."""
        await cache.put(sample_request, sample_prompt)

        # First access
        result1 = await cache.get(sample_request)
        first_accessed = cache._memory_cache[cache.generate_key(sample_request)]["last_accessed"]

        # Second access
        result2 = await cache.get(sample_request)
        entry = cache._memory_cache[cache.generate_key(sample_request)]

        assert entry["hit_count"] == 2  # Accessed twice
        assert entry["last_accessed"] >= first_accessed  # Timestamp updated

    @pytest.mark.asyncio
    async def test_cache_invalidate(self, cache, sample_request, sample_prompt):
        """Can invalidate cached entry."""
        await cache.put(sample_request, sample_prompt)

        # Verify cached
        result = await cache.get(sample_request)
        assert result is not None

        # Invalidate
        deleted = await cache.invalidate(sample_request)
        assert deleted is True

        # Verify gone
        result = await cache.get(sample_request)
        assert result is None

    @pytest.mark.asyncio
    async def test_invalidate_nonexistent_returns_false(self, cache, sample_request):
        """Invalidating non-existent entry returns False."""
        deleted = await cache.invalidate(sample_request)
        assert deleted is False

    @pytest.mark.asyncio
    async def test_get_stats_empty_cache(self, cache):
        """Stats for empty cache."""
        stats = await cache.get_stats()

        assert stats["total_entries"] == 0
        assert stats["total_hits"] == 0
        assert stats["avg_hit_count"] == 0

    @pytest.mark.asyncio
    async def test_get_stats_with_entries(self, cache, sample_request, sample_prompt):
        """Stats reflect cache contents."""
        # Add multiple entries
        await cache.put(sample_request, sample_prompt)

        request2 = NLaCRequest(idea="Different", context="Test", mode="nlac")
        prompt2 = PromptObject(
            id="test-456",
            version="1.0.0",
            intent_type=IntentType.GENERATE,
            template="Different template",
            strategy_meta={},
            constraints={},
            created_at=datetime.now(UTC).isoformat(),
            updated_at=datetime.now(UTC).isoformat(),
        )
        await cache.put(request2, prompt2)

        # Access first one twice
        await cache.get(sample_request)
        await cache.get(sample_request)

        # Access second one once
        await cache.get(request2)

        stats = await cache.get_stats()

        assert stats["total_entries"] == 2
        assert stats["total_hits"] == 3  # 2 + 1
        assert stats["avg_hit_count"] == 1.5  # 3 / 2

    @pytest.mark.asyncio
    async def test_clear_cache(self, cache, sample_request, sample_prompt):
        """Can clear all cache entries."""
        # Add entries
        await cache.put(sample_request, sample_prompt)

        request2 = NLaCRequest(idea="Another", context="Test", mode="nlac")
        prompt2 = PromptObject(
            id="test-456",
            version="1.0.0",
            intent_type=IntentType.GENERATE,
            template="Another template",
            strategy_meta={},
            constraints={},
            created_at=datetime.now(UTC).isoformat(),
            updated_at=datetime.now(UTC).isoformat(),
        )
        await cache.put(request2, prompt2)

        # Clear
        cleared = await cache.clear()
        assert cleared == 2

        # Verify empty
        result = await cache.get(sample_request)
        assert result is None

    @pytest.mark.asyncio
    async def test_cache_overwrite(self, cache, sample_request):
        """Putting same request twice overwrites cache."""
        prompt1 = PromptObject(
            id="test-1",
            version="1.0.0",
            intent_type=IntentType.GENERATE,
            template="First version",
            strategy_meta={},
            constraints={},
            created_at=datetime.now(UTC).isoformat(),
            updated_at=datetime.now(UTC).isoformat(),
        )

        prompt2 = PromptObject(
            id="test-2",
            version="1.0.0",
            intent_type=IntentType.GENERATE,
            template="Second version",
            strategy_meta={},
            constraints={},
            created_at=datetime.now(UTC).isoformat(),
            updated_at=datetime.now(UTC).isoformat(),
        )

        await cache.put(sample_request, prompt1)
        await cache.put(sample_request, prompt2)

        result = await cache.get(sample_request)
        assert result.id == "test-2"  # Second version overwrote first
        assert result.template == "Second version"

    def test_sha256_key_format(self, cache, sample_request):
        """Cache key is valid SHA256 hex string."""
        key = cache.generate_key(sample_request)

        # SHA256 produces 64 hex characters
        assert len(key) == 64
        assert all(c in "0123456789abcdef" for c in key)
