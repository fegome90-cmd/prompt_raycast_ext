# eval/src/strategies/simple_strategy.py
import logging
import dspy
from hemdov.domain.dspy_modules.prompt_improver import PromptImproverSignature
from .base import PromptImproverStrategy

logger = logging.getLogger(__name__)


class SimpleStrategy(PromptImproverStrategy):
    """Ultra-concise strategy for simple/trivial inputs."""

    def __init__(self, max_length: int = 800):
        """
        Initialize simple strategy.

        Args:
            max_length: Maximum output length in characters
        """
        self.improver = dspy.Predict(PromptImproverSignature)
        self._max_length = max_length

    def improve(self, original_idea: str, context: str) -> dspy.Prediction:
        """
        Generate concise prompt improvement.

        Args:
            original_idea: User's original prompt idea
            context: Additional context (optional)

        Returns:
            dspy.Prediction with improved_prompt, role, directive, framework, guardrails

        Raises:
            ValueError: If DSPy Prediction validation fails
            TypeError: If inputs are not strings
        """
        # Input validation
        self._validate_inputs(original_idea, context)

        try:
            result = self.improver(original_idea=original_idea, context=context)
        except Exception as e:
            logger.error(f"DSPy Predict error in SimpleStrategy: {e}")
            raise RuntimeError(f"DSPy PromptImprover failed: {e}") from e

        # Validate Prediction structure
        self._validate_prediction(result)

        # Truncate if exceeds max length
        if len(result.improved_prompt) > self._max_length:
            result.improved_prompt = self._truncate_at_sentence(
                result.improved_prompt,
                self._max_length,
                add_suffix=True
            )

        return result

    @property
    def name(self) -> str:
        return "simple"
