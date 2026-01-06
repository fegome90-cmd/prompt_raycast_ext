# eval/src/strategies/moderate_strategy.py
import dspy
from hemdov.domain.dspy_modules.prompt_improver import PromptImproverSignature
from .base import PromptImproverStrategy


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
        """Generate balanced prompt improvement with reasoning."""
        result = self.improver(original_idea=original_idea, context=context)

        # Truncate if exceeds max length
        if len(result.improved_prompt) > self._max_length:
            result.improved_prompt = self._truncate_at_sentence(result.improved_prompt)

        return result

    @property
    def name(self) -> str:
        return "moderate"

    def _truncate_at_sentence(self, text: str) -> str:
        """Truncate at last complete sentence within limit."""
        truncated = text[:self._max_length]
        last_period = truncated.rfind('.')
        last_newline = truncated.rfind('\n')

        if last_period > self._max_length * 0.7:
            return truncated[:last_period + 1]
        elif last_newline > self._max_length * 0.7:
            return truncated[:last_newline]
        else:
            return truncated
