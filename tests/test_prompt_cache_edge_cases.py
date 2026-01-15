"""
Edge case and error condition tests for PromptCache.

Tests cover:
- Repository failure scenarios
- Concurrent access patterns
- Cache key edge cases
- Memory overflow scenarios
- Error recovery
"""

import asyncio
from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest

from hemdov.domain.dto.nlac_models import IntentType, NLaCRequest, PromptObject
from hemdov.domain.services.prompt_cache import PromptCache


class TestPromptCacheEdgeCases:
    """Test edge cases in PromptCache."""

    @pytest.fixture
    def mock_repository(self):
        """Create mock repository."""
        repo = AsyncMock()
        repo.get_cached_prompt = AsyncMock(return_value=None)
        repo.cache_prompt = AsyncMock()
        repo.delete_cached_prompt = AsyncMock(return_value=False)
        repo.update_cache_access = AsyncMock()
        repo.get_cache_stats = AsyncMock(return_value={})
        repo.clear_cache = AsyncMock(return_value=0)
        return repo

    @pytest.fixture
    def cache(self, mock_repository):
        """Create cache with mock repository."""
        return PromptCache(repository=mock_repository)

    @pytest.fixture
    def memory_cache(self):
        """Create in-memory only cache."""
        return PromptCache(repository=None)

    @pytest.fixture
    def sample_request(self):
        """Create sample NLaCRequest."""
        return NLaCRequest(
            idea="Create a function",
            context="Python",
            mode="nlac"
        )

    @pytest.fixture
    def sample_prompt(self):
        """Create sample PromptObject."""
        return PromptObject(
            id="test-123",
            version="1.0.0",
            intent_type=IntentType.GENERATE,
            template="You are a Developer.\n\nCreate a function.",
            strategy_meta={"strategy": "simple"},
            constraints={"max_tokens": 500},
            created_at=datetime.now(UTC).isoformat(),
            updated_at=datetime.now(UTC).isoformat(),
        )

    # ========================================================================
    # CACHE KEY EDGE CASES
    # ========================================================================

    def test_cache_key_with_unicode(self, memory_cache):
        """Unicode characters in cache key should be handled."""
        request = NLaCRequest(
            idea="创建函数",  # Chinese: "Create function"
            context="Python",
            mode="nlac"
        )
        key = memory_cache.generate_key(request)
        # Should produce valid SHA256
        assert len(key) == 64
        assert all(c in "0123456789abcdef" for c in key)

    def test_cache_key_with_emoji(self, memory_cache):
        """Emoji in cache key should be handled."""
        request = NLaCRequest(
            idea="Fix bug 🐛",
            context="",
            mode="nlac"
        )
        key = memory_cache.generate_key(request)
        assert len(key) == 64

    def test_cache_key_with_newlines(self, memory_cache):
        """Newlines and special chars in cache key."""
        request = NLaCRequest(
            idea="Create\n\na\n\nfunction\n\n",
            context="",
            mode="nlac"
        )
        key1 = memory_cache.generate_key(request)
        key2 = memory_cache.generate_key(request)
        # Same input should produce same key
        assert key1 == key2

    def test_cache_key_very_long_input(self, memory_cache):
        """Very long input should still produce valid key."""
        long_idea = "a" * 100000
        request = NLaCRequest(
            idea=long_idea,
            context="",
            mode="nlac"
        )
        key = memory_cache.generate_key(request)
        assert len(key) == 64

    def test_cache_key_none_context(self, memory_cache):
        """Empty context should be handled in cache key."""
        # NLaCRequest has default="" for context
        request = NLaCRequest(
            idea="Test",
            context="",  # Empty string, not None
            mode="nlac"
        )
        # Should not raise
        key = memory_cache.generate_key(request)
        assert len(key) == 64

    def test_cache_key_empty_all_fields(self, memory_cache):
        """Empty context should still produce valid key (idea cannot be empty)."""
        # NLaCRequest validation rejects empty idea
        # So we test with minimal valid input
        request = NLaCRequest(
            idea="x",  # Minimal non-empty idea
            context="",
            mode="nlac"
        )
        key = memory_cache.generate_key(request)
        assert len(key) == 64

    def test_cache_key_determinism_across_calls(self, memory_cache):
        """Cache key must be deterministic across multiple calls."""
        request = NLaCRequest(
            idea="Test idea",
            context="Test context",
            mode="nlac"
        )
        keys = [memory_cache.generate_key(request) for _ in range(100)]
        # All keys should be identical
        assert len(set(keys)) == 1

    # ========================================================================
    # REPOSITORY FAILURE SCENARIOS
    # ========================================================================

    @pytest.mark.asyncio
    async def test_repository_exception_on_get(self, mock_repository):
        """Repository exception on get should fallback to memory."""
        mock_repository.get_cached_prompt.side_effect = Exception("DB down")

        cache = PromptCache(repository=mock_repository)
        request = NLaCRequest(idea="Test", context="", mode="nlac")

        # Should not raise, should return None (cache miss)
        result = await cache.get(request)
        assert result is None

    @pytest.mark.asyncio
    async def test_repository_exception_on_put(self, mock_repository, sample_request, sample_prompt):
        """Repository exception on put should fallback to memory."""
        mock_repository.cache_prompt.side_effect = Exception("Write failed")

        cache = PromptCache(repository=mock_repository)

        # Should not raise, should fallback to memory
        await cache.put(sample_request, sample_prompt)

        # Verify it's in memory cache
        key = cache.generate_key(sample_request)
        assert key in cache._memory_cache

    @pytest.mark.asyncio
    async def test_repository_exception_on_invalidate(self, mock_repository, sample_request, sample_prompt):
        """Repository exception on invalidate should try memory."""
        mock_repository.delete_cached_prompt.side_effect = Exception("Delete failed")

        cache = PromptCache(repository=mock_repository)

        # Put to memory cache (repository will fail)
        await cache.put(sample_request, sample_prompt)

        # Invalidate should fall back to memory cache
        deleted = await cache.invalidate(sample_request)
        # Memory cache should have it and deletion should succeed
        assert deleted is True

    @pytest.mark.asyncio
    async def test_repository_exception_on_stats(self, mock_repository):
        """Repository exception on stats should fallback to memory stats."""
        mock_repository.get_cache_stats.side_effect = Exception("Stats failed")
        mock_repository.cache_prompt.side_effect = Exception("Write failed")

        cache = PromptCache(repository=mock_repository)
        request = NLaCRequest(idea="Test", context="", mode="nlac")
        prompt = PromptObject(
            id="1",
            version="1.0",
            intent_type=IntentType.GENERATE,
            template="Test",
            strategy_meta={},
            constraints={},
            created_at=datetime.now(UTC).isoformat(),
            updated_at=datetime.now(UTC).isoformat(),
        )

        # Put will fail to repository and fallback to memory
        await cache.put(request, prompt)
        stats = await cache.get_stats()

        # Should return memory stats
        assert stats["total_entries"] == 1

    @pytest.mark.asyncio
    async def test_repository_exception_on_clear(self, mock_repository, sample_request, sample_prompt):
        """Repository exception on clear should still clear memory."""
        mock_repository.clear_cache.side_effect = Exception("Clear failed")
        mock_repository.cache_prompt.side_effect = Exception("Write failed")

        cache = PromptCache(repository=mock_repository)

        # Put will fallback to memory
        await cache.put(sample_request, sample_prompt)

        # Should not raise, should clear memory at least
        cleared = await cache.clear()
        assert cleared >= 1  # At least memory entry cleared

    # ========================================================================
    # MEMORY CACHE OVERFLOW
    # ========================================================================

    @pytest.mark.asyncio
    async def test_large_number_of_entries(self, memory_cache):
        """Cache should handle many entries."""
        count = 1000
        prompts = []

        for i in range(count):
            request = NLaCRequest(
                idea=f"Idea {i}",
                context=f"Context {i}",
                mode="nlac"
            )
            prompt = PromptObject(
                id=f"prompt-{i}",
                version="1.0.0",
                intent_type=IntentType.GENERATE,
                template=f"Template {i}",
                strategy_meta={},
                constraints={},
                created_at=datetime.now(UTC).isoformat(),
                updated_at=datetime.now(UTC).isoformat(),
            )
            await memory_cache.put(request, prompt)
            prompts.append((request, prompt))

        # All should be retrievable
        for request, original_prompt in prompts:
            retrieved = await memory_cache.get(request)
            assert retrieved is not None
            assert retrieved.id == original_prompt.id

    @pytest.mark.asyncio
    async def test_cache_with_large_prompt_object(self, memory_cache, sample_request):
        """Cache should handle large prompt templates."""
        large_template = "This is a very long prompt template. " * 10000  # ~330KB
        large_prompt = PromptObject(
            id="large",
            version="1.0.0",
            intent_type=IntentType.GENERATE,
            template=large_template,
            strategy_meta={"large": True},
            constraints={"max_tokens": 1000000},
            created_at=datetime.now(UTC).isoformat(),
            updated_at=datetime.now(UTC).isoformat(),
        )

        await memory_cache.put(sample_request, large_prompt)
        retrieved = await memory_cache.get(sample_request)

        assert retrieved is not None
        assert len(retrieved.template) == len(large_template)

    # ========================================================================
    # CONCURRENT ACCESS
    # ========================================================================

    @pytest.mark.asyncio
    async def test_concurrent_gets(self, memory_cache, sample_request, sample_prompt):
        """Concurrent gets should be thread-safe."""
        await memory_cache.put(sample_request, sample_prompt)

        # Launch many concurrent gets
        tasks = [memory_cache.get(sample_request) for _ in range(100)]
        results = await asyncio.gather(*tasks)

        # All should succeed
        assert all(r is not None for r in results)
        assert all(r.id == sample_prompt.id for r in results)

    @pytest.mark.asyncio
    async def test_concurrent_puts(self, memory_cache):
        """Concurrent puts to different keys should be safe."""
        tasks = []
        for i in range(100):
            request = NLaCRequest(
                idea=f"Idea {i}",
                context=f"Context {i}",
                mode="nlac"
            )
            prompt = PromptObject(
                id=f"prompt-{i}",
                version="1.0.0",
                intent_type=IntentType.GENERATE,
                template=f"Template {i}",
                strategy_meta={},
                constraints={},
                created_at=datetime.now(UTC).isoformat(),
                updated_at=datetime.now(UTC).isoformat(),
            )
            tasks.append(memory_cache.put(request, prompt))

        await asyncio.gather(*tasks)

        # All should be cached
        stats = await memory_cache.get_stats()
        assert stats["total_entries"] == 100

    @pytest.mark.asyncio
    async def test_concurrent_overwrites(self, memory_cache, sample_request):
        """Consecutive overwrites of same key should be safe."""
        tasks = []
        for i in range(100):
            prompt = PromptObject(
                id=f"prompt-{i}",
                version="1.0.0",
                intent_type=IntentType.GENERATE,
                template=f"Version {i}",
                strategy_meta={},
                constraints={},
                created_at=datetime.now(UTC).isoformat(),
                updated_at=datetime.now(UTC).isoformat(),
            )
            tasks.append(memory_cache.put(sample_request, prompt))

        await asyncio.gather(*tasks)

        # Last write should win
        result = await memory_cache.get(sample_request)
        assert result.id == "prompt-99"

    @pytest.mark.asyncio
    async def test_concurrent_invalidates(self, memory_cache, sample_request, sample_prompt):
        """Concurrent invalidates should be safe."""
        await memory_cache.put(sample_request, sample_prompt)

        # Multiple concurrent invalidates
        tasks = [memory_cache.invalidate(sample_request) for _ in range(10)]
        results = await asyncio.gather(*tasks)

        # First should return True, rest False
        assert results[0] is True
        assert all(r is False for r in results[1:])

    # ========================================================================
    # CACHE STATISTICS EDGE CASES
    # ========================================================================

    @pytest.mark.asyncio
    async def test_stats_division_by_zero(self, memory_cache):
        """Stats should handle empty cache without division by zero."""
        stats = await memory_cache.get_stats()
        assert stats["avg_hit_count"] == 0  # Should not raise ZeroDivisionError

    @pytest.mark.asyncio
    async def test_stats_with_zero_hits(self, memory_cache, sample_request, sample_prompt):
        """Entry with zero hits should be handled in stats."""
        await memory_cache.put(sample_request, sample_prompt)

        stats = await memory_cache.get_stats()
        assert stats["total_entries"] == 1
        assert stats["total_hits"] == 0
        assert stats["avg_hit_count"] == 0

    @pytest.mark.asyncio
    async def test_stats_after_multiple_accesses(self, memory_cache, sample_request, sample_prompt):
        """Stats should accurately track hit counts."""
        await memory_cache.put(sample_request, sample_prompt)

        # Access 5 times
        for _ in range(5):
            await memory_cache.get(sample_request)

        stats = await memory_cache.get_stats()
        assert stats["total_hits"] == 5
        assert stats["avg_hit_count"] == 5.0

    # ========================================================================
    # CACHE INVALIDATION EDGE CASES
    # ========================================================================

    @pytest.mark.asyncio
    async def test_invalidate_then_get(self, memory_cache, sample_request, sample_prompt):
        """Get after invalidate should return None."""
        await memory_cache.put(sample_request, sample_prompt)
        await memory_cache.invalidate(sample_request)

        result = await memory_cache.get(sample_request)
        assert result is None

    @pytest.mark.asyncio
    async def test_invalidate_nonexistent_from_empty_cache(self, memory_cache, sample_request):
        """Invalidating from empty cache should return False."""
        deleted = await memory_cache.invalidate(sample_request)
        assert deleted is False

    @pytest.mark.asyncio
    async def test_double_invalidate(self, memory_cache, sample_request, sample_prompt):
        """Double invalidate should be safe."""
        await memory_cache.put(sample_request, sample_prompt)

        first = await memory_cache.invalidate(sample_request)
        second = await memory_cache.invalidate(sample_request)

        assert first is True
        assert second is False

    # ========================================================================
    # CLEAR CACHE EDGE CASES
    # ========================================================================

    @pytest.mark.asyncio
    async def test_clear_empty_cache(self, memory_cache):
        """Clearing empty cache should return 0."""
        cleared = await memory_cache.clear()
        assert cleared == 0

    @pytest.mark.asyncio
    async def test_clear_then_stats(self, memory_cache, sample_request, sample_prompt):
        """Stats after clear should show zero entries."""
        await memory_cache.put(sample_request, sample_prompt)
        await memory_cache.clear()

        stats = await memory_cache.get_stats()
        assert stats["total_entries"] == 0
        assert stats["total_hits"] == 0

    # ========================================================================
    # MEMORY vs REPOSITORY CONSISTENCY
    # ========================================================================

    @pytest.mark.asyncio
    async def test_repository_failure_fallback_to_memory_consistency(
        self, mock_repository, sample_request, sample_prompt
    ):
        """When repository fails, operations should be consistent with memory."""
        mock_repository.cache_prompt.side_effect = Exception("DB error")

        cache = PromptCache(repository=mock_repository)

        # Put should fallback to memory
        await cache.put(sample_request, sample_prompt)

        # Get should find it in memory
        result = await cache.get(sample_request)
        assert result is not None
        assert result.id == sample_prompt.id

        # Invalidate should work
        deleted = await cache.invalidate(sample_request)
        assert deleted is True

        # Get should return None
        result = await cache.get(sample_request)
        assert result is None


