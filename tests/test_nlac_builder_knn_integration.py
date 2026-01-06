"""
Tests for NLaCBuilder integration with KNNProvider.

Tests ComponentCatalog few-shot example injection into NLaCBuilder.
"""
from pathlib import Path
from hemdov.domain.dto.nlac_models import NLaCRequest, NLaCInputs
from hemdov.domain.services.nlac_builder import NLaCBuilder
from hemdov.domain.services.knn_provider import KNNProvider, FewShotExample
from unittest.mock import Mock


def test_nlac_builder_without_knn():
    """NLaCBuilder should work without KNNProvider (backward compatibility)"""
    builder = NLaCBuilder(knn_provider=None)

    request = NLaCRequest(
        idea="Debug this function",
        context="The function returns None",
        inputs=NLaCInputs(
            code_snippet="def foo():\n    pass",
            error_log="TypeError: NoneType is not iterable"
        )
    )

    result = builder.build(request)

    assert result.template is not None
    assert "# Examples" not in result.template  # No examples without KNN
    assert result.strategy_meta["knn_enabled"] == False
    assert result.strategy_meta["fewshot_count"] == 0


def test_nlac_builder_with_knn_injects_examples():
    """NLaCBuilder should inject KNN examples into template"""
    # Create mock KNNProvider that returns examples
    mock_knn = Mock(spec=KNNProvider)
    mock_knn.find_examples.return_value = [
        FewShotExample(
            input_idea="Optimize slow function",
            input_context="Performance issue",
            improved_prompt="Optimize the code using list comprehension",
            role="Developer",
            directive="Make it faster",
            framework="Python",
            guardrails=["Maintain readability"],
            expected_output=None,
            metadata={}
        ),
        FewShotExample(
            input_idea="Refactor legacy code",
            input_context="Code smells",
            improved_prompt="Refactor using modern patterns",
            role="Architect",
            directive="Clean up the code",
            framework="Python",
            guardrails=["Keep functionality"],
            expected_output=None,
            metadata={}
        ),
        FewShotExample(
            input_idea="Improve algorithm",
            input_context="O(n²) complexity",
            improved_prompt="Use hash map for O(n) lookup",
            role="Senior Developer",
            directive="Optimize algorithm",
            framework="Python",
            guardrails=["Test thoroughly"],
            expected_output=None,
            metadata={}
        ),
    ]

    builder = NLaCBuilder(knn_provider=mock_knn)

    request = NLaCRequest(
        idea="Refactor this code for better performance",
        context="It's too slow",
        inputs=NLaCInputs(
            code_snippet="def slow_code():\n    return [x for x in range(1000)]"
        )
    )

    result = builder.build(request)

    assert result.template is not None
    assert "# Examples" in result.template
    assert result.strategy_meta["knn_enabled"] == True
    assert result.strategy_meta["fewshot_count"] == 3

    # Verify KNNProvider was called correctly
    mock_knn.find_examples.assert_called_once()
    call_args = mock_knn.find_examples.call_args
    assert call_args[1]["has_expected_output"] == True  # REFACTOR uses expected_output filter


def test_nlac_builder_filters_refactor_examples():
    """NLaCBuilder should filter by expected_output for REFACTOR"""
    # Create mock KNNProvider that returns empty list (simulating catalog without expected_output)
    mock_knn = Mock(spec=KNNProvider)
    mock_knn.find_examples.return_value = []

    builder = NLaCBuilder(knn_provider=mock_knn)

    request = NLaCRequest(
        idea="Refactor this function",
        context="Make it cleaner",
    )

    result = builder.build(request)

    assert result.template is not None
    # The builder should have attempted to fetch with has_expected_output=True
    assert result.strategy_meta["knn_enabled"] == True
    assert result.strategy_meta["fewshot_count"] == 0  # No examples found
