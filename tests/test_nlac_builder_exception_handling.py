"""
Test NLaCBuilder separates transient failures from code bugs.

After fix: ConnectionError/TimeoutError/KNNProviderError degrade gracefully.
KeyError/TypeError/RuntimeError propagate as code bugs.
"""

import pytest
from unittest.mock import Mock
from hemdov.domain.services.nlac_builder import NLaCBuilder
from hemdov.domain.dto.nlac_models import NLaCRequest
from hemdov.domain.services.complexity_analyzer import ComplexityLevel
from hemdov.domain.services.knn_provider import KNNProviderError


def test_transient_connection_error_degrades_gracefully():
    """Test that ConnectionError degrades gracefully."""
    mock_knn = Mock()
    mock_knn.find_examples.side_effect = ConnectionError("Network down")

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
    assert result.strategy_meta.get("knn_failed") is True


def test_transient_timeout_error_degrades_gracefully():
    """Test that TimeoutError degrades gracefully."""
    mock_knn = Mock()
    mock_knn.find_examples.side_effect = TimeoutError("Request timed out")

    builder = NLaCBuilder(knn_provider=mock_knn)
    request = NLaCRequest(
        idea="Create a function",
        context="",
        mode="nlac",
        intent="debug",
        complexity=ComplexityLevel.SIMPLE
    )

    result = builder.build(request)
    assert result is not None
    assert result.strategy_meta.get("fewshot_count", 0) == 0
    assert result.strategy_meta.get("knn_failed") is True


def test_knn_provider_error_degrades_gracefully():
    """Test that KNNProviderError degrades gracefully."""
    mock_knn = Mock()
    mock_knn.find_examples.side_effect = KNNProviderError("KNN service unavailable")

    builder = NLaCBuilder(knn_provider=mock_knn)
    request = NLaCRequest(
        idea="Create a function",
        context="",
        mode="nlac",
        intent="debug",
        complexity=ComplexityLevel.SIMPLE
    )

    result = builder.build(request)
    assert result is not None
    assert result.strategy_meta.get("fewshot_count", 0) == 0


def test_code_bug_keyerror_propagates():
    """Test that KeyError (code bug) propagates instead of being swallowed."""
    mock_knn = Mock()
    mock_knn.find_examples.side_effect = KeyError("missing_key")

    builder = NLaCBuilder(knn_provider=mock_knn)
    request = NLaCRequest(
        idea="Debug this error",
        context="",
        mode="nlac",
        intent="debug",
        complexity=ComplexityLevel.SIMPLE
    )

    # Should propagate KeyError, not swallow it
    with pytest.raises(KeyError) as exc_info:
        builder.build(request)

    assert "missing_key" in str(exc_info.value)


def test_code_bug_typeerror_propagates():
    """Test that TypeError (code bug) propagates."""
    mock_knn = Mock()
    mock_knn.find_examples.side_effect = TypeError("Wrong type")

    builder = NLaCBuilder(knn_provider=mock_knn)
    request = NLaCRequest(
        idea="Debug this error",
        context="",
        mode="nlac",
        intent="debug",
        complexity=ComplexityLevel.SIMPLE
    )

    with pytest.raises(TypeError):
        builder.build(request)


def test_code_bug_runtime_error_propagates():
    """Test that RuntimeError (code bug) propagates."""
    mock_knn = Mock()
    mock_knn.find_examples.side_effect = RuntimeError("Code bug detected")

    builder = NLaCBuilder(knn_provider=mock_knn)
    request = NLaCRequest(
        idea="Debug this error",
        context="",
        mode="nlac",
        intent="debug",
        complexity=ComplexityLevel.SIMPLE
    )

    with pytest.raises(RuntimeError):
        builder.build(request)


def test_code_bug_value_error_propagates():
    """Test that ValueError (code bug) propagates."""
    mock_knn = Mock()
    mock_knn.find_examples.side_effect = ValueError("Invalid value")

    builder = NLaCBuilder(knn_provider=mock_knn)
    request = NLaCRequest(
        idea="Debug this error",
        context="",
        mode="nlac",
        intent="debug",
        complexity=ComplexityLevel.SIMPLE
    )

    with pytest.raises(ValueError):
        builder.build(request)


def test_keyboard_interrupt_never_caught():
    """KeyboardInterrupt should NEVER be caught."""
    mock_knn = Mock()
    mock_knn.find_examples.side_effect = KeyboardInterrupt()

    builder = NLaCBuilder(knn_provider=mock_knn)
    request = NLaCRequest(
        idea="Test",
        context="",
        mode="nlac",
        intent="debug",
        complexity=ComplexityLevel.SIMPLE
    )

    with pytest.raises(KeyboardInterrupt):
        builder.build(request)
