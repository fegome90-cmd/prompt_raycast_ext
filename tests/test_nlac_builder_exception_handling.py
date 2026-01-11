"""Test NLaCBuilder handles specific exceptions correctly."""

import pytest
from unittest.mock import Mock
from hemdov.domain.services.nlac_builder import NLaCBuilder
from hemdov.domain.dto.nlac_models import NLaCRequest
from hemdov.domain.services.complexity_analyzer import ComplexityLevel


def test_builder_handles_runtime_error_from_knn():
    """Builder should handle RuntimeError from KNNProvider gracefully."""
    mock_knn = Mock()
    mock_knn.find_examples.side_effect = RuntimeError("Catalog file not found")

    builder = NLaCBuilder(knn_provider=mock_knn)
    request = NLaCRequest(
        idea="Create a function",
        context="",
        mode="nlac",
        intent="debug",
        complexity=ComplexityLevel.SIMPLE
    )

    result = builder.build(request)
    # Should still return valid result, just without few-shot examples
    assert result is not None
    assert result.strategy_meta.get("fewshot_count", 0) == 0


def test_builder_handles_keyerror_from_knn():
    """Builder should handle KeyError from KNNProvider gracefully."""
    mock_knn = Mock()
    mock_knn.find_examples.side_effect = KeyError("missing_key")

    builder = NLaCBuilder(knn_provider=mock_knn)
    request = NLaCRequest(
        idea="Refactor this code",
        context="",
        mode="nlac",
        intent="refactor",
        complexity=ComplexityLevel.MODERATE
    )

    result = builder.build(request)
    assert result is not None
    assert result.strategy_meta.get("fewshot_count", 0) == 0


def test_builder_propagates_unexpected_exceptions():
    """Builder should propagate exceptions that are not KNN-related."""
    mock_knn = Mock()
    # KeyboardInterrupt should NEVER be caught
    mock_knn.find_examples.side_effect = KeyboardInterrupt()

    builder = NLaCBuilder(knn_provider=mock_knn)
    request = NLaCRequest(
        idea="Test",
        context="",
        mode="nlac",
        intent="debug",
        complexity=ComplexityLevel.SIMPLE
    )

    # Should raise KeyboardInterrupt, not catch it
    with pytest.raises(KeyboardInterrupt):
        builder.build(request)
