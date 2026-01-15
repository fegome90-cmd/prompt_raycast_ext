"""
Tests for OPROOptimizer with KNNProvider integration.

Tests few-shot examples in meta-prompts for better optimization.
"""
from unittest.mock import Mock

from hemdov.domain.dto.nlac_models import IntentType, NLaCRequest, PromptObject
from hemdov.domain.services.knn_provider import FewShotExample, KNNProvider
from hemdov.domain.services.oprop_optimizer import OPROOptimizer


def test_opro_without_knn():
    """OPROOptimizer should work without KNNProvider"""
    optimizer = OPROOptimizer(llm_client=None, knn_provider=None)

    request = NLaCRequest(
        idea="Optimize this function",
        context="Performance issue"
    )
    prompt_obj = PromptObject(
        id="test-1",
        version="1.0.0",
        intent_type=IntentType.GENERATE,
        template="# Task\nOptimize this function",
        strategy_meta={"intent": "generate", "complexity": "moderate"},
        constraints={"max_tokens": 500},
        created_at="2026-01-06T00:00:00Z",
        updated_at="2026-01-06T00:00:00Z",
    )

    result = optimizer.run_loop(prompt_obj)

    assert result is not None
    assert result.final_instruction is not None


def test_opro_with_knn_builds_enhanced_meta_prompt():
    """OPROOptimizer should include KNN examples in meta-prompt"""
    # Create mock KNNProvider
    mock_knn = Mock(spec=KNNProvider)
    mock_knn.find_examples.return_value = [
        FewShotExample(
            input_idea="Optimize code",
            input_context="Performance",
            improved_prompt="Use efficient algorithms",
            role="Developer",
            directive="Make it fast",
            framework="Python",
            guardrails=["Test"],
            expected_output=None,
            metadata={}
        ),
        FewShotExample(
            input_idea="Refactor function",
            input_context="Clean code",
            improved_prompt="Apply SOLID principles",
            role="Architect",
            directive="Clean up",
            framework="Python",
            guardrails=["Document"],
            expected_output=None,
            metadata={}
        ),
    ]

    optimizer = OPROOptimizer(llm_client=None, knn_provider=mock_knn)

    # Create a PromptObject with trajectory
    prompt_obj = PromptObject(
        id="test-2",
        version="1.0.0",
        intent_type=IntentType.REFACTOR,
        template="# Task\nRefactor this function",
        strategy_meta={"intent": "refactor", "complexity": "moderate"},
        constraints={"max_tokens": 1000},
        created_at="2026-01-06T00:00:00Z",
        updated_at="2026-01-06T00:00:00Z",
    )

    # Build meta-trigger and verify it includes examples
    meta_prompt = optimizer._build_meta_prompt(prompt_obj, trajectory=[])

    assert "Reference Examples" in meta_prompt
    assert "Optimize code" in meta_prompt
    assert "Refactor function" in meta_prompt


def test_opro_handles_knn_failure_gracefully():
    """OPRO should handle KNN failures without crashing."""
    # Create mock KNN that fails
    mock_knn = Mock(spec=KNNProvider)
    mock_knn.find_examples.side_effect = ConnectionError("KNN unavailable")

    optimizer = OPROOptimizer(llm_client=None, knn_provider=mock_knn)

    prompt_obj = PromptObject(
        id="test-3",
        version="1.0.0",
        intent_type=IntentType.EXPLAIN,
        template="Test prompt",
        strategy_meta={"intent": "explain", "complexity": "moderate"},
        constraints={},
        is_active=True,
        created_at="2026-01-06T00:00:00Z",
        updated_at="2026-01-06T00:00:00Z",
    )

    # Should not raise, should complete without few-shot examples
    result = optimizer.run_loop(prompt_obj)

    assert result is not None
    assert result.trajectory is not None


def test_opro_knn_failure_tracked():
    """When KNN fails during OPRO, failure should be tracked in response."""
    # Create mock KNN that fails
    mock_knn = Mock(spec=KNNProvider)
    mock_knn.find_examples.side_effect = RuntimeError("KNN catalog empty")

    optimizer = OPROOptimizer(llm_client=None, knn_provider=mock_knn)
    prompt_obj = PromptObject(
        id="test-123",
        version="1.0.0",
        intent_type=IntentType.GENERATE,
        template="Improve this prompt",
        strategy_meta={"intent": "generate", "complexity": "simple"},
        constraints={},
        created_at="2025-01-13T00:00:00Z",
        updated_at="2025-01-13T00:00:00Z"
    )

    # Act
    result = optimizer.run_loop(prompt_obj)

    # Assert
    assert result.knn_failure is not None
    assert result.knn_failure.get('failed') is True
    assert "RuntimeError" in result.knn_failure.get('errors', [{}])[0].get('error_type', '')

