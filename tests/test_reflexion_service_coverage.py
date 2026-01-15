"""
Coverage tests for ReflexionService.

This file provides comprehensive coverage tests for the domain service
located at hemdov/domain/services/reflexion_service.py.

Tests cover:
- Reflection with errors (error feedback loop)
- Reflection without errors (clean generation)
- Reflection metadata generation
- Max reflections limit
- Input validation
- LLM failure handling
"""

import pytest
from hemdov.domain.services.reflexion_service import ReflexionService, ReflexionResult
from hemdov.domain.services.llm_protocol import LLMClient


class TestReflexionServiceCoverage:
    """Comprehensive coverage tests for ReflexionService domain service."""

    # ========================================================================
    # REFLECTION WITH ERRORS
    # ========================================================================

    def test_reflect_with_errors(self):
        """
        Test reflection loop with error feedback.

        Verifies that:
        1. Initial code generation happens
        2. Execution fails with error
        3. Error is fed back for retry
        4. Second iteration succeeds
        """
        class FailingFirstMockLLM:
            def __init__(self):
                self.call_count = 0

            def generate(self, prompt: str, **kwargs) -> str:
                self.call_count += 1
                if self.call_count == 1:
                    return "def buggy():\n    return 1/0"
                # Second call sees error feedback
                return "def fixed():\n    return 42"

        def mock_executor(code):
            """Executor that fails on buggy code, succeeds on fixed"""
            if "buggy" in code:
                raise RuntimeError("Code still has bugs")
            return True  # Success

        service = ReflexionService(llm_client=FailingFirstMockLLM(), executor=mock_executor)

        result = service.refine(
            prompt="Fix this division by zero",
            error_type="ZeroDivisionError",
            max_iterations=2
        )

        assert result.code is not None
        assert result.success is True
        assert result.iteration_count == 2  # Should retry once
        assert "fixed" in result.code
        assert len(result.error_history) == 1  # One error was encountered
        assert result.final_error is None  # Should have no final error on success

    # ========================================================================
    # REFLECTION WITHOUT ERRORS
    # ========================================================================

    def test_reflect_without_errors(self):
        """
        Test reflection without initial errors (clean generation).

        Verifies that:
        1. Code is generated successfully
        2. No errors are encountered
        3. Loop exits early with success
        4. Error history is empty
        """
        class SuccessMockLLM:
            def generate(self, prompt: str, **kwargs) -> str:
                return "def working_code():\n    return 42"

        def mock_executor(code):
            """Executor that always succeeds"""
            return True

        service = ReflexionService(llm_client=SuccessMockLLM(), executor=mock_executor)

        result = service.refine(
            prompt="Create a function",
            error_type="CodeRequest",
            max_iterations=3
        )

        assert result.code is not None
        assert result.success is True
        assert result.iteration_count == 1  # Should succeed on first try
        assert len(result.error_history) == 0  # No errors
        assert result.final_error is None

    # ========================================================================
    # REFLECTION METADATA GENERATION
    # ========================================================================

    def test_reflection_metadata_generation(self):
        """
        Test that ReflexionResult metadata is generated correctly.

        Verifies that all fields are populated:
        - code: Final generated code
        - iteration_count: Number of iterations performed
        - success: Whether convergence was achieved
        - error_history: List of errors encountered
        - final_error: Last error if not converged
        """
        class TwoIterationMockLLM:
            def __init__(self):
                self.call_count = 0

            def generate(self, prompt: str, **kwargs) -> str:
                self.call_count += 1
                return f"# Code iteration {self.call_count}"

        def mock_executor(code):
            """Fails first time, succeeds second"""
            if "iteration 1" in code:
                raise ValueError("First attempt failed")
            return True

        service = ReflexionService(llm_client=TwoIterationMockLLM(), executor=mock_executor)

        result = service.refine(
            prompt="Generate code",
            error_type="ValueError",
            error_message="Invalid value",
            max_iterations=2
        )

        # Verify all metadata fields
        assert result.code is not None
        assert "iteration 2" in result.code
        assert result.iteration_count == 2
        assert result.success is True
        assert isinstance(result.error_history, list)
        assert len(result.error_history) == 1
        assert "First attempt failed" in result.error_history[0]
        assert result.final_error is None  # Success means no final error

    # ========================================================================
    # MAX REFLECTIONS LIMIT
    # ========================================================================

    def test_max_reflections_limit(self):
        """
        Test that reflection stops at max_iterations even if not converged.

        Verifies that:
        1. Loop stops at max_iterations
        2. Result indicates failure
        3. Final error is set
        4. All iterations were attempted
        """
        class AlwaysFailingMockLLM:
            def generate(self, prompt: str, **kwargs) -> str:
                return "def still_buggy():\n    return 1/0"

        def always_failing_executor(code):
            """Executor that always fails"""
            raise RuntimeError("Still broken")

        service = ReflexionService(llm_client=AlwaysFailingMockLLM(), executor=always_failing_executor)

        result = service.refine(
            prompt="Fix this",
            error_type="RuntimeError",
            max_iterations=3
        )

        assert result.iteration_count == 3  # Should stop at max
        assert result.success is False  # Should not converge
        assert result.code is not None  # Should return last generated code
        assert len(result.error_history) == 3  # One error per iteration
        assert result.final_error is not None  # Should have final error
        assert "Still broken" in result.final_error

    # ========================================================================
    # INPUT VALIDATION
    # ========================================================================

    def test_input_validation_none_prompt(self):
        """Test that None prompt raises ValueError."""
        service = ReflexionService()

        with pytest.raises(ValueError, match="prompt and error_type cannot be None"):
            service.refine(
                prompt=None,
                error_type="Error"
            )

    def test_input_validation_none_error_type(self):
        """Test that None error_type raises ValueError."""
        service = ReflexionService()

        with pytest.raises(ValueError, match="prompt and error_type cannot be None"):
            service.refine(
                prompt="Fix this",
                error_type=None
            )

    def test_input_validation_empty_prompt(self):
        """Test that empty prompt raises ValueError."""
        service = ReflexionService()

        with pytest.raises(ValueError, match="prompt cannot be empty"):
            service.refine(
                prompt="   ",
                error_type="Error"
            )

    def test_input_validation_empty_error_type(self):
        """Test that empty error_type raises ValueError."""
        service = ReflexionService()

        with pytest.raises(ValueError, match="error_type cannot be empty"):
            service.refine(
                prompt="Fix this",
                error_type="   "
            )

    def test_input_validation_invalid_max_iterations(self):
        """Test that max_iterations < 1 raises ValueError."""
        service = ReflexionService()

        with pytest.raises(ValueError, match="max_iterations must be at least 1"):
            service.refine(
                prompt="Fix this",
                error_type="Error",
                max_iterations=0
            )

    def test_input_validation_wrong_type_prompt(self):
        """Test that non-string prompt raises TypeError."""
        service = ReflexionService()

        with pytest.raises(TypeError, match="prompt and error_type must be strings"):
            service.refine(
                prompt=123,
                error_type="Error"
            )

    def test_input_validation_wrong_type_error_type(self):
        """Test that non-string error_type raises TypeError."""
        service = ReflexionService()

        with pytest.raises(TypeError, match="prompt and error_type must be strings"):
            service.refine(
                prompt="Fix this",
                error_type=123
            )

    # ========================================================================
    # LLM FAILURE HANDLING
    # ========================================================================

    def test_llm_connection_error_handling(self):
        """Test that LLM ConnectionError is handled gracefully."""
        class FailingLLM:
            def generate(self, prompt: str, **kwargs) -> str:
                raise ConnectionError("Cannot reach LLM")

        service = ReflexionService(llm_client=FailingLLM())

        result = service.refine(
            prompt="Fix this",
            error_type="Error",
            max_iterations=2
        )

        # Should abort with error details
        assert result.success is False
        assert result.code == ""
        assert result.iteration_count == 1
        assert "LLM generation failed" in result.final_error
        assert "Cannot reach LLM" in result.final_error

    def test_llm_timeout_error_handling(self):
        """Test that LLM TimeoutError is handled gracefully."""
        class TimeoutLLM:
            def generate(self, prompt: str, **kwargs) -> str:
                raise TimeoutError("LLM timed out")

        service = ReflexionService(llm_client=TimeoutLLM())

        result = service.refine(
            prompt="Fix this",
            error_type="Error",
            max_iterations=2
        )

        # Should abort with error details
        assert result.success is False
        assert result.code == ""
        assert "LLM generation failed" in result.final_error
        assert "LLM timed out" in result.final_error

    # ========================================================================
    # NO EXECUTOR (GENERATION ONLY)
    # ========================================================================

    def test_reflection_without_executor(self):
        """
        Test reflection without executor (generation only).

        When no executor is provided:
        1. Code is generated
        2. No execution happens
        3. Assumes success after first iteration
        """
        class SimpleMockLLM:
            def generate(self, prompt: str, **kwargs) -> str:
                return "def generated_code():\n    pass"

        service = ReflexionService(llm_client=SimpleMockLLM(), executor=None)

        result = service.refine(
            prompt="Generate code",
            error_type="CodeRequest",
            max_iterations=3
        )

        # Should succeed without execution
        assert result.code is not None
        assert result.success is True
        assert result.iteration_count == 1  # Stops after first generation
        assert len(result.error_history) == 0

    # ========================================================================
    # ERROR MESSAGE AND CONTEXT HANDLING
    # ========================================================================

    def test_error_message_in_prompt(self):
        """Test that error_message is included in the initial prompt."""
        class PromptCaptureMockLLM:
            def __init__(self):
                self.prompts = []

            def generate(self, prompt: str, **kwargs) -> str:
                self.prompts.append(prompt)
                return "code"

        llm = PromptCaptureMockLLM()
        service = ReflexionService(llm_client=llm, executor=None)

        service.refine(
            prompt="Fix this",
            error_type="ValueError",
            error_message="Invalid value: 42",
            max_iterations=1
        )

        # Verify error message was in prompt
        initial_prompt = llm.prompts[0]
        assert "# Error Details" in initial_prompt
        assert "Invalid value: 42" in initial_prompt

    def test_context_in_prompt(self):
        """Test that initial_context is included in the initial prompt."""
        class PromptCaptureMockLLM:
            def __init__(self):
                self.prompts = []

            def generate(self, prompt: str, **kwargs) -> str:
                self.prompts.append(prompt)
                return "code"

        llm = PromptCaptureMockLLM()
        service = ReflexionService(llm_client=llm, executor=None)

        context_code = "def original():\n    pass"
        service.refine(
            prompt="Improve this",
            error_type="CodeQuality",
            initial_context=context_code,
            max_iterations=1
        )

        # Verify context was in prompt
        initial_prompt = llm.prompts[0]
        assert "# Code Context" in initial_prompt
        assert context_code in initial_prompt

    # ========================================================================
    # FEEDBACK PROMPT STRUCTURE
    # ========================================================================

    def test_feedback_prompt_includes_previous_attempt(self):
        """Test that feedback prompt includes previous code and error."""
        class FeedbackCaptureMockLLM:
            def __init__(self):
                self.second_prompt = None

            def generate(self, prompt: str, **kwargs) -> str:
                if "# Previous Attempt" in prompt:
                    self.second_prompt = prompt
                return "code"

        llm = FeedbackCaptureMockLLM()

        def failing_executor(code):
            raise ValueError("Test error")

        service = ReflexionService(llm_client=llm, executor=failing_executor)

        service.refine(
            prompt="Generate",
            error_type="ValueError",
            max_iterations=2
        )

        # Verify second prompt structure
        assert llm.second_prompt is not None
        assert "# Previous Attempt" in llm.second_prompt
        assert "code" in llm.second_prompt
        assert "# Error" in llm.second_prompt
        assert "Test error" in llm.second_prompt
