#!/usr/bin/env python3
"""Metrics port for domain layer - hexagonal architecture."""
from typing import Protocol


class MetricsPort(Protocol):
    """Metrics collection interface for domain layer.

    This port defines the contract for metrics collection in the hexagonal
    architecture. The domain layer records metrics through this interface,
    while infrastructure provides concrete implementations.

    Methods:
        record_knn_hit: Record KNN query with usage stats
        record_ifeval_result: Record IFEval validation result
        record_latency: Record operation latency
        record_cache_hit: Record cache hit/miss
        get_knn_hit_rate: Get KNN embedding usage rate
        get_cache_hit_rate: Get cache hit rate
    """

    def record_knn_hit(self, used_embeddings: bool, query: str) -> None:
        """Record KNN query with usage stats.

        Args:
            used_embeddings: True if DSPy embeddings were used, False if bigrams
            query: Query string for analytics
        """
        ...

    def record_ifeval_result(self, score: float, passed: bool, prompt_id: str) -> None:
        """Record IFEval validation result.

        Args:
            score: Total score (0.0 - 1.0)
            passed: Whether validation passed threshold
            prompt_id: ID of validated prompt
        """
        ...

    def record_latency(self, operation: str, duration_ms: float) -> None:
        """Record operation latency.

        Args:
            operation: Operation name (e.g., 'knn_find_examples', 'nlac_build')
            duration_ms: Duration in milliseconds
        """
        ...

    def record_cache_hit(self, hit: bool, key: str) -> None:
        """Record cache hit/miss.

        Args:
            hit: True if cache hit, False if miss
            key: Cache key (hashed for privacy)
        """
        ...

    def get_knn_hit_rate(self, time_window: str = "24h") -> float:
        """Get KNN embedding usage rate.

        Args:
            time_window: Time window (e.g., '24h', '7d')

        Returns:
            Fraction of queries using embeddings (0.0 - 1.0)
        """
        ...

    def get_cache_hit_rate(self, time_window: str = "24h") -> float:
        """Get cache hit rate.

        Args:
            time_window: Time window (e.g., '24h', '7d')

        Returns:
            Fraction of cache hits (0.0 - 1.0)
        """
        ...
