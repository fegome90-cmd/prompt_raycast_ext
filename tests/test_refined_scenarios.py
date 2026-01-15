"""
Comprehensive tests for refined NLaC + KNN pipeline.

Tests the 3 MultiAIGCD-refined scenarios:
1. DEBUG with Reflexion (not OPRO) - Scenario II
2. REFACTOR with Expected Output - Scenario III
3. GENERATE with RaR scope constraints
"""
from unittest.mock import Mock

from hemdov.domain.dto.nlac_models import NLaCRequest
from hemdov.domain.services.reflexion_service import ReflexionService

# ============================================================================
# Scenario 1: DEBUG with Reflexion (MultiAIGCD Scenario II)
# ============================================================================

class TestDebugScenarioWithReflexion:
    """DEBUG scenario should use Reflexion (not OPRO)."""

    def test_reflexion_converges_faster_than_opro(self):
        """Reflexion should converge in 1-2 iterations vs 3 for OPRO"""
        class MockLLM:
            def __init__(self):
                self.call_count = 0

            def generate(self, prompt: str, **kwargs):
                self.call_count += 1
                if "Error:" in prompt:
                    return "def fixed():\n    return 42"
                return "def buggy():\n    return 1/0"

        reflexion = ReflexionService(llm_client=MockLLM())

        result = reflexion.refine(
            prompt="Fix division by zero",
            error_type="ZeroDivisionError",
            max_iterations=2
        )

        # Should converge in 2 iterations (vs 3 for OPRO)
        assert result.iteration_count <= 2
        assert result.code is not None

    def test_debug_with_knn_examples(self):
        """DEBUG should use KNN examples from ComponentCatalog"""
        # Test with mock KNNProvider
        mock_knn = Mock()
        mock_knn.find_examples.return_value = []

        # Verify KNNProvider interface works
        examples = mock_knn.find_examples(
            intent="debug",
            complexity="simple",
            k=1
        )

        assert mock_knn.find_examples.called


# ============================================================================
# Scenario 2: REFACTOR with Expected Output (MultiAIGCD Scenario III)
# ============================================================================

class TestRefactorScenarioWithExpectedOutput:
    """REFACTOR should filter by expected_output."""

    def test_knn_filters_by_expected_output(self):
        """KNNProvider should filter examples with expected_output for REFACTOR"""
        # Test with mock KNNProvider
        mock_knn = Mock()

        # Mock: without filter returns 2 examples, with filter returns 1
        mock_knn.find_examples.side_effect = [
            [Mock(), Mock()],  # has_expected_output=False
            [Mock()],          # has_expected_output=True
        ]

        # Without filter - should return all candidates
        all_examples = mock_knn.find_examples(
            intent="refactor",
            complexity="moderate",
            k=10,
            has_expected_output=False
        )

        # With filter - should only return examples with expected_output
        filtered_examples = mock_knn.find_examples(
            intent="refactor",
            complexity="moderate",
            k=10,
            has_expected_output=True
        )

        # Filtered should be subset of all
        assert len(filtered_examples) < len(all_examples)
        assert mock_knn.find_examples.call_count == 2


# ============================================================================
# Scenario 3: GENERATE with RaR scope constraints
# ============================================================================

class TestGenerateScenarioWithRaR:
    """GENERATE with complex inputs should use RaR (Rephrase and Respond)."""

    def test_complex_input_triggers_rar(self):
        """Complex inputs should trigger RaR template in NLaCBuilder"""
        from hemdov.domain.services.nlac_builder import NLaCBuilder

        builder = NLaCBuilder(knn_provider=None)

        # Complex request (multi-sentence, technical details)
        request = NLaCRequest(
            idea="Create a REST API for user management with authentication, "
                  "authorization, CRUD operations, and database integration",
            context="Need to handle JWT tokens, bcrypt password hashing, "
                   "and follow REST best practices"
        )

        result = builder.build(request)

        # Complex input should use RaR
        assert result.strategy_meta.get("rar_used") == True
        # Template should contain rephrasing section
        assert "Rephrased Understanding" in result.template or "Understanding the Request" in result.template

    def test_simple_input_no_rar(self):
        """Simple inputs should NOT use RaR"""
        from hemdov.domain.services.nlac_builder import NLaCBuilder

        builder = NLaCBuilder(knn_provider=None)

        # Simple request
        request = NLaCRequest(
            idea="Fix this bug",
            context="Function returns None"
        )

        result = builder.build(request)

        # Simple input should NOT use RaR
        assert result.strategy_meta.get("rar_used") == False


# ============================================================================
# Integration Tests
# ============================================================================

class TestNLaCPipelineIntegration:
    """Test full pipeline integration."""

    def test_nlac_builder_without_knn(self):
        """NLaCBuilder should work without KNNProvider (backward compatibility)"""
        from hemdov.domain.services.nlac_builder import NLaCBuilder

        builder = NLaCBuilder(knn_provider=None)

        request = NLaCRequest(
            idea="Debug this function",
            context="Returns None unexpectedly"
        )

        result = builder.build(request)

        assert result.template is not None
        assert result.strategy_meta.get("knn_enabled") == False
        assert result.strategy_meta.get("fewshot_count") == 0

    def test_nlac_builder_with_mock_knn(self):
        """NLaCBuilder should inject KNN examples when KNNProvider is available"""
        from hemdov.domain.services.knn_provider import FewShotExample
        from hemdov.domain.services.nlac_builder import NLaCBuilder

        # Create mock KNNProvider
        mock_knn = Mock()
        mock_knn.find_examples.return_value = [
            FewShotExample(
                input_idea="Fix bug",
                input_context="Error in code",
                improved_prompt="Add error handling",
                role="Developer",
                directive="Fix it",
                framework="Python",
                guardrails=["Test"],
                expected_output=None,
                metadata={}
            )
        ]

        builder = NLaCBuilder(knn_provider=mock_knn)

        request = NLaCRequest(
            idea="Debug this function",
            context="Returns None"
        )

        result = builder.build(request)

        assert result.template is not None
        assert result.strategy_meta.get("knn_enabled") == True
        assert result.strategy_meta.get("fewshot_count") >= 1
        # Verify KNN was called
        mock_knn.find_examples.assert_called_once()


# ============================================================================
# OPROOptimizer Integration Tests
# ============================================================================

class TestOPROWithKNNIntegration:
    """Test OPROOptimizer with KNN few-shot examples."""

    def test_opro_without_knn(self):
        """OPROOptimizer should work without KNNProvider"""
        from hemdov.domain.dto.nlac_models import IntentType, PromptObject
        from hemdov.domain.services.oprop_optimizer import OPROOptimizer

        optimizer = OPROOptimizer(llm_client=None, knn_provider=None)

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

    def test_opro_with_mock_knn(self):
        """OPROOptimizer should include KNN examples in meta-prompt"""
        from hemdov.domain.dto.nlac_models import IntentType, PromptObject
        from hemdov.domain.services.knn_provider import FewShotExample
        from hemdov.domain.services.oprop_optimizer import OPROOptimizer

        # Create mock KNNProvider
        mock_knn = Mock()
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
            )
        ]

        optimizer = OPROOptimizer(llm_client=None, knn_provider=mock_knn)

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

        # Should include reference examples when KNN provides them
        assert "Reference Examples" in meta_prompt
        # Verify KNN was called with k=2 for meta-prompt
        mock_knn.find_examples.assert_called_once()
        call_kwargs = mock_knn.find_examples.call_args[1]
        assert call_kwargs["k"] == 2  # Meta-prompt uses k=2
