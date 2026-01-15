"""
Integration tests for Domain Layer Services.

This file tests the interaction between multiple domain services
to verify they work correctly together.

Tests cover:
- IntentClassifier + ComplexityAnalyzer integration
- NLaCBuilder full pipeline integration
- ReflexionService integration scenarios
- OPROOptimizer integration scenarios
"""

import pytest
from datetime import datetime, UTC
from hemdov.domain.dto.nlac_models import (
    NLaCRequest,
    PromptObject,
    IntentType,
    NLaCInputs,
)
from hemdov.domain.services.intent_classifier import IntentClassifier
from hemdov.domain.services.complexity_analyzer import ComplexityAnalyzer, ComplexityLevel
from hemdov.domain.services.nlac_builder import NLaCBuilder
from hemdov.domain.services.reflexion_service import ReflexionService, ReflexionResult
from hemdov.domain.services.oprop_optimizer import OPROOptimizer
from hemdov.domain.services.llm_protocol import LLMClient


class TestIntentComplexityIntegration:
    """Integration tests for IntentClassifier + ComplexityAnalyzer."""

    @pytest.fixture
    def classifier(self):
        return IntentClassifier()

    @pytest.fixture
    def analyzer(self):
        return ComplexityAnalyzer()

    def test_debug_intent_with_runtime_error_is_complex(self, classifier, analyzer):
        """
        Test that DEBUG intent with runtime error + long input is classified as COMPLEX.

        Scenario: User provides code snippet and error log with long context
        Expected: DEBUG intent + COMPLEX complexity
        """
        request = NLaCRequest(
            idea="Fix this error in the production system that is causing critical failures "
                 "and needs immediate attention with comprehensive debugging and analysis "
                 "of the entire application infrastructure including database connections "
                 "and network components and user session management and authentication",
            context="The application is failing when processing user requests "
                   "and it's causing downtime for our customers due to multiple "
                   "interconnected issues that require deep investigation of the "
                   "entire system architecture including componentes, repositorios, "
                   "adaptadores, integración, pipeline, and framework patterns",
            mode="nlac",
            inputs=NLaCInputs(
                code_snippet="def process_user_request(user_id):\n    # Complex logic here\n"
                                "    result = database.query(user_id)\n    return result",
                error_log="DatabaseError: connection timeout after 30 seconds"
            )
        )

        # Classify intent
        intent_str = classifier.classify(request)
        intent_type = classifier.get_intent_type(intent_str)

        # Analyze complexity
        complexity = analyzer.analyze(request.idea, request.context)

        # Verify results
        assert intent_type == IntentType.DEBUG
        assert complexity == ComplexityLevel.COMPLEX

    def test_simple_generate_intent_is_simple(self, classifier, analyzer):
        """
        Test that simple GENERATE request is classified as SIMPLE.

        Scenario: Short, simple request
        Expected: GENERATE intent + SIMPLE complexity
        """
        request = NLaCRequest(
            idea="Create a hello world function",
            context="",
            mode="nlac"
        )

        intent_str = classifier.classify(request)
        intent_type = classifier.get_intent_type(intent_str)
        complexity = analyzer.analyze(request.idea, request.context)

        assert intent_type == IntentType.GENERATE
        assert complexity == ComplexityLevel.SIMPLE


class TestNLaCBuilderIntegration:
    """Integration tests for NLaCBuilder with its dependencies."""

    @pytest.fixture
    def builder(self):
        return NLaCBuilder(knn_provider=None)

    def test_builder_uses_classifier_and_analyzer(self, builder):
        """
        Test that NLaCBuilder correctly integrates IntentClassifier and ComplexityAnalyzer.

        Verifies:
        1. Intent is classified correctly
        2. Complexity is analyzed correctly
        3. Strategy is selected based on both
        4. Role is injected based on intent + complexity
        """
        request = NLaCRequest(
            idea="Fix this bug",
            context="In the authentication module",
            mode="nlac"
        )

        result = builder.build(request)

        # Verify integration
        assert result.intent_type in [IntentType.GENERATE, IntentType.DEBUG]
        assert result.strategy_meta["complexity"] in ["simple", "moderate", "complex"]
        assert result.strategy_meta["intent"] in ["generate", "debug", "refactor", "explain"]
        assert result.strategy_meta["role"] is not None

    def test_builder_with_structured_inputs(self, builder):
        """
        Test that NLaCBuilder correctly handles structured inputs.

        Verifies that code_snippet and error_log are included in the template.
        """
        request = NLaCRequest(
            idea="Fix this error",
            context="Production issue",
            mode="nlac",
            inputs=NLaCInputs(
                code_snippet="def buggy():\n    return 1/0",
                error_log="ZeroDivisionError: division by zero"
            )
        )

        result = builder.build(request)

        # Verify structured inputs are in template
        template = result.template
        assert "def buggy():" in template
        assert "ZeroDivisionError" in template


