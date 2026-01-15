"""
Error handling and edge case tests for critical services.

Tests cover:
- KNNProvider: empty catalog, invalid queries, edge cases
- ReflexionService: executor failures, edge cases
- NLaCStrategy: validation edge cases
"""
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from eval.src.strategies.nlac_strategy import NLaCStrategy
from hemdov.domain.services.knn_provider import KNNProvider
from hemdov.domain.services.oprop_optimizer import OPROOptimizer
from hemdov.domain.services.reflexion_service import ReflexionService

# ============================================================================
# KNNProvider Error Handling Tests
# ============================================================================

class TestKNNProviderErrorHandling:
    """Test KNNProvider error handling and edge cases."""

    def test_knn_provider_with_empty_catalog(self):
        """KNNProvider should raise ValueError when catalog is empty."""
        # Create temporary empty catalog
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            import json
            json.dump([], f)
            temp_path = f.name

        try:
            with pytest.raises(ValueError, match="No valid examples found"):
                provider = KNNProvider(catalog_path=Path(temp_path))
        finally:
            Path(temp_path).unlink()

    def test_knn_provider_with_invalid_catalog_path(self):
        """KNNProvider should raise FileNotFoundError when catalog missing."""
        with pytest.raises(FileNotFoundError, match="ComponentCatalog not found"):
            provider = KNNProvider(catalog_path=Path("/nonexistent/path.json"))

    def test_knn_provider_with_zero_k(self):
        """KNNProvider returns all examples when k=0 (current behavior)."""
        provider = KNNProvider(catalog_path=Path("datasets/exports/unified-fewshot-pool-v2.json"))
        examples = provider.find_examples(
            intent="debug",
            complexity="simple",
            k=0
        )
        # Current behavior: returns all available examples when k=0
        # (Note: this could be considered a bug, but test documents current behavior)
        assert len(examples) > 0

    def test_knn_provider_with_large_k(self):
        """KNNProvider should handle k larger than catalog size."""
        provider = KNNProvider(catalog_path=Path("datasets/exports/unified-fewshot-pool-v2.json"))
        examples = provider.find_examples(
            intent="debug",
            complexity="simple",
            k=99999  # Much larger than catalog
        )
        # Should return all available examples, not crash
        assert isinstance(examples, list)


# ============================================================================
# OPROOptimizer Edge Cases
# ============================================================================

class TestOPROOptimizerEdgeCases:
    """Test OPROOptimizer input validation."""

    def test_opro_with_none_prompt_obj(self):
        """OPROOptimizer should raise ValueError when prompt_obj is None."""
        optimizer = OPROOptimizer(llm_client=None)

        with pytest.raises(ValueError, match="prompt_obj cannot be None"):
            optimizer.run_loop(prompt_obj=None)


# ============================================================================
# ReflexionService Edge Cases
# ============================================================================

class TestReflexionServiceEdgeCases:
    """Test ReflexionService edge cases."""

    def test_reflexion_with_none_prompt(self):
        """Reflexion should raise ValueError when prompt is None."""
        class MockLLM:
            def generate(self, prompt: str, **kwargs):
                return "def test():\n    return 1"

        reflexion = ReflexionService(llm_client=MockLLM())

        with pytest.raises(ValueError, match="prompt and error_type cannot be None"):
            reflexion.refine(
                prompt=None,
                error_type="Error"
            )

    def test_reflexion_with_empty_prompt(self):
        """Reflexion should raise ValueError when prompt is empty."""
        class MockLLM:
            def generate(self, prompt: str, **kwargs):
                return "def test():\n    return 1"

        reflexion = ReflexionService(llm_client=MockLLM())

        with pytest.raises(ValueError, match="prompt cannot be empty"):
            reflexion.refine(
                prompt="   ",
                error_type="Error"
            )

    def test_reflexion_with_invalid_max_iterations(self):
        """Reflexion should raise ValueError when max_iterations < 1."""
        class MockLLM:
            def generate(self, prompt: str, **kwargs):
                return "def test():\n    return 1"

        reflexion = ReflexionService(llm_client=MockLLM())

        with pytest.raises(ValueError, match="max_iterations must be at least 1"):
            reflexion.refine(
                prompt="Fix this",
                error_type="Error",
                max_iterations=0
            )

    def test_reflexion_with_executor_always_failing(self):
        """Reflexion should stop when executor always fails."""
        class MockLLM:
            def generate(self, prompt: str, **kwargs):
                return "def test():\\n    return 1"

        class AlwaysFailingExecutor:
            def execute(self, code: str):
                raise RuntimeError("Always fails")

        reflexion = ReflexionService(
            llm_client=MockLLM(),
            executor=AlwaysFailingExecutor()
        )

        result = reflexion.refine(
            prompt="Fix this",
            error_type="RuntimeError",
            max_iterations=3
        )

        # Should reach max_iterations
        assert result.iteration_count == 3
        assert result.success == False

    def test_reflexion_without_executor(self):
        """Reflexion should work without executor (assumes success)."""
        class MockLLM:
            def generate(self, prompt: str, **kwargs):
                return "def test():\\n    return 42"

        reflexion = ReflexionService(llm_client=MockLLM(), executor=None)

        result = reflexion.refine(
            prompt="Fix this",
            error_type="Error",
            max_iterations=2
        )

        # Should converge immediately without executor validation
        assert result.iteration_count == 1
        assert result.success == True

    def test_reflexion_with_max_iterations_1(self):
        """Reflexion should respect max_iterations=1."""
        class MockLLM:
            def generate(self, prompt: str, **kwargs):
                return "code"

        reflexion = ReflexionService(llm_client=MockLLM())

        result = reflexion.refine(
            prompt="Fix this",
            error_type="Error",
            max_iterations=1
        )

        # Should only run once
        assert result.iteration_count == 1


