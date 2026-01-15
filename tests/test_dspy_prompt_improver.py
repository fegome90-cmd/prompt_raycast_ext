"""
Tests for PromptImprover module.

Following HemDov TDD pattern (RED-GREEN-REFACTOR).
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from unittest.mock import MagicMock, patch

import dspy
import pytest

from eval.src.dspy_prompt_improver import PromptImprover
from eval.src.prompt_improvement_dataset import load_prompt_improvement_examples


class TestPromptImprover:
    """Test suite for PromptImprover module."""

    def test_load_prompt_improvement_examples(self):
        """GREEN: Dataset should load at least 3 examples."""
        examples = load_prompt_improvement_examples()
        assert len(examples) >= 3
        assert all(hasattr(ex, "original_idea") for ex in examples)
        assert all(hasattr(ex, "improved_prompt") for ex in examples)

    def test_prompt_improver_basic_call(self):
        """GREEN: Should improve a raw idea into structured prompt."""

        # Setup mock LM with required attributes
        mock_lm = MagicMock(spec=dspy.LM)
        mock_lm.kwargs = {"temperature": 0.0, "max_tokens": 1000}
        dspy.settings.configure(lm=mock_lm)

        # Setup improver
        improver = PromptImprover()

        # Execute (with mock LM to avoid real calls in tests)
        mock_prediction = MagicMock()
        mock_prediction.improved_prompt = (
            "**[ROLE]** Test role\n**[DIRECTIVE]** Test directive"
        )
        mock_prediction.role = "Test role"
        mock_prediction.directive = "Test directive"
        mock_prediction.framework = "chain-of-thought"
        mock_prediction.guardrails = "Guardrail 1\nGuardrail 2"

        with patch.object(improver.improver, "forward", return_value=mock_prediction):
            result = improver(original_idea="Test idea", context="Test context")

        # Assert
        assert result.improved_prompt is not None
        assert len(result.improved_prompt) > 0
        assert result.role == "Test role"
        assert result.directive == "Test directive"

    def test_prompt_improver_output_format(self):
        """GREEN: Output should contain all required sections."""

        # Setup mock LM with required attributes
        mock_lm = MagicMock(spec=dspy.LM)
        mock_lm.kwargs = {"temperature": 0.0, "max_tokens": 1000}
        dspy.settings.configure(lm=mock_lm)

        # Setup improver
        improver = PromptImprover()

        mock_prediction = MagicMock()
        mock_prediction.improved_prompt = """**[ROLE & PERSONA]** Test role
**[CORE DIRECTIVE]** Test directive
**[EXECUTION FRAMEWORK]** Test framework
**[CONSTRAINTS & GUARDRAILS]** Test guardrails"""
        mock_prediction.role = "Test role"
        mock_prediction.directive = "Test directive"
        mock_prediction.framework = "chain-of-thought"
        mock_prediction.guardrails = "Guardrail 1\nGuardrail 2"

        with patch.object(improver.improver, "forward", return_value=mock_prediction):
            result = improver(original_idea="Test idea", context="Test context")

        # Assert
        assert "ROLE" in result.improved_prompt.upper()
        assert "DIRECTIVE" in result.improved_prompt.upper()
        assert "FRAMEWORK" in result.improved_prompt.upper()
        assert "GUARDRAILS" in result.improved_prompt.upper()

    def test_compile_prompt_improver(self):
        """GREEN: Should compile with BootstrapFewShot."""
        # Setup
        from eval.src.dspy_prompt_improver import PromptImprover

        improver = PromptImprover()
        trainset = load_prompt_improvement_examples()

        # Execute
        # TODO: Mock the optimization process

        # Assert
        # TODO: Verify compiled module loads successfully


# Integration test
class TestPromptImproverIntegration:
    """Integration tests for PromptImprover."""

    @pytest.mark.integration
    def test_end_to_end_improvement(self):
        """GREEN: Full flow from idea to improved prompt."""
        # TODO: Test with real DSPy LM (Ollama)
        pass
