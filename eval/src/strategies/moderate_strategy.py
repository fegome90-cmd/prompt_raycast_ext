# eval/src/strategies/moderate_strategy.py
import logging
import dspy
from hemdov.domain.dspy_modules.prompt_improver import PromptImproverSignature
from .base import PromptImproverStrategy

logger = logging.getLogger(__name__)


class ModerateStrategy(PromptImproverStrategy):
    """Balanced strategy for moderate inputs with ChainOfThought."""

    def __init__(self, max_length: int = 2000):
        """
        Initialize moderate strategy.

        Args:
            max_length: Maximum output length in characters
        """
        self.improver = dspy.ChainOfThought(PromptImproverSignature)
        self._max_length = max_length

    def improve(self, original_idea: str, context: str) -> dspy.Prediction:
        """
        Generate balanced prompt improvement with reasoning.

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
            logger.error(f"DSPy ChainOfThought error in ModerateStrategy: {e}")
            raise RuntimeError(f"DSPy PromptImprover failed: {e}") from e

        # Validate Prediction structure
        self._validate_prediction(result)

        # Truncate if exceeds max length
        if len(result.improved_prompt) > self._max_length:
            result.improved_prompt = self._truncate_at_sentence(
                result.improved_prompt,
                self._max_length,
                add_suffix=False
            )

        return result

    @property
    def name(self) -> str:
        return "moderate"