# ============================================================================
# NLaCStrategy Validation Tests
# ============================================================================

class TestNLaCStrategyValidation:
    """Test NLaCStrategy input validation."""

    def test_validate_inputs_with_none_idea(self):
        """Should raise ValueError when idea is None."""
        strategy = NLaCStrategy(llm_client=None, enable_optimization=False)

        with pytest.raises(ValueError, match="must be non-None"):
            strategy._validate_inputs(None, "some context")

    def test_validate_inputs_with_none_context(self):
        """Should raise ValueError when context is None."""
        strategy = NLaCStrategy(llm_client=None, enable_optimization=False)

        with pytest.raises(ValueError, match="must be non-None"):
            strategy._validate_inputs("some idea", None)

    def test_validate_inputs_with_non_string_idea(self):
        """Should raise TypeError when idea is not string."""
        strategy = NLaCStrategy(llm_client=None, enable_optimization=False)

        with pytest.raises(TypeError, match="must be strings"):
            strategy._validate_inputs(123, "context")

    def test_validate_inputs_with_non_string_context(self):
        """Should raise TypeError when context is not string."""
        strategy = NLaCStrategy(llm_client=None, enable_optimization=False)

        with pytest.raises(TypeError, match="must be strings"):
            strategy._validate_inputs("idea", 123)

    def test_validate_inputs_with_empty_idea(self):
        """Should raise ValueError when idea is empty/whitespace."""
        strategy = NLaCStrategy(llm_client=None, enable_optimization=False)

        with pytest.raises(ValueError, match="cannot be empty"):
            strategy._validate_inputs("   ", "context")

    def test_validate_inputs_with_valid_inputs(self):
        """Should not raise with valid inputs."""
        strategy = NLaCStrategy(llm_client=None, enable_optimization=False)

        # Should not raise
        strategy._validate_inputs("valid idea", "valid context")


# ============================================================================
# NLaCStrategy Integration Tests
# ============================================================================

class TestNLaCStrategyIntegration:
    """Integration tests for full NLaCStrategy pipeline."""

    def test_nlac_strategy_routes_debug_to_reflexion(self):
        """DEBUG intent should route to ReflexionService."""
        from unittest.mock import patch

        class MockLLM:
            def generate(self, prompt: str, **kwargs):
                return "def fixed():\\n    return 42"

        mock_llm = MockLLM()
        strategy = NLaCStrategy(
            llm_client=mock_llm,
            enable_optimization=False,
            knn_provider=None
        )

        # Mock ReflexionService
        with patch.object(strategy, 'reflexion') as mock_reflexion:
            mock_reflexion.refine.return_value = Mock(
                code="refined code",
                iteration_count=1,
                success=True,
                error_history=[]
            )

            result = strategy.improve("Debug this error", "ZeroDivisionError in foo")

            # Verify Reflexion was called
            mock_reflexion.refine.assert_called_once()
            # Verify intent extraction worked
            call_args = mock_reflexion.refine.call_args
            assert call_args[1]['error_type'] == 'ZeroDivisionError'

    def test_nlac_strategy_routes_generate_to_opro(self):
        """GENERATE intent should route to OPROOptimizer when optimization enabled."""

        class MockLLM:
            def generate(self, prompt: str, **kwargs):
                return "improved prompt"

        mock_llm = MockLLM()
        strategy = NLaCStrategy(
            llm_client=mock_llm,
            enable_optimization=True,
            knn_provider=None
        )

        # Mock OPROOptimizer
        with patch.object(strategy, 'optimizer') as mock_optimizer:
            mock_optimizer.run_loop.return_value = Mock(
                final_instruction="optimized instruction",
                iteration_count=1
            )

            result = strategy.improve("Create API endpoint", "Need REST API")

            # Verify OPRO was called
            mock_optimizer.run_loop.assert_called_once()

    def test_extract_error_type_fallback(self):
        """Should return 'Error' when no known error type found."""
        strategy = NLaCStrategy(llm_client=None)

        error_type = strategy._extract_error_type("Some random issue")

        assert error_type == "Error"

    def test_extract_error_type_known_error(self):
        """Should extract known error types from context."""
        strategy = NLaCStrategy(llm_client=None)

        assert strategy._extract_error_type("Fix ZeroDivisionError") == "ZeroDivisionError"
        assert strategy._extract_error_type("Handle TypeError") == "TypeError"
        assert strategy._extract_error_type("ValueError occurred") == "ValueError"
