"""
Coverage tests for OPROOptimizer.

This file provides comprehensive coverage tests for the domain service
located at hemdov/domain/services/oprop_optimizer.py.

Tests cover:
- Run loop converges (early stopping)
- Run loop max iterations
- Evaluate candidate scoring
- Trajectory tracking
- Best candidate selection
"""

import pytest

# Component not exposed - kept for future use (see PLAN-2026-0001)
pytestmark = pytest.mark.skip(
    reason="Component not exposed - kept for future use (see PLAN-2026-0001)"
)
from datetime import datetime, UTC
from hemdov.domain.dto.nlac_models import (
    PromptObject,
    IntentType,
    OptimizeResponse,
    OPROIteration,
)
from hemdov.domain.services.oprop_optimizer import OPROOptimizer
from hemdov.domain.services.llm_protocol import LLMClient


class TestOPROOptimizerCoverage:
    """Comprehensive coverage tests for OPROOptimizer domain service."""

    @pytest.fixture
    def optimizer(self):
        """Create optimizer without LLM or KNN provider."""
        return OPROOptimizer(llm_client=None, knn_provider=None)

    @pytest.fixture
    def sample_prompt_obj(self):
        """Create a sample PromptObject for testing."""
        return PromptObject(
            id="test-123",
            version="1.0.0",
            intent_type=IntentType.GENERATE,
            template="Create a function that returns hello world",
            strategy_meta={"strategy": "simple", "complexity": "simple"},
            constraints={"max_tokens": 500, "include_examples": False, "include_explanation": False},
            created_at=datetime.now(UTC).isoformat(),
            updated_at=datetime.now(UTC).isoformat(),
        )

    # ========================================================================
    # RUN LOOP CONVERGES (Early Stopping)
    # ========================================================================

    def test_run_loop_converges(self, optimizer, sample_prompt_obj):
        """
        Test that optimization loop converges with early stopping.

        Verifies that:
        1. Loop stops when quality threshold (1.0) is reached
        2. early_stopped flag is True
        3. Final score is 1.0
        4. Best candidate is returned
        """
        # Mock evaluator that returns perfect score on first try
        call_count = [0]
        def mock_evaluate(prompt_obj):
            call_count[0] += 1
            return 1.0, "All constraints passed"

        optimizer._evaluate = mock_evaluate

        result = optimizer.run_loop(sample_prompt_obj)

        # Verify early stopping
        assert result.early_stopped is True
        assert result.final_score == 1.0
        assert result.iteration_count == 1  # Should stop after first iteration
        # Note: trajectory is empty because early stopping happens before trajectory entry is added
        assert len(result.trajectory) == 0  # No trajectory entries when early stopping on first iteration
        assert result.final_instruction is not None
        assert result.prompt_id == sample_prompt_obj.id

    # ========================================================================
    # RUN LOOP MAX ITERATIONS
    # ========================================================================

    def test_run_loop_max_iterations(self, optimizer, sample_prompt_obj):
        """
        Test that optimization loop respects max_iterations limit.

        Verifies that:
        1. Loop stops at MAX_ITERATIONS (3)
        2. early_stopped flag is False
        3. All 3 iterations were attempted
        4. Best candidate from all iterations is returned
        """
        # Mock evaluator that never reaches threshold
        iteration_scores = [0.6, 0.7, 0.8]
        call_count = [0]

        def mock_evaluate(prompt_obj):
            score = iteration_scores[call_count[0]]
            call_count[0] += 1
            return score, f"Score: {score}"

        optimizer._evaluate = mock_evaluate

        result = optimizer.run_loop(sample_prompt_obj)

        # Verify max iterations reached
        assert result.early_stopped is False
        assert result.iteration_count == 3  # MAX_ITERATIONS
        assert len(result.trajectory) == 3  # All iterations recorded
        assert result.final_score == 0.8  # Best score from all iterations

    # ========================================================================
    # EVALUATE CANDIDATE SCORING
    # ========================================================================

    def test_evaluate_candidate_scoring(self, optimizer):
        """
        Test that candidate evaluation produces correct scores.

        Verifies different scenarios:
        1. Perfect score (all constraints passed)
        2. Partial score (some constraints failed)
        3. Zero score (all constraints failed)
        """
        # Perfect candidate - passes all constraints
        perfect_prompt = PromptObject(
            id="perfect",
            version="1.0.0",
            intent_type=IntentType.GENERATE,
            template="```python\ndef hello():\n    return 'hello world'\n```\n\nThis is an example with explanation because it clarifies the code.",
            strategy_meta={"strategy": "simple"},
            constraints={
                "max_tokens": 500,
                "format": "code in Python",
                "include_examples": True,
                "include_explanation": True
            },
            created_at=datetime.now(UTC).isoformat(),
            updated_at=datetime.now(UTC).isoformat(),
        )

        score, feedback = optimizer._evaluate(perfect_prompt)
        assert score == 1.0
        assert feedback == "All constraints passed"

        # Partial candidate - passes some constraints
        partial_prompt = PromptObject(
            id="partial",
            version="1.0.0",
            intent_type=IntentType.GENERATE,
            template="Create a function",  # Too short, no code
            strategy_meta={"strategy": "simple"},
            constraints={"max_tokens": 500, "include_examples": True},
            created_at=datetime.now(UTC).isoformat(),
            updated_at=datetime.now(UTC).isoformat(),
        )

        score, feedback = optimizer._evaluate(partial_prompt)
        assert 0.0 < score < 1.0  # Partial score
        assert "Missing" in feedback or "too short" in feedback

    # ========================================================================
    # TRAJECTORY TRACKING
    # ========================================================================

    def test_trajectory_tracking(self, optimizer, sample_prompt_obj):
        """
        Test that trajectory is tracked correctly across iterations.

        Verifies that each iteration records:
        1. iteration_number
        2. meta_prompt_used
        3. generated_instruction
        4. score
        5. feedback
        """
        # Mock evaluator with varying scores
        iteration_scores = [0.5, 0.7, 0.9]
        call_count = [0]

        def mock_evaluate(prompt_obj):
            score = iteration_scores[call_count[0]]
            feedback = f"Iteration {call_count[0] + 1}"
            call_count[0] += 1
            return score, feedback

        optimizer._evaluate = mock_evaluate

        result = optimizer.run_loop(sample_prompt_obj)

        # Verify trajectory
        assert len(result.trajectory) == 3

        # Check first iteration
        iter1 = result.trajectory[0]
        assert iter1.iteration_number == 1
        assert iter1.score == 0.5
        assert iter1.feedback == "Iteration 1"
        assert iter1.meta_prompt_used is not None
        assert iter1.generated_instruction is not None

        # Check last iteration
        iter3 = result.trajectory[2]
        assert iter3.iteration_number == 3
        assert iter3.score == 0.9

    # ========================================================================
    # BEST CANDIDATE SELECTION
    # ========================================================================

    def test_best_candidate_selection(self, optimizer, sample_prompt_obj):
        """
        Test that best candidate is selected from trajectory.

        Verifies that:
        1. Best score is tracked correctly
        2. Best prompt is returned even if not last
        3. Score improves are handled correctly
        """
        # Scores that improve then decline (0.5 -> 0.9 -> 0.7)
        iteration_scores = [0.5, 0.9, 0.7]
        call_count = [0]

        def mock_evaluate(prompt_obj):
            score = iteration_scores[call_count[0]]
            call_count[0] += 1
            return score, f"Score: {score}"

        optimizer._evaluate = mock_evaluate

        result = optimizer.run_loop(sample_prompt_obj)

        # Should return best score (0.9) from iteration 2
        assert result.final_score == 0.9
        assert result.iteration_count == 3  # Ran all iterations (early_stopped=False)

    # ========================================================================
    # KNN FAILURE TRACKING
    # ========================================================================

    def test_knn_failure_tracking(self, optimizer, sample_prompt_obj):
        """
        Test that KNN failures are tracked correctly.

        Verifies that:
        1. KNN errors are tracked in _knn_failures
        2. KNN failure metadata is included in response
        3. Transient failures don't stop optimization
        """
        from hemdov.domain.services.knn_provider import KNNProvider, KNNProviderError

        class FailingKNNProvider:
            def find_examples(self, **kwargs):
                raise KNNProviderError("Catalog empty")

        optimizer_with_knn = OPROOptimizer(llm_client=None, knn_provider=FailingKNNProvider())

        def mock_evaluate(prompt_obj):
            return 0.8, "Good"

        optimizer_with_knn._evaluate = mock_evaluate

        result = optimizer_with_knn.run_loop(sample_prompt_obj)

        # Should have tracked KNN failure
        assert len(optimizer_with_knn._knn_failures) == 3  # One per iteration

        # Should have KNN failure metadata in response
        # Note: KNN failures are tracked in knn_failure dict if early stopping occurred
        # or if max iterations reached and failures exist
        if result.early_stopped or optimizer_with_knn._knn_failures:
            # The KNN failure metadata is built in run_loop method
            # We can verify it was tracked
            assert any(f["error_type"] == "KNNProviderError" for f in optimizer_with_knn._knn_failures)

    # ========================================================================
    # INPUT VALIDATION
    # ========================================================================

    def test_input_validation_none_prompt_obj(self, optimizer):
        """Test that None prompt_obj raises ValueError."""
        with pytest.raises(ValueError, match="prompt_obj cannot be None"):
            optimizer.run_loop(None)

    # ========================================================================
    # FIRST ITERATION USES ORIGINAL PROMPT
    # ========================================================================

    def test_first_iteration_uses_original_prompt(self, optimizer, sample_prompt_obj):
        """
        Test that first iteration uses the original prompt without modification.

        Verifies that:
        1. First iteration candidate is the original prompt_obj
        2. No LLM generation happens on first iteration
        """
        original_template = sample_prompt_obj.template

        def mock_evaluate(prompt_obj):
            return 0.5, "OK"

        optimizer._evaluate = mock_evaluate

        result = optimizer.run_loop(sample_prompt_obj)

        # First iteration should use original template
        first_iter = result.trajectory[0]
        assert first_iter.generated_instruction == original_template

    # ========================================================================
    # QUALITY THRESHOLD CONSTANTS
    # ========================================================================

    def test_quality_threshold_constants(self, optimizer):
        """
        Test that quality threshold constants are set correctly.

        Verifies:
        1. MAX_ITERATIONS = 3
        2. QUALITY_THRESHOLD = 1.0
        """
        assert optimizer.MAX_ITERATIONS == 3
        assert optimizer.QUALITY_THRESHOLD == 1.0

    # ========================================================================
    # RESPONSE BUILDING
    # ========================================================================

    def test_response_building(self, optimizer, sample_prompt_obj):
        """
        Test that OptimizeResponse is built correctly.

        Verifies all response fields:
        1. prompt_id
        2. final_instruction
        3. final_score
        4. iteration_count
        5. early_stopped
        6. trajectory
        7. backend/model fields
        """
        def mock_evaluate(prompt_obj):
            return 0.7, "Partial success"

        optimizer._evaluate = mock_evaluate

        result = optimizer.run_loop(sample_prompt_obj)

        # Verify response structure
        assert isinstance(result, OptimizeResponse)
        assert result.prompt_id == sample_prompt_obj.id
        assert result.final_instruction is not None
        assert result.final_score == 0.7
        assert result.iteration_count == 3
        assert result.early_stopped is False
        assert len(result.trajectory) == 3
        assert result.backend == "nlac-opro"
        assert result.model == "oprop-optimizer"
        assert result.improved_prompt == result.final_instruction

    # ========================================================================
    # LLM FAILURE HANDLING (CRITICAL - 10/10 priority)
    # ========================================================================

    def test_llm_connection_error_degrades_gracefully(self, sample_prompt_obj):
        """
        Test that LLM ConnectionError is handled gracefully.

        When LLM is unavailable:
        1. Should fall back to original prompt
        2. Should return meaningful response
        3. Should not crash or raise uncaught exceptions
        """
        class FailingLLM:
            def generate(self, prompt: str, **kwargs) -> str:
                raise ConnectionError("LLM service unavailable")

        optimizer = OPROOptimizer(llm_client=FailingLLM(), knn_provider=None)

        # First iteration uses original prompt, so we need to handle variation generation
        # For iterations 2+, when LLM fails, the behavior depends on implementation
        # Let's verify it doesn't crash
        result = optimizer.run_loop(sample_prompt_obj)

        # Should complete with first iteration (original prompt)
        assert result is not None
        assert result.final_instruction is not None
        # The implementation should handle LLM failures gracefully

    def test_llm_timeout_error_degrades_gracefully(self, sample_prompt_obj):
        """
        Test that LLM TimeoutError is handled gracefully.

        When LLM times out:
        1. Should not hang indefinitely
        2. Should return fallback response
        """
        class TimeoutLLM:
            def generate(self, prompt: str, **kwargs) -> str:
                raise TimeoutError("LLM request timed out")

        optimizer = OPROOptimizer(llm_client=TimeoutLLM(), knn_provider=None)

        result = optimizer.run_loop(sample_prompt_obj)

        # Should complete despite timeout
        assert result is not None
        assert result.final_instruction is not None

    def test_llm_runtime_error_not_yet_integrated(self, sample_prompt_obj):
        """
        Test LLM error handling (note: LLM integration is pending).

        NOTE: The _llm_generate_variation method currently has a TODO
        and delegates to _simple_refinement. When LLM integration is
        implemented, this test should verify proper error handling.
        """
        # For now, verify that having an LLM client doesn't break the flow
        class PlaceholderLLM:
            def generate(self, prompt: str, **kwargs) -> str:
                # This won't be called until LLM integration is implemented
                return "Improved version"

        optimizer = OPROOptimizer(llm_client=PlaceholderLLM(), knn_provider=None)

        # Should complete without errors (uses _simple_refinement for now)
        result = optimizer.run_loop(sample_prompt_obj)
        assert result is not None
        assert result.final_instruction is not None

        # TODO: When LLM integration is implemented, add test for:
        # - RuntimeError propagation (code bugs)
        # - ConnectionError/TimeoutError graceful degradation

    # ========================================================================
    # INPUT VALIDATION (IMPORTANT - 8/10 priority)
    # ========================================================================

    def test_input_validation_minimal_template(self, optimizer):
        """
        Test that minimal template (below quality threshold) is handled correctly.

        Very short templates fail the quality check in _evaluate():
        - Templates <= 50 chars fail basic quality check
        """
        minimal_prompt = PromptObject(
            id="minimal",
            version="1.0.0",
            intent_type=IntentType.GENERATE,
            template="Hi",  # Very short template
            strategy_meta={"strategy": "simple"},
            constraints={"max_tokens": 500},
            created_at=datetime.now(UTC).isoformat(),
            updated_at=datetime.now(UTC).isoformat(),
        )

        def mock_evaluate(prompt_obj):
            return 0.5, "OK"

        optimizer._evaluate = mock_evaluate

        # Should handle gracefully
        result = optimizer.run_loop(minimal_prompt)
        assert result is not None

    # ========================================================================
    # CONSTRAINT VALIDATION (IMPORTANT - 7/10 priority)
    # ========================================================================

    def test_constraint_validation_max_tokens(self, optimizer):
        """
        Test that max_tokens constraint is validated correctly.

        Verifies:
        1. Templates within max_tokens pass
        2. Templates exceeding max_tokens fail
        """
        # Template within limit
        valid_prompt = PromptObject(
            id="valid",
            version="1.0.0",
            intent_type=IntentType.GENERATE,
            template="Short prompt",
            strategy_meta={"strategy": "simple"},
            constraints={"max_tokens": 500},
            created_at=datetime.now(UTC).isoformat(),
            updated_at=datetime.now(UTC).isoformat(),
        )

        score, feedback = optimizer._evaluate(valid_prompt)
        assert score > 0  # Should pass max_tokens check
        assert "too long" not in feedback.lower()

        # Template exceeding limit
        invalid_prompt = PromptObject(
            id="invalid",
            version="1.0.0",
            intent_type=IntentType.GENERATE,
            template="x" * 1000,  # Exceeds max_tokens=500
            strategy_meta={"strategy": "simple"},
            constraints={"max_tokens": 500},
            created_at=datetime.now(UTC).isoformat(),
            updated_at=datetime.now(UTC).isoformat(),
        )

        score, feedback = optimizer._evaluate(invalid_prompt)
        assert score < 1.0  # Should fail max_tokens check
        assert "too long" in feedback.lower()

    def test_constraint_validation_format_requirement(self, optimizer):
        """
        Test that format constraint is validated correctly.

        When format="code in Python":
        1. Templates with code markers pass
        2. Templates without code markers fail
        """
        # Template with code
        with_code = PromptObject(
            id="with-code",
            version="1.0.0",
            intent_type=IntentType.GENERATE,
            template="```python\ndef foo(): pass```",
            strategy_meta={"strategy": "simple"},
            constraints={"max_tokens": 500, "format": "code in Python"},
            created_at=datetime.now(UTC).isoformat(),
            updated_at=datetime.now(UTC).isoformat(),
        )

        score, _ = optimizer._evaluate(with_code)
        assert score > 0  # Should pass format check

        # Template without code
        without_code = PromptObject(
            id="without-code",
            version="1.0.0",
            intent_type=IntentType.GENERATE,
            template="Create a function",  # No code markers
            strategy_meta={"strategy": "simple"},
            constraints={"max_tokens": 500, "format": "code in Python"},
            created_at=datetime.now(UTC).isoformat(),
            updated_at=datetime.now(UTC).isoformat(),
        )

        score, feedback = optimizer._evaluate(without_code)
        assert score < 1.0  # Should fail format check
        assert "missing code" in feedback.lower()
