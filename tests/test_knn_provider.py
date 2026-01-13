"""
Tests for KNNProvider service.

Tests ComponentCatalog integration using semantic search.
"""
import pytest
from pathlib import Path
from hemdov.domain.services.knn_provider import KNNProvider, FewShotExample


def test_knn_provider_initializes():
    """KNNProvider should load catalog from path"""
    provider = KNNProvider(catalog_path=Path("datasets/exports/unified-fewshot-pool-v2.json"))
    assert provider.catalog is not None
    assert len(provider.catalog) > 0


def test_knn_provider_finds_similar_examples():
    """KNNProvider should find k similar examples using semantic search"""
    provider = KNNProvider(catalog_path=Path("datasets/exports/unified-fewshot-pool-v2.json"))

    examples = provider.find_examples(
        intent="debug",
        complexity="simple",
        k=3
    )

    assert len(examples) == 3
    assert all(isinstance(ex, FewShotExample) for ex in examples)


def test_knn_provider_filters_by_expected_output():
    """
    KNNProvider should filter examples that have expected_output.

    Note: Current catalog may not have examples with expected_output,
    so this test verifies the filter mechanism works.
    """
    provider = KNNProvider(catalog_path=Path("datasets/exports/unified-fewshot-pool-v2.json"))

    # First, check if any examples have expected_output
    examples_with_output = [ex for ex in provider.catalog if ex.expected_output is not None]

    if not examples_with_output:
        # Skip test if catalog doesn't have expected_output examples
        pytest.skip("Catalog has no examples with expected_output")

    examples = provider.find_examples(
        intent="refactor",
        complexity="moderate",
        k=3,
        has_expected_output=True  # CRITICAL for MultiAIGCD Scenario III
    )

    assert len(examples) == 3
    # All examples should have expected_output field
    assert all(ex.expected_output is not None for ex in examples)


def test_knn_provider_returns_examples_for_any_query():
    """
    KNNProvider should return k examples for any query using semantic similarity.

    Note: Since catalog doesn't have intent/complexity metadata,
    filtering is done by semantic similarity only.
    """
    provider = KNNProvider(catalog_path=Path("datasets/exports/unified-fewshot-pool-v2.json"))

    examples = provider.find_examples(
        intent="any_intent",
        complexity="any_complexity",
        k=3
    )

    # Should return k examples based on semantic similarity
    assert len(examples) == 3
    assert all(isinstance(ex, FewShotExample) for ex in examples)


def test_knn_provider_raises_when_no_examples():
    """KNNProvider should raise ValueError when catalog has no valid examples."""
    import tempfile
    import json

    # Create temporary catalog with no valid examples
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        empty_catalog = {
            "examples": [
                {
                    "inputs": {"original_idea": "test"},
                    # Missing 'outputs' key - will be skipped
                }
            ]
        }
        json.dump(empty_catalog, f)
        catalog_path = Path(f.name)

    try:
        # Should raise ValueError when all examples fail validation
        with pytest.raises(ValueError, match="No valid examples found"):
            KNNProvider(catalog_path=catalog_path)
    finally:
        catalog_path.unlink()


def test_find_examples_raises_when_vectorizer_none(monkeypatch):
    """find_examples should raise RuntimeError when vectorizer is None."""
    provider = KNNProvider(catalog_path=Path("datasets/exports/unified-fewshot-pool-v2.json"))

    # Mock vectorizer to None to simulate initialization failure
    monkeypatch.setattr(provider, '_vectorizer', None)

    # Should raise RuntimeError, not return first-k examples
    with pytest.raises(RuntimeError, match="vectorizer not initialized"):
        provider.find_examples(intent="explain", complexity="moderate", k=3)
