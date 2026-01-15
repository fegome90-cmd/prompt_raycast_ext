"""
Tests for NLaC Pydantic Models.

Validates all NLaC domain models with comprehensive coverage of:
- Model creation and defaults
- Field validation
- Edge cases and error conditions
- JSON serialization/deserialization
"""

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

from hemdov.domain.dto.nlac_models import (
    IntentType,
    NLaCInputs,
    NLaCRequest,
    NLaCResponse,
    OPROIteration,
    OptimizeResponse,
    PromptObject,
)

# ============================================================================
# NLaCInputs Tests
# ============================================================================

class TestNLaCInputs:
    """Test NLaCInputs model (optional structured inputs)."""

    def test_default_values(self):
        """Test NLaCInputs with all default values."""
        inputs = NLaCInputs()
        assert inputs.code_snippet is None
        assert inputs.error_log is None
        assert inputs.target_language is None
        assert inputs.target_framework is None
        assert inputs.context_files == []

    def test_with_code_snippet(self):
        """Test NLaCInputs with code snippet."""
        inputs = NLaCInputs(code_snippet="def foo(): pass")
        assert inputs.code_snippet == "def foo(): pass"

    def test_with_error_log(self):
        """Test NLaCInputs with error log."""
        inputs = NLaCInputs(error_log="NameError: name 'x' is not defined")
        assert "NameError" in inputs.error_log

    def test_with_target_language(self):
        """Test NLaCInputs with target language."""
        inputs = NLaCInputs(target_language="python")
        assert inputs.target_language == "python"

    def test_with_context_files(self):
        """Test NLaCInputs with context files."""
        inputs = NLaCInputs(context_files=["src/main.py", "tests/test_main.py"])
        assert len(inputs.context_files) == 2
        assert "src/main.py" in inputs.context_files

    def test_context_files_filters_empty_strings(self):
        """Test that context_files filters out empty strings."""
        inputs = NLaCInputs(context_files=["file1.py", "", "file2.py", None, "   "])
        assert inputs.context_files == ["file1.py", "file2.py"]

    def test_full_inputs(self):
        """Test NLaCInputs with all fields populated."""
        inputs = NLaCInputs(
            code_snippet="function test() {}",
            error_log="ReferenceError: test is not defined",
            target_language="javascript",
            target_framework="React",
            context_files=["src/App.tsx"]
        )
        assert inputs.code_snippet == "function test() {}"
        assert inputs.target_framework == "React"
        assert len(inputs.context_files) == 1


# ============================================================================
# NLaCRequest Tests
# ============================================================================

