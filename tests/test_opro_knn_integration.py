"""
Tests for OPROOptimizer with KNNProvider integration.

Tests few-shot examples in meta-prompts for better optimization.
"""
from unittest.mock import Mock
from hemdov.domain.dto.nlac_models import NLaCRequest, PromptObject, IntentType
from hemdov.domain.services.oprop_optimizer import OPROOptimizer
from hemdov.domain.services.knn_provider import KNNProvider, FewShotExample


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