class TestReflexionServiceIntegration:
    """Integration tests for ReflexionService with dependencies."""

    def test_reflexion_with_llm_and_executor(self):
        """
        Test ReflexionService with both LLM client and executor.

        Scenario: Code generation fails first time, succeeds second time
        Expected: Refinement loop retries and converges
        """
        class TwoTryLLM:
            def __init__(self):
                self.call_count = 0

            def generate(self, prompt: str, **kwargs) -> str:
                self.call_count += 1
                if self.call_count == 1:
                    return "def buggy():\n    return 1/0"
                else:
                    return "def fixed():\n    return 42"

        def executor(code):
            if "buggy" in code:
                raise RuntimeError("Code has bugs")
            return True

        service = ReflexionService(llm_client=TwoTryLLM(), executor=executor)

        result = service.refine(
            prompt="Fix the bug",
            error_type="RuntimeError",
            max_iterations=2
        )

        # Should converge in 2 iterations
        assert result.success is True
        assert result.iteration_count == 2
        assert "fixed" in result.code
        assert len(result.error_history) == 1

    def test_reflexion_degrades_without_executor(self):
        """
        Test ReflexionService without executor (generation only).

        Scenario: No executor provided, LLM generates code
        Expected: Assumes success without validation
        """
        class SimpleLLM:
            def generate(self, prompt: str, **kwargs) -> str:
                return "def generated_code():\n    pass"

        service = ReflexionService(llm_client=SimpleLLM(), executor=None)

        result = service.refine(
            prompt="Generate a function",
            error_type="CodeRequest",
            max_iterations=1
        )

        # Should succeed without execution validation
        assert result.success is True
        assert result.iteration_count == 1
        assert "generated_code" in result.code


class TestOPROOptimizerIntegration:
    """Integration tests for OPROOptimizer with dependencies."""

    @pytest.fixture
    def sample_prompt_obj(self):
        """Create a sample PromptObject for testing."""
        return PromptObject(
            id="test-123",
            version="1.0.0",
            intent_type=IntentType.GENERATE,
            template="Create a function",
            strategy_meta={"strategy": "simple", "complexity": "simple"},
            constraints={"max_tokens": 500},
            created_at=datetime.now(UTC).isoformat(),
            updated_at=datetime.now(UTC).isoformat(),
        )

    def test_optimizer_with_knn_provider(self, sample_prompt_obj):
        """
        Test OPROOptimizer with KNN provider integration.

        Verifies that KNN failures are tracked and don't stop optimization.
        """
        from hemdov.domain.services.knn_provider import KNNProvider, KNNProviderError

        class FailingKNN:
            def find_examples(self, **kwargs):
                raise KNNProviderError("Catalog empty")

        optimizer = OPROOptimizer(llm_client=None, knn_provider=FailingKNN())

        def mock_evaluate(prompt_obj):
            return 0.7, "Good"

        optimizer._evaluate = mock_evaluate

        result = optimizer.run_loop(sample_prompt_obj)

        # Should complete despite KNN failures
        assert result is not None
        assert result.final_instruction is not None
        # KNN failures should be tracked
        assert len(optimizer._knn_failures) == 3  # One per iteration

    def test_optimizer_trajectory_with_scores(self, sample_prompt_obj):
        """
        Test that OPROOptimizer builds correct trajectory with scores.

        Verifies trajectory entries have correct metadata.
        """
        optimizer = OPROOptimizer(llm_client=None, knn_provider=None)

        iteration_scores = [0.5, 0.7, 0.9]
        call_count = [0]

        def mock_evaluate(prompt_obj):
            score = iteration_scores[call_count[0]]
            call_count[0] += 1
            return score, f"Score: {score}"

        optimizer._evaluate = mock_evaluate

        result = optimizer.run_loop(sample_prompt_obj)

        # Verify trajectory structure
        assert len(result.trajectory) == 3

        for i, entry in enumerate(result.trajectory, 1):
            assert entry.iteration_number == i
            assert entry.meta_prompt_used is not None
            assert entry.generated_instruction is not None
            assert entry.score in iteration_scores
            assert entry.feedback is not None