class TestNLaCRequest:
    """Test NLaCRequest model (main API request)."""

    def test_minimal_request_legacy_mode(self):
        """Test minimal request in legacy mode."""
        request = NLaCRequest(idea="Create a function")
        assert request.idea == "Create a function"
        assert request.context == ""
        assert request.mode == "legacy"
        assert request.enable_optimization is False
        assert request.max_iterations == 3

    def test_minimal_request_nlac_mode(self):
        """Test minimal request in nlac mode."""
        request = NLaCRequest(idea="Debug this", mode="nlac")
        assert request.mode == "nlac"
        # inputs is optional even in nlac mode
        assert request.inputs is None

    def test_with_context(self):
        """Test request with context."""
        request = NLaCRequest(
            idea="Fix the bug",
            context="Production environment, high priority"
        )
        assert "Production" in request.context

    def test_with_structured_inputs(self):
        """Test request with structured NLaCInputs."""
        request = NLaCRequest(
            idea="Debug this error",
            inputs=NLaCInputs(
                code_snippet="def foo():\n    return x",
                error_log="NameError: name 'x' is not defined"
            )
        )
        assert request.inputs.code_snippet == "def foo():\n    return x"
        assert "NameError" in request.inputs.error_log

    def test_optimization_enabled(self):
        """Test request with optimization enabled."""
        request = NLaCRequest(
            idea="Optimize this",
            mode="nlac",
            enable_optimization=True,
            max_iterations=5
        )
        assert request.enable_optimization is True
        assert request.max_iterations == 5
        assert request.target_score == 1.0

    def test_custom_target_score(self):
        """Test request with custom target score."""
        request = NLaCRequest(
            idea="Test",
            enable_optimization=True,
            target_score=0.85
        )
        assert request.target_score == 0.85

    def test_mode_literal_validation_valid(self):
        """Test that mode accepts valid literal values."""
        for mode in ["legacy", "nlac"]:
            request = NLaCRequest(idea="test", mode=mode)
            assert request.mode == mode

    def test_mode_literal_validation_invalid(self):
        """Test that mode rejects invalid values."""
        with pytest.raises(ValidationError):
            NLaCRequest(idea="test", mode="invalid")

    def test_idea_trims_whitespace(self):
        """Test that idea is trimmed of whitespace."""
        request = NLaCRequest(idea="   Create a function   ")
        assert request.idea == "Create a function"
        assert request.idea[0] != " "
        assert request.idea[-1] != " "

    def test_idea_cannot_be_empty(self):
        """Test that empty idea raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            NLaCRequest(idea="")
        assert "idea" in str(exc_info.value).lower()

    def test_idea_cannot_be_whitespace_only(self):
        """Test that whitespace-only idea raises ValidationError."""
        with pytest.raises(ValidationError):
            NLaCRequest(idea="   \n\t   ")

    def test_max_iterations_minimum(self):
        """Test that max_iterations respects minimum value."""
        request = NLaCRequest(idea="test", max_iterations=1)
        assert request.max_iterations == 1

    def test_max_iterations_maximum(self):
        """Test that max_iterations respects maximum value."""
        request = NLaCRequest(idea="test", max_iterations=5)
        assert request.max_iterations == 5

    def test_max_iterations_exceeds_limit(self):
        """Test that max_iterations > 5 raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            NLaCRequest(idea="test", max_iterations=6)
        assert "max_iterations" in str(exc_info.value).lower()
        assert "5" in str(exc_info.value)

    def test_target_score_range_valid(self):
        """Test that target_score accepts valid range [0.0, 1.0]."""
        for score in [0.0, 0.5, 0.99, 1.0]:
            request = NLaCRequest(idea="test", target_score=score)
            assert request.target_score == score

    def test_target_score_below_minimum(self):
        """Test that target_score < 0.0 raises ValidationError."""
        with pytest.raises(ValidationError):
            NLaCRequest(idea="test", target_score=-0.1)

    def test_target_score_above_maximum(self):
        """Test that target_score > 1.0 raises ValidationError."""
        with pytest.raises(ValidationError):
            NLaCRequest(idea="test", target_score=1.1)

    def test_full_request_serialization(self):
        """Test that full request serializes to JSON correctly."""
        request = NLaCRequest(
            idea="Debug this",
            context="Important",
            mode="nlac",
            inputs=NLaCInputs(
                code_snippet="def test(): pass",
                error_log="Error"
            ),
            enable_optimization=True,
            max_iterations=3,
            target_score=0.9
        )
        data = request.model_dump()
        assert data["idea"] == "Debug this"
        assert data["mode"] == "nlac"
        assert data["inputs"]["code_snippet"] == "def test(): pass"


# ============================================================================
# PromptObject Tests
# ============================================================================