class TestPromptCacheWithRealRepositoryFailures:
    """Test cache behavior with realistic repository failure patterns."""

    @pytest.fixture
    def flaky_repository(self):
        """Create repository that fails intermittently."""
        repo = AsyncMock()
        call_count = {"get": 0, "put": 0}

        async def flaky_get(*args, **kwargs):
            call_count["get"] += 1
            if call_count["get"] % 3 == 0:  # Fail every 3rd call
                raise Exception("Connection timeout")
            return None

        async def flaky_put(*args, **kwargs):
            call_count["put"] += 1
            if call_count["put"] % 2 == 0:  # Fail every 2nd call
                raise Exception("Write timeout")

        repo.get_cached_prompt = flaky_get
        repo.cache_prompt = flaky_put
        repo.delete_cached_prompt = AsyncMock(return_value=False)
        repo.update_cache_access = AsyncMock()
        repo.get_cache_stats = AsyncMock(side_effect=Exception("Stats error"))
        repo.clear_cache = AsyncMock(side_effect=Exception("Clear error"))

        return repo

    @pytest.mark.asyncio
    async def test_cache_resilient_to_flaky_repository(self, flaky_repository):
        """Cache should remain functional despite repository failures."""
        cache = PromptCache(repository=flaky_repository)

        request = NLaCRequest(idea="Test", context="", mode="nlac")
        prompt = PromptObject(
            id="1",
            version="1.0",
            intent_type=IntentType.GENERATE,
            template="Test",
            strategy_meta={},
            constraints={},
            created_at=datetime.now(UTC).isoformat(),
            updated_at=datetime.now(UTC).isoformat(),
        )

        # Try multiple puts - should fallback to memory
        for i in range(5):
            await cache.put(request, prompt)

        # Should be retrievable from memory
        result = await cache.get(request)
        assert result is not None

        # Stats should work (from memory)
        stats = await cache.get_stats()
        assert stats["total_entries"] >= 1


