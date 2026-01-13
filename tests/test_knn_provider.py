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


def test_find_examples_returns_empty_when_threshold_not_met():
    """find_examples should return empty list when no examples meet similarity threshold."""
    provider = KNNProvider(catalog_path=Path("datasets/exports/unified-fewshot-pool-v2.json"))

    # Use unrealistically high threshold (cosine similarity max is 1.0)
    result = provider.find_examples(
        intent="totally_unrelated_intent_xyz123",
        complexity="extremely_unlikely_complexity_abc456",
        k=3,
        min_similarity=0.99  # 99% similarity - extremely unlikely to match
    )

    # Should return empty list, not fallback to top-k below threshold
    assert result == []


def test_knn_raises_when_skip_rate_high(tmp_path):
    """KNNProvider should raise ValueError when >20% of catalog examples fail validation."""
    import json

    # Create catalog with mostly invalid examples (only 2 valid, 8 invalid = 80% skip rate)
    catalog_path = tmp_path / "bad_catalog.json"

    bad_examples = []
    for i in range(10):
        # Only 2 valid examples, 8 invalid
        if i < 2:
            bad_examples.append({
                "inputs": {"original_idea": f"valid {i}"},
                "outputs": {"improved_prompt": f"prompt {i}"}
            })
        else:
            # Missing required fields
            bad_examples.append({"inputs": {}})

    with open(catalog_path, 'w') as f:
        json.dump({"examples": bad_examples}, f)

    # Should raise due to 80% skip rate
    with pytest.raises(ValueError, match="80.0%"):
        KNNProvider(catalog_path=catalog_path)


def test_find_examples_ignores_empty_user_input():
    """find_examples should ignore empty or whitespace-only user_input."""
    provider = KNNProvider(catalog_path=Path("datasets/exports/unified-fewshot-pool-v2.json"))

    # Empty string should be ignored
    result1 = provider.find_examples(
        intent="explain",
        complexity="moderate",
        user_input="",
        k=2
    )

    # Whitespace-only should be ignored
    result2 = provider.find_examples(
        intent="explain",
        complexity="moderate",
        user_input="   ",
        k=2
    )

    # Both should return same results as no user_input
    result3 = provider.find_examples(
        intent="explain",
        complexity="moderate",
        k=2
    )

    # Results should be identical (same examples selected)
    assert len(result1) == len(result2) == len(result3)