class TestPromptObject:
    """Test PromptObject model (structured prompt representation)."""

    def test_minimal_prompt_object(self):
        """Test minimal PromptObject creation."""
        prompt_id = str(uuid4())
        now = datetime.now(UTC).isoformat()

        prompt = PromptObject(
            id=prompt_id,
            version="1.0.0",
            intent_type=IntentType.GENERATE,
            template="Generate a function to {task}",
            created_at=now,
            updated_at=now
        )
        assert prompt.id == prompt_id
        assert prompt.version == "1.0.0"
        assert prompt.intent_type == IntentType.GENERATE
        assert prompt.is_active is True
        assert prompt.strategy_meta == {}

    def test_with_strategy_metadata(self):
        """Test PromptObject with strategy metadata."""
        prompt = PromptObject(
            id=str(uuid4()),
            version="1.0.0",
            intent_type=IntentType.DEBUG,
            template="Debug: {code}",
            strategy_meta={
                "complexity": "low",
                "strategy": "SimpleStrategy",
                "confidence": 0.95
            },
            created_at=datetime.now(UTC).isoformat(),
            updated_at=datetime.now(UTC).isoformat()
        )
        assert prompt.strategy_meta["strategy"] == "SimpleStrategy"
        assert prompt.strategy_meta["confidence"] == 0.95

    def test_with_constraints(self):
        """Test PromptObject with constraints."""
        prompt = PromptObject(
            id=str(uuid4()),
            version="1.0.0",
            intent_type=IntentType.REFACTOR,
            template="Refactor this code",
            constraints={
                "max_tokens": 500,
                "format": "markdown",
                "include_tests": True
            },
            created_at=datetime.now(UTC).isoformat(),
            updated_at=datetime.now(UTC).isoformat()
        )
        assert prompt.constraints["max_tokens"] == 500
        assert prompt.constraints["include_tests"] is True

    def test_is_active_flag(self):
        """Test is_active flag."""
        prompt_active = PromptObject(
            id=str(uuid4()),
            version="1.0.0",
            intent_type=IntentType.GENERATE,
            template="Test",
            is_active=True,
            created_at=datetime.now(UTC).isoformat(),
            updated_at=datetime.now(UTC).isoformat()
        )
        prompt_inactive = PromptObject(
            id=str(uuid4()),
            version="1.0.0",
            intent_type=IntentType.GENERATE,
            template="Test",
            is_active=False,
            created_at=datetime.now(UTC).isoformat(),
            updated_at=datetime.now(UTC).isoformat()
        )
        assert prompt_active.is_active is True
        assert prompt_inactive.is_active is False

    def test_all_intent_types(self):
        """Test all IntentType enum values."""
        now = datetime.now(UTC).isoformat()
        for intent in [IntentType.GENERATE, IntentType.DEBUG, IntentType.REFACTOR, IntentType.EXPLAIN]:
            prompt = PromptObject(
                id=str(uuid4()),
                version="1.0.0",
                intent_type=intent,
                template=f"Template for {intent}",
                created_at=now,
                updated_at=now
            )
            assert prompt.intent_type == intent

    def test_template_cannot_be_empty(self):
        """Test that empty template raises ValidationError."""
        with pytest.raises(ValidationError):
            PromptObject(
                id=str(uuid4()),
                version="1.0.0",
                intent_type=IntentType.GENERATE,
                template="   ",
                created_at=datetime.now(UTC).isoformat(),
                updated_at=datetime.now(UTC).isoformat()
            )

    def test_metadata_defaults_to_empty_dict(self):
        """Test that metadata fields default to empty dict when None."""
        prompt = PromptObject(
            id=str(uuid4()),
            version="1.0.0",
            intent_type=IntentType.GENERATE,
            template="Test",
            strategy_meta=None,  # Explicitly None
            constraints=None,
            created_at=datetime.now(UTC).isoformat(),
            updated_at=datetime.now(UTC).isoformat()
        )
        assert prompt.strategy_meta == {}
        assert prompt.constraints == {}


# ============================================================================
# OPROIteration Tests
# ============================================================================

class TestOPROIteration:
    """Test OPROIteration model (single optimization iteration)."""

    def test_minimal_iteration(self):
        """Test minimal OPROIteration."""
        iteration = OPROIteration(
            iteration_number=1,
            meta_prompt_used="Optimize this prompt",
            generated_instruction="Improved prompt",
            score=0.85
        )
        assert iteration.iteration_number == 1
        assert iteration.score == 0.85
        assert iteration.feedback is None

    def test_with_feedback(self):
        """Test OPROIteration with feedback."""
        iteration = OPROIteration(
            iteration_number=2,
            meta_prompt_used="Improve",
            generated_instruction="Better prompt",
            score=0.92,
            feedback="Good improvement, focus on clarity"
        )
        assert iteration.feedback is not None
        assert "clarity" in iteration.feedback

    def test_iteration_number_positive(self):
        """Test that iteration_number must be >= 1."""
        with pytest.raises(ValidationError):
            OPROIteration(
                iteration_number=0,
                meta_prompt_used="Test",
                generated_instruction="Test",
                score=0.5
            )

    def test_score_range_valid(self):
        """Test that score accepts valid range [0.0, 1.0]."""
        for score in [0.0, 0.33, 0.66, 1.0]:
            iteration = OPROIteration(
                iteration_number=1,
                meta_prompt_used="Test",
                generated_instruction="Test",
                score=score
            )
            assert iteration.score == score

    def test_score_below_minimum(self):
        """Test that score < 0.0 raises ValidationError."""
        with pytest.raises(ValidationError):
            OPROIteration(
                iteration_number=1,
                meta_prompt_used="Test",
                generated_instruction="Test",
                score=-0.1
            )

    def test_score_above_maximum(self):
        """Test that score > 1.0 raises ValidationError."""
        with pytest.raises(ValidationError):
            OPROIteration(
                iteration_number=1,
                meta_prompt_used="Test",
                generated_instruction="Test",
                score=1.1
            )