class TestPromptCacheTimestampEdgeCases:
    """Test timestamp handling edge cases."""

    @pytest.fixture
    def memory_cache(self):
        """Create in-memory cache."""
        return PromptCache(repository=None)

    @pytest.mark.asyncio
    async def test_last_accessed_updates(self, memory_cache):
        """last_accessed should update on each access."""
        request = NLaCRequest(idea="Test", context="", mode="nlac")
        prompt = PromptObject(
            id="1",
            version="1.0",
            intent_type=IntentType.GENERATE,
            template="Test",
            strategy_meta={},
            constraints={},
            created_at=datetime.now(UTC).isoformat(),
            updated_at=datetime.now(UTC).isoformat(),
        )

        await memory_cache.put(request, prompt)
        key = memory_cache.generate_key(request)

        first_accessed = memory_cache._memory_cache[key]["last_accessed"]

        # Wait a bit and access again
        import asyncio
        await asyncio.sleep(0.01)

        await memory_cache.get(request)
        second_accessed = memory_cache._memory_cache[key]["last_accessed"]

        assert second_accessed > first_accessed

    @pytest.mark.asyncio
    async def test_created_at_remains_constant(self, memory_cache):
        """created_at should not change on access."""
        request = NLaCRequest(idea="Test", context="", mode="nlac")
        prompt = PromptObject(
            id="1",
            version="1.0",
            intent_type=IntentType.GENERATE,
            template="Test",
            strategy_meta={},
            constraints={},
            created_at=datetime.now(UTC).isoformat(),
            updated_at=datetime.now(UTC).isoformat(),
        )

        await memory_cache.put(request, prompt)
        key = memory_cache.generate_key(request)

        created_at = memory_cache._memory_cache[key]["created_at"]

        # Access multiple times
        for _ in range(5):
            await memory_cache.get(request)

        # created_at should remain the same
        assert memory_cache._memory_cache[key]["created_at"] == created_at
