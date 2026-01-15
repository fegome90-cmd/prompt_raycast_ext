#!/usr/bin/env python3
"""Vectorizer port for domain layer - hexagonal architecture."""
from typing import Protocol

import numpy as np


class VectorizerPort(Protocol):
    """Vectorizer interface for domain layer.

    This port defines the contract for text vectorization in the hexagonal
    architecture. Supports hybrid vectorization with router pattern:
    - DSPy mode: Uses Ollama embeddings (768 dimensions)
    - Bigram mode: Uses character bigrams for semantic search

    Methods:
        mode: Get current vectorizer mode
        __call__: Vectorize texts
        get_catalog_vectors: Get pre-computed catalog vectors
        get_usage_stats: Get vectorizer usage statistics
    """

    @property
    def mode(self) -> str:
        """Return current vectorizer mode ('dspy' or 'bigram').

        Returns:
            'dspy' if using DSPy/Ollama embeddings, 'bigram' if using character bigrams
        """
        ...

    def __call__(self, texts: list[str]) -> np.ndarray:
        """Vectorize texts.

        Args:
            texts: List of text strings to vectorize

        Returns:
            Array of shape (len(texts), embedding_dim)
        """
        ...

    def get_catalog_vectors(self) -> np.ndarray:
        """Get pre-computed catalog vectors.

        Returns:
            Cached catalog vectors (shape: [catalog_size, embedding_dim])
        """
        ...

    def get_usage_stats(self) -> dict:
        """Get vectorizer usage statistics.

        Returns:
            Dict with 'dspy_usage_count', 'bigram_usage_count', 'total_queries'
        """
        ...