# ============================================================================
# OptimizeResponse Tests
# ============================================================================

class TestOptimizeResponse:
    """Test OptimizeResponse model (OPRO optimization result)."""

    def test_minimal_response(self):
        """Test minimal OptimizeResponse."""
        response = OptimizeResponse(
            prompt_id=str(uuid4()),
            final_instruction="Optimized prompt",
            final_score=0.95,
            iteration_count=3
        )
        assert response.final_score == 0.95
        assert response.iteration_count == 3
        assert response.early_stopped is False
        assert response.trajectory == []

    def test_with_trajectory(self):
        """Test OptimizeResponse with full trajectory."""
        iterations = [
            OPROIteration(
                iteration_number=1,
                meta_prompt_used="Optimize",
                generated_instruction="V1",
                score=0.70
            ),
            OPROIteration(
                iteration_number=2,
                meta_prompt_used="Optimize",
                generated_instruction="V2",
                score=0.85
            ),
            OPROIteration(
                iteration_number=3,
                meta_prompt_used="Optimize",
                generated_instruction="V3",
                score=0.95
            ),
        ]
        response = OptimizeResponse(
            prompt_id=str(uuid4()),
            final_instruction="V3",
            final_score=0.95,
            iteration_count=3,
            trajectory=iterations
        )
        assert len(response.trajectory) == 3
        assert response.trajectory[0].score == 0.70
        assert response.trajectory[-1].score == 0.95

    def test_early_stopped_flag(self):
        """Test early_stopped flag."""
        response = OptimizeResponse(
            prompt_id=str(uuid4()),
            final_instruction="Target reached",
            final_score=1.0,
            iteration_count=2,
            early_stopped=True
        )
        assert response.early_stopped is True

    def test_with_improved_prompt(self):
        """Test OptimizeResponse with improved_prompt."""
        response = OptimizeResponse(
            prompt_id=str(uuid4()),
            final_instruction="Optimized",
            final_score=0.9,
            iteration_count=1,
            improved_prompt="# Full rendered prompt\n\nOptimized"
        )
        assert response.improved_prompt is not None
        assert "rendered" in response.improved_prompt.lower()

    def test_with_metadata(self):
        """Test OptimizeResponse with timing and model metadata."""
        response = OptimizeResponse(
            prompt_id=str(uuid4()),
            final_instruction="Result",
            final_score=0.88,
            iteration_count=3,
            total_latency_ms=5500,
            model="deepseek-chat"
        )
        assert response.total_latency_ms == 5500
        assert response.model == "deepseek-chat"

    def test_iteration_count_minimum(self):
        """Test that iteration_count must be >= 1."""
        with pytest.raises(ValidationError):
            OptimizeResponse(
                prompt_id=str(uuid4()),
                final_instruction="Test",
                final_score=0.5,
                iteration_count=0
            )


# ============================================================================
# NLaCResponse Tests
# ============================================================================

