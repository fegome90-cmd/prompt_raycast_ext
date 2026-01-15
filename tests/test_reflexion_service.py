"""
Tests for ReflexionService service.

Tests iterative refinement loop for DEBUG scenario (MultiAIGCD Scenario II).
"""
from hemdov.domain.services.reflexion_service import ReflexionService


class MockLLMClient:
    """Mock LLM for testing"""
    def generate(self, prompt: str, **kwargs) -> str:
        # Return different responses based on prompt content
        if "Error:" in prompt:
            return "def fixed_version():\n    return 42  # Fixed division by zero"
        return "def buggy_version():\n    return 1/0"


def test_reflexion_generates_code():
    """Reflexion should generate initial code"""
    service = ReflexionService(llm_client=MockLLMClient())

    result = service.refine(
        prompt="Fix this error",
        error_type="ZeroDivisionError",
        max_iterations=2
    )

    assert result.code is not None
    assert result.iteration_count == 1


def test_reflexion_retries_on_error():
    """Reflexion should retry with error feedback"""
    class FailingFirstMockLLM:
        def __init__(self):
            self.call_count = 0

        def generate(self, prompt: str, **kwargs) -> str:
            self.call_count += 1
            if self.call_count == 1:
                return "def buggy():\n    return 1/0"
            # Second call sees error feedback
            if "Error:" in prompt:
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
    assert result.iteration_count == 2  # Should retry once
    assert "fixed" in result.code


def test_reflexion_stops_at_max_iterations():
    """Reflexion should stop at max_iterations even if not perfect"""
    class AlwaysFailingMockLLM:
        def __init__(self):
            self.call_count = 0

        def generate(self, prompt: str, **kwargs) -> str:
            self.call_count += 1
            return "def still_buggy():\n    return 1/0"

    def always_failing_executor(code):
        """Executor that always fails"""
        raise RuntimeError("Still broken")

    service = ReflexionService(llm_client=AlwaysFailingMockLLM(), executor=always_failing_executor)

    result = service.refine(
        prompt="Fix this",
        error_type="ZeroDivisionError",
        max_iterations=3
    )

    assert result.iteration_count == 3  # Should stop at max
    assert result.success == False  # Should not converge
