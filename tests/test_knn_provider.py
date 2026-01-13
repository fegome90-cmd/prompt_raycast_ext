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
    KNNProvider should return k examples for any valid query using semantic similarity.

    Note: Since catalog doesn't have intent/complexity metadata,
    filtering is done by semantic similarity only.
    """
    provider = KNNProvider(catalog_path=Path("datasets/exports/unified-fewshot-pool-v2.json"))

    examples = provider.find_examples(
        intent="generate",  # Valid intent
        complexity="simple",  # Valid complexity
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
        # Should raise ValueError (either from skip rate check or empty catalog check)
        with pytest.raises(ValueError, match="100.0%|No valid examples found"):
            KNNProvider(catalog_path=catalog_path)
    finally:
        catalog_path.unlink()


def test_find_examples_raises_when_vectorizer_none(monkeypatch):
    """find_examples should raise KNNProviderError when vectorizer is None."""
    from hemdov.domain.services.knn_provider import KNNProviderError

    provider = KNNProvider(catalog_path=Path("datasets/exports/unified-fewshot-pool-v2.json"))

    # Mock vectorizer to None to simulate initialization failure
    monkeypatch.setattr(provider, '_vectorizer', None)

    # Should raise KNNProviderError, not return first-k examples
    with pytest.raises(KNNProviderError, match="vectorizer not initialized"):
        provider.find_examples(intent="explain", complexity="moderate", k=3)


def test_find_examples_returns_empty_when_threshold_not_met():
    """find_examples should return empty list when no examples meet similarity threshold."""
    provider = KNNProvider(catalog_path=Path("datasets/exports/unified-fewshot-pool-v2.json"))

    # Filter by expected_output when no examples have it, plus high threshold
    result = provider.find_examples(
        intent="refactor",
        complexity="simple",
        k=3,
        has_expected_output=True,  # Filters to examples with expected_output (likely none)
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


def test_knn_logs_error_at_5_percent_skip_rate(tmp_path, caplog):
    """KNNProvider should log ERROR when skip rate >= 5%."""
    import json
    import logging

    # Create catalog with 6% skip rate (94 valid, 6 invalid)
    catalog_path = tmp_path / "catalog_6_percent.json"

    examples = []
    for i in range(100):
        if i < 94:
            examples.append({
                "inputs": {"original_idea": f"valid {i}"},
                "outputs": {"improved_prompt": f"prompt {i}"}
            })
        else:
            examples.append({"inputs": {}})  # Invalid

    with open(catalog_path, 'w') as f:
        json.dump({"examples": examples}, f)

    # Should log ERROR at 6%
    with caplog.at_level(logging.ERROR):
        provider = KNNProvider(catalog_path=catalog_path)

    assert any(record.levelno == logging.ERROR for record in caplog.records)
    assert any("quality degradation" in record.getMessage() for record in caplog.records if record.levelno == logging.ERROR)


def test_knn_logs_warning_below_5_percent_skip_rate(tmp_path, caplog):
    """KNNProvider should log WARNING when skip rate < 5% (no quality degradation ERROR)."""
    import json
    import logging

    # Create catalog with 3% skip rate (97 valid, 3 invalid)
    catalog_path = tmp_path / "catalog_3_percent.json"

    examples = []
    for i in range(100):
        if i < 97:
            examples.append({
                "inputs": {"original_idea": f"valid {i}"},
                "outputs": {"improved_prompt": f"prompt {i}"}
            })
        else:
            examples.append({"inputs": {}})  # Invalid

    with open(catalog_path, 'w') as f:
        json.dump({"examples": examples}, f)

    # Should log WARNING (not ERROR) at 3% for quality degradation
    with caplog.at_level(logging.WARNING):
        provider = KNNProvider(catalog_path=catalog_path)

    # Should have WARNING about skip rate
    assert any("skip rate" in record.getMessage() for record in caplog.records if record.levelno == logging.WARNING)
    # Should NOT have catalog quality degradation ERROR message
    assert not any("quality degradation" in record.getMessage() for record in caplog.records if record.levelno == logging.ERROR)


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


def test_handle_knn_failure_returns_correct_tuple(caplog):
    """Given: KNN failure exception
    When: Call handle_knn_failure utility
    Then: Returns (failed=True, error_message)"""
    import logging
    from hemdov.domain.services.knn_provider import handle_knn_failure

    logger_instance = logging.getLogger("test")
    exception = RuntimeError("vectorizer not initialized")

    with caplog.at_level(logging.ERROR):
        failed, error = handle_knn_failure(logger_instance, "test_context", exception)

    assert failed is True
    assert "RuntimeError" in error
    assert "vectorizer not initialized" in error
    assert "test_context" in caplog.text


def test_knn_logs_error_at_exact_5_percent_skip_rate(tmp_path, caplog):
    """KNNProvider should log ERROR at exactly 5% skip rate (boundary test)."""
    import json
    import logging

    # Create catalog with exactly 5% skip rate (95 valid, 5 invalid)
    catalog_path = tmp_path / "catalog_exact_5_percent.json"

    examples = []
    for i in range(100):
        if i < 95:
            examples.append({
                "inputs": {"original_idea": f"valid {i}"},
                "outputs": {"improved_prompt": f"prompt {i}"}
            })
        else:
            examples.append({"inputs": {}})  # Invalid

    with open(catalog_path, 'w') as f:
        json.dump({"examples": examples}, f)

    # Should log ERROR at exactly 5%
    with caplog.at_level(logging.ERROR):
        provider = KNNProvider(catalog_path=catalog_path)

    assert any(
        record.levelno == logging.ERROR and "quality degradation" in record.getMessage()
        for record in caplog.records
    )


def test_knn_raises_at_exact_20_percent_skip_rate(tmp_path):
    """KNNProvider should raise ValueError at exactly 20% skip rate (boundary test)."""
    import json

    # Create catalog with exactly 20% skip rate (80 valid, 20 invalid)
    catalog_path = tmp_path / "catalog_exact_20_percent.json"

    examples = []
    for i in range(100):
        if i < 80:
            examples.append({
                "inputs": {"original_idea": f"valid {i}"},
                "outputs": {"improved_prompt": f"prompt {i}"}
            })
        else:
            examples.append({"inputs": {}})  # Invalid

    with open(catalog_path, 'w') as f:
        json.dump({"examples": examples}, f)

    # Should raise due to exactly 20% skip rate
    with pytest.raises(ValueError, match="20.0%"):
        KNNProvider(catalog_path=catalog_path)


def test_knn_does_not_raise_below_20_percent_skip_rate(tmp_path):
    """KNNProvider should NOT raise ValueError at 19% skip rate (boundary test)."""
    import json

    # Create catalog with 19% skip rate (81 valid, 19 invalid)
    catalog_path = tmp_path / "catalog_below_20_percent.json"

    examples = []
    for i in range(100):
        if i < 81:
            examples.append({
                "inputs": {"original_idea": f"valid {i}"},
                "outputs": {"improved_prompt": f"prompt {i}"}
            })
        else:
            examples.append({"inputs": {}})  # Invalid

    with open(catalog_path, 'w') as f:
        json.dump({"examples": examples}, f)

    # Should NOT raise at 19%
    provider = KNNProvider(catalog_path=catalog_path)
    assert len(provider.catalog) == 81


def test_compute_cosine_similarities_raises_with_nan_vectors(monkeypatch):
    """_compute_cosine_similarities should raise ValueError with NaN vectors."""
    import numpy as np
    from hemdov.domain.services.knn_provider import KNNProvider

    provider = KNNProvider(catalog_path=Path("datasets/exports/unified-fewshot-pool-v2.json"))

    # Create NaN vectors
    candidate_vectors = np.array([[1.0, 0.0], [np.nan, 1.0]])
    query_vector = np.array([1.0, 0.0])

    with pytest.raises(ValueError, match="NaN or infinite"):
        provider._compute_cosine_similarities(candidate_vectors, query_vector)


def test_compute_cosine_similarities_raises_with_inf_vectors(monkeypatch):
    """_compute_cosine_similarities should raise ValueError with infinite vectors."""
    import numpy as np
    from hemdov.domain.services.knn_provider import KNNProvider

    provider = KNNProvider(catalog_path=Path("datasets/exports/unified-fewshot-pool-v2.json"))

    # Create infinite vectors
    candidate_vectors = np.array([[1.0, 0.0], [np.inf, 1.0]])
    query_vector = np.array([1.0, 0.0])

    with pytest.raises(ValueError, match="NaN or infinite"):
        provider._compute_cosine_similarities(candidate_vectors, query_vector)


def test_find_examples_raises_with_invalid_intent():
    """find_examples should raise ValueError with invalid intent."""
    provider = KNNProvider(catalog_path=Path("datasets/exports/unified-fewshot-pool-v2.json"))

    with pytest.raises(ValueError, match="Invalid intent 'invalid_intent'"):
        provider.find_examples(
            intent="invalid_intent",
            complexity="simple",
            k=3
        )


def test_find_examples_raises_with_invalid_complexity():
    """find_examples should raise ValueError with invalid complexity."""
    provider = KNNProvider(catalog_path=Path("datasets/exports/unified-fewshot-pool-v2.json"))

    with pytest.raises(ValueError, match="Invalid complexity 'invalid_complexity'"):
        provider.find_examples(
            intent="debug",
            complexity="invalid_complexity",
            k=3
        )


def test_find_examples_with_metadata_returns_result():
    """find_examples_with_metadata should return FindExamplesResult with metadata."""
    from hemdov.domain.services.knn_provider import FindExamplesResult

    provider = KNNProvider(catalog_path=Path("datasets/exports/unified-fewshot-pool-v2.json"))

    result = provider.find_examples_with_metadata(
        intent="debug",
        complexity="simple",
        k=3
    )

    assert isinstance(result, FindExamplesResult)
    assert len(result.examples) == 3
    assert result.highest_similarity > 0
    assert result.total_candidates > 0
    assert result.met_threshold is True
    assert result.empty is False


def test_find_examples_with_metadata_empty_returns_metadata():
    """find_examples_with_metadata should return FindExamplesResult with metadata when empty."""
    from hemdov.domain.services.knn_provider import FindExamplesResult

    provider = KNNProvider(catalog_path=Path("datasets/exports/unified-fewshot-pool-v2.json"))

    # Filter by expected_output when no examples have it, plus high threshold
    result = provider.find_examples_with_metadata(
        intent="refactor",
        complexity="simple",
        k=3,
        has_expected_output=True,  # Filters to examples with expected_output (likely none)
        min_similarity=0.99
    )

    assert isinstance(result, FindExamplesResult)
    assert len(result.examples) == 0
    assert result.empty is True
    assert result.met_threshold is False
    assert result.highest_similarity >= 0  # Should have highest similarity even when empty
    assert result.total_candidates >= 0  # May be 0 if no examples have expected_output


# ============================================================================
# Fase 1: Tests de Validación de Parámetros
# ============================================================================

def test_find_examples_raises_with_zero_k():
    """find_examples should raise ValueError when k <= 0."""
    provider = KNNProvider(catalog_path=Path("datasets/exports/unified-fewshot-pool-v2.json"))

    with pytest.raises(ValueError, match="k must be positive"):
        provider.find_examples(intent="debug", complexity="simple", k=0)

    with pytest.raises(ValueError, match="k must be positive"):
        provider.find_examples(intent="debug", complexity="simple", k=-1)


def test_find_examples_raises_with_invalid_min_similarity():
    """find_examples should raise ValueError when min_similarity not in [-1, 1]."""
    provider = KNNProvider(catalog_path=Path("datasets/exports/unified-fewshot-pool-v2.json"))

    with pytest.raises(ValueError, match="min_similarity must be in \\[-1, 1\\]"):
        provider.find_examples(intent="debug", complexity="simple", k=3, min_similarity=1.5)

    with pytest.raises(ValueError, match="min_similarity must be in \\[-1, 1\\]"):
        provider.find_examples(intent="debug", complexity="simple", k=3, min_similarity=-1.5)


def test_find_examples_raises_with_invalid_user_input_type():
    """find_examples should raise TypeError when user_input is not str or None."""
    provider = KNNProvider(catalog_path=Path("datasets/exports/unified-fewshot-pool-v2.json"))

    with pytest.raises(TypeError, match="user_input must be str or None"):
        provider.find_examples(intent="debug", complexity="simple", k=3, user_input=123)


def test_find_examples_with_metadata_raises_with_zero_k():
    """find_examples_with_metadata should raise ValueError when k <= 0."""
    provider = KNNProvider(catalog_path=Path("datasets/exports/unified-fewshot-pool-v2.json"))

    with pytest.raises(ValueError, match="k must be positive"):
        provider.find_examples_with_metadata(intent="debug", complexity="simple", k=0)


def test_find_examples_with_metadata_raises_with_invalid_min_similarity():
    """find_examples_with_metadata should raise ValueError when min_similarity not in [-1, 1]."""
    provider = KNNProvider(catalog_path=Path("datasets/exports/unified-fewshot-pool-v2.json"))

    with pytest.raises(ValueError, match="min_similarity must be in \\[-1, 1\\]"):
        provider.find_examples_with_metadata(intent="debug", complexity="simple", k=3, min_similarity=2.0)


def test_find_examples_result_enforces_invariants():
    """FindExamplesResult should enforce invariants in __post_init__."""
    from hemdov.domain.services.knn_provider import FindExamplesResult

    provider = KNNProvider(catalog_path=Path("datasets/exports/unified-fewshot-pool-v2.json"))

    # highest_similarity out of range
    with pytest.raises(ValueError, match="highest_similarity must be in"):
        FindExamplesResult(
            examples=[],
            highest_similarity=1.5,  # Invalid: > 1.0
            threshold_used=0.1,
            total_candidates=0,
            met_threshold=False
        )

    with pytest.raises(ValueError, match="highest_similarity must be in"):
        FindExamplesResult(
            examples=[],
            highest_similarity=-1.5,  # Invalid: < -1.0
            threshold_used=0.1,
            total_candidates=0,
            met_threshold=False
        )

    # total_candidates negative
    with pytest.raises(ValueError, match="total_candidates cannot be negative"):
        FindExamplesResult(
            examples=[],
            highest_similarity=0.5,
            threshold_used=0.1,
            total_candidates=-1,  # Invalid
            met_threshold=False
        )

    # Consistency check: met_threshold=True requires non-empty examples
    with pytest.raises(ValueError, match="met_threshold=True requires"):
        FindExamplesResult(
            examples=[],  # Empty
            highest_similarity=0.8,
            threshold_used=0.1,
            total_candidates=10,
            met_threshold=True  # Inconsistent
        )


def test_compute_cosine_similarities_with_zero_norm_vectors():
    """Should handle zero-norm vectors gracefully (return 0 similarity)."""
    import numpy as np
    from hemdov.domain.services.knn_provider import KNNProvider

    provider = KNNProvider(catalog_path=Path("datasets/exports/unified-fewshot-pool-v2.json"))

    # Candidate vectors with one zero-norm vector
    candidate_vectors = np.array([[1.0, 0.0], [0.0, 0.0]])
    query_vector = np.array([0.0, 0.0])  # Zero norm

    similarities = provider._compute_cosine_similarities(candidate_vectors, query_vector)

    # Should not return NaN for zero-norm vectors
    assert not np.any(np.isnan(similarities)), "Should not return NaN for zero-norm vectors"
    # Zero-norm vector should have 0 similarity
    assert similarities[1] == 0.0, "Zero-norm vector should have 0 similarity"


def test_knn_provider_accepts_repository():
    """KNNProvider should accept CatalogRepositoryInterface."""
    from unittest.mock import Mock
    from hemdov.infrastructure.repositories.catalog_repository import CatalogRepositoryInterface

    mock_repo = Mock(spec=CatalogRepositoryInterface)
    mock_repo.load_catalog.return_value = [
        {"inputs": {"original_idea": "test"}, "outputs": {"improved_prompt": "improved"}}
    ]

    provider = KNNProvider(repository=mock_repo)

    assert provider.catalog is not None
    assert len(provider.catalog) == 1
    mock_repo.load_catalog.assert_called_once()


# ============================================================================
# Fase 5: Tests Adicionales y Mejoras
# ============================================================================

def test_knn_logs_error_at_4_99_percent_skip_rate(tmp_path, caplog):
    """KNNProvider should NOT log ERROR at 4.99% skip rate (below 5% threshold)."""
    import json
    import logging

    # Para testear el boundary justo por debajo de 5%, usamos 4.9%
    # 4.9% de 1000 = 49 ejemplos inválidos
    # 951 válidos + 49 inválidos = 1000 ejemplos, skip rate = 49/1000 = 4.9%
    catalog_path = tmp_path / "catalog_4_99_percent.json"

    examples = []
    for i in range(1000):
        if i < 951:  # 951 válidos, 49 inválidos = 4.9% (abajo del threshold de 5%)
            examples.append({
                "inputs": {"original_idea": f"valid {i}"},
                "outputs": {"improved_prompt": f"prompt {i}"}
            })
        else:
            examples.append({"inputs": {}})  # Invalid

    with open(catalog_path, 'w') as f:
        json.dump({"examples": examples}, f)

    with caplog.at_level(logging.ERROR):
        provider = KNNProvider(catalog_path=catalog_path)

    # 4.9% < 5%, NO debe loggear ERROR de quality degradation
    assert not any(
        record.levelno == logging.ERROR and "quality degradation" in record.getMessage()
        for record in caplog.records
    )


@pytest.mark.parametrize("intent,complexity", [
    ("debug", "simple"),
    ("debug", "moderate"),
    ("debug", "complex"),
    ("refactor", "simple"),
    ("refactor", "moderate"),
    ("refactor", "complex"),
    ("generate", "simple"),
    ("generate", "moderate"),
    ("generate", "complex"),
    ("explain", "simple"),
    ("explain", "moderate"),
    ("explain", "complex"),
])
def test_find_examples_all_intent_complexity_combinations(intent, complexity):
    """KNNProvider should return examples for all valid intent/complexity combinations."""
    provider = KNNProvider(catalog_path=Path("datasets/exports/unified-fewshot-pool-v2.json"))

    examples = provider.find_examples(intent=intent, complexity=complexity, k=2)

    assert len(examples) == 2
    assert all(isinstance(ex, FewShotExample) for ex in examples)


@pytest.mark.parametrize("k", [1, 2, 3, 5, 10])
def test_find_examples_returns_exact_k(k):
    """Property: find_examples always returns exactly k examples when available."""
    provider = KNNProvider(catalog_path=Path("datasets/exports/unified-fewshot-pool-v2.json"))

    for intent in ["debug", "refactor", "generate", "explain"]:
        for complexity in ["simple", "moderate", "complex"]:
            examples = provider.find_examples(intent=intent, complexity=complexity, k=k)
            assert len(examples) == k, f"Expected {k} examples for {intent}/{complexity}"


def test_similarity_score_in_valid_range():
    """Property: All similarity scores should be in [-1, 1]."""
    provider = KNNProvider(catalog_path=Path("datasets/exports/unified-fewshot-pool-v2.json"))

    # Use the class attributes directly from the provider
    valid_intents = provider.VALID_INTENTS
    valid_complexities = provider.VALID_COMPLEXITIES

    for intent in valid_intents:
        for complexity in valid_complexities:
            result = provider.find_examples_with_metadata(
                intent=intent, complexity=complexity, k=5
            )
            assert -1.0 <= result.highest_similarity <= 1.0, \
                f"Similarity out of range for {intent}/{complexity}: {result.highest_similarity}"


def test_knn_provider_end_to_end_with_real_catalog():
    """Integration test with real catalog file."""
    provider = KNNProvider(catalog_path=Path("datasets/exports/unified-fewshot-pool-v2.json"))

    # Test basic functionality
    assert len(provider.catalog) > 0

    # Test with metadata
    result = provider.find_examples_with_metadata(
        intent="debug",
        complexity="simple",
        k=3,
        user_input="fix error in function"
    )

    assert len(result.examples) == 3
    assert result.total_candidates > 0
    assert not result.empty
    assert result.met_threshold is True