class TestNLaCResponse:
    """Test NLaCResponse model (complete API response)."""

    def test_legacy_response(self):
        """Test NLaCResponse in legacy mode (no NLaC fields)."""
        response = NLaCResponse(
            improved_prompt="Improved prompt",
            role="Expert Developer",
            directive="Create a function",
            framework="chain-of-thought",
            guardrails=["Be concise", "Use examples"],
            backend="zero-shot"
        )
        assert response.improved_prompt == "Improved prompt"
        assert response.prompt_object is None
        assert response.optimization_result is None
        assert response.cache_hit is False

    def test_nlac_response_with_prompt_object(self):
        """Test NLaCResponse with PromptObject."""
        now = datetime.now(UTC).isoformat()
        prompt_obj = PromptObject(
            id=str(uuid4()),
            version="1.0.0",
            intent_type=IntentType.DEBUG,
            template="Debug this code",
            created_at=now,
            updated_at=now
        )
        response = NLaCResponse(
            improved_prompt="Debugged prompt",
            role="Debugger",
            directive="Fix the error",
            framework="chain-of-thought",
            guardrails=["Check syntax"],
            backend="nlac",
            prompt_object=prompt_obj,
            intent_type=IntentType.DEBUG
        )
        assert response.prompt_object is not None
        assert response.intent_type == IntentType.DEBUG
        assert response.backend == "nlac"

    def test_nlac_response_with_optimization(self):
        """Test NLaCResponse with optimization result."""
        opt_result = OptimizeResponse(
            prompt_id=str(uuid4()),
            final_instruction="Optimized",
            final_score=0.95,
            iteration_count=3
        )
        response = NLaCResponse(
            improved_prompt="Optimized prompt",
            role="Expert",
            directive="Create",
            framework="chain-of-thought",
            guardrails=["Safe"],
            backend="nlac",
            optimization_result=opt_result
        )
        assert response.optimization_result is not None
        assert response.optimization_result.final_score == 0.95

    def test_cache_hit_flag(self):
        """Test cache_hit flag."""
        response_cached = NLaCResponse(
            improved_prompt="Cached result",
            role="Expert",
            directive="Test",
            framework="chain-of-thought",
            guardrails=["Safe"],
            cache_hit=True
        )
        response_uncached = NLaCResponse(
            improved_prompt="New result",
            role="Expert",
            directive="Test",
            framework="chain-of-thought",
            guardrails=["Safe"],
            cache_hit=False
        )
        assert response_cached.cache_hit is True
        assert response_uncached.cache_hit is False

    def test_optional_fields(self):
        """Test optional fields (reasoning, confidence)."""
        response_with_optional = NLaCResponse(
            improved_prompt="Prompt",
            role="Expert",
            directive="Create",
            framework="chain-of-thought",
            guardrails=["Safe"],
            reasoning="Step-by-step reasoning",
            confidence=0.92
        )
        assert response_with_optional.reasoning is not None
        assert response_with_optional.confidence == 0.92

        response_without_optional = NLaCResponse(
            improved_prompt="Prompt",
            role="Expert",
            directive="Create",
            framework="chain-of-thought",
            guardrails=["Safe"]
        )
        assert response_without_optional.reasoning is None
        assert response_without_optional.confidence is None

    def test_guardrails_is_list(self):
        """Test that guardrails is a list."""
        response = NLaCResponse(
            improved_prompt="Test",
            role="Expert",
            directive="Create",
            framework="chain-of-thought",
            guardrails=["Rule 1", "Rule 2", "Rule 3"]
        )
        assert isinstance(response.guardrails, list)
        assert len(response.guardrails) == 3


# ============================================================================
# Integration Tests
# ============================================================================

class TestModelIntegration:
    """Integration tests for model interactions."""

    def test_request_to_response_workflow(self):
        """Test workflow from NLaCRequest to NLaCResponse."""
        # Create request
        request = NLaCRequest(
            idea="Debug this error",
            mode="nlac",
            inputs=NLaCInputs(
                code_snippet="def test(): return x",
                error_log="NameError"
            ),
            enable_optimization=True
        )

        # Simulate processing (would be done by actual API)
        response = NLaCResponse(
            improved_prompt="Here's the fixed code...",
            role="Expert Debugger",
            directive="Fix the NameError",
            framework="chain-of-thought",
            guardrails=["Check variable definitions"],
            backend="nlac",
            intent_type=IntentType.DEBUG,
            confidence=0.95
        )

        assert response.intent_type == IntentType.DEBUG
        assert response.backend == "nlac"

    def test_optimization_trajectory_serialization(self):
        """Test that optimization trajectory serializes correctly."""
        iterations = [
            OPROIteration(
                iteration_number=i,
                meta_prompt_used="Optimize",
                generated_instruction=f"Version {i}",
                score=0.5 + (i * 0.15)
            )
            for i in range(1, 4)
        ]

        opt_response = OptimizeResponse(
            prompt_id=str(uuid4()),
            final_instruction="Version 3",
            final_score=0.95,
            iteration_count=3,
            trajectory=iterations
        )

        # Verify serialization
        data = opt_response.model_dump()
        assert len(data["trajectory"]) == 3
        assert data["trajectory"][0]["score"] == 0.65
        assert data["trajectory"][-1]["score"] == 0.95