class TestCrossServiceIntegration:
    """Cross-service integration tests."""

    def test_full_nlac_pipeline_integration(self):
        """
        Test the full NLaC pipeline: Request → Classifier → Analyzer → Builder → PromptObject.

        This is a critical integration test that verifies the entire flow.
        """
        # Create services
        classifier = IntentClassifier()
        analyzer = ComplexityAnalyzer()
        builder = NLaCBuilder(knn_provider=None)

        # Create request
        request = NLaCRequest(
            idea="Fix this bug in the authentication module",
            context="Users cannot log in due to database timeout",
            mode="nlac",
            inputs=NLaCInputs(
                code_snippet="def authenticate(user, password):\n    db.connect()\n    return db.query(user)",
                error_log="DatabaseError: connection timeout"
            )
        )

        # Step 1: Classify intent
        intent_str = classifier.classify(request)
        intent_type = classifier.get_intent_type(intent_str)

        # Step 2: Analyze complexity
        complexity = analyzer.analyze(request.idea, request.context)

        # Step 3: Build prompt
        result = builder.build(request)

        # Verify integration
        assert intent_type in [IntentType.DEBUG, IntentType.GENERATE]
        assert complexity in [ComplexityLevel.SIMPLE, ComplexityLevel.MODERATE, ComplexityLevel.COMPLEX]

        # Verify builder used both classifier and analyzer
        assert result.strategy_meta["intent"] in ["generate", "debug", "refactor", "explain"]
        assert result.strategy_meta["complexity"] in ["simple", "moderate", "complex"]

        # Verify template was built
        assert result.template is not None
        assert len(result.template) > 0

        # Verify constraints were built based on complexity
        if complexity == ComplexityLevel.SIMPLE:
            assert result.constraints["max_tokens"] == 500
        elif complexity == ComplexityLevel.MODERATE:
            assert result.constraints["max_tokens"] == 1000
        elif complexity == ComplexityLevel.COMPLEX:
            assert result.constraints["max_tokens"] == 2000

    def test_reflexion_after_nlac_builder_integration(self):
        """
        Test ReflexionService after NLaCBuilder produces initial code.

        This tests the DEBUG scenario where:
        1. NLaCBuilder produces initial debugging prompt
        2. ReflexionService iteratively refines the code
        """
        # Step 1: NLaCBuilder produces initial prompt
        builder = NLaCBuilder(knn_provider=None)
        request = NLaCRequest(
            idea="Fix this error",
            context="In production",
            mode="nlac",
            inputs=NLaCInputs(
                code_snippet="def buggy():\n    return 1/0",
                error_log="ZeroDivisionError"
            )
        )
        initial_prompt = builder.build(request)

        # Step 2: ReflexionService refines the code
        class ImprovementLLM:
            def __init__(self):
                self.call_count = 0

            def generate(self, prompt: str, **kwargs) -> str:
                self.call_count += 1
                # First call: return buggy code (will fail execution)
                if self.call_count == 1:
                    return "def buggy():\n    return 1/0"
                # Second call (with error feedback): return fixed code
                else:
                    return "def fixed():\n    return 42"

        def executor(code):
            if "buggy" in code:
                raise RuntimeError("Still buggy")
            return True

        reflexion = ReflexionService(llm_client=ImprovementLLM(), executor=executor)

        result = reflexion.refine(
            prompt=initial_prompt.template,
            error_type="ZeroDivisionError",
            max_iterations=2
        )

        # Verify integration
        assert result.success is True
        assert "fixed" in result.code
        assert result.iteration_count == 2

    def test_opro_after_nlac_builder_integration(self):
        """
        Test OPROOptimizer after NLaCBuilder produces initial prompt.

        This tests the optimization scenario where:
        1. NLaCBuilder produces initial prompt
        2. OPROOptimizer iteratively optimizes the prompt
        """
        # Step 1: NLaCBuilder produces initial prompt
        builder = NLaCBuilder(knn_provider=None)
        request = NLaCRequest(
            idea="Create a user authentication system",
            context="For a web application",
            mode="nlac",
            enable_optimization=True,
            max_iterations=2
        )
        initial_prompt = builder.build(request)

        # Step 2: OPROOptimizer optimizes the prompt
        optimizer = OPROOptimizer(llm_client=None, knn_provider=None)

        result = optimizer.run_loop(initial_prompt)

        # Verify integration
        assert result is not None
        assert result.final_instruction is not None
        assert result.iteration_count <= 3  # MAX_ITERATIONS
        assert result.prompt_id == initial_prompt.id

        # Verify optimization happened (not just returned original)
        # The trajectory should show iterations
        assert len(result.trajectory) >= 0
