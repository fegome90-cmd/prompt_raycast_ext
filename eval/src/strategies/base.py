# eval/src/strategies/base.py
from abc import ABC, abstractmethod
import dspy
import logging

logger = logging.getLogger(__name__)


class PromptImproverStrategy(ABC):
    """Base strategy for prompt improvement."""

    # Truncation threshold ratio (70% of max_length)
    TRUNCATION_THRESHOLD_RATIO = 0.7

    @abstractmethod
    def improve(self, original_idea: str, context: str) -> dspy.Prediction:
        """
        Improve prompt according to strategy.

        Args:
            original_idea: User's original prompt idea
            context: Additional context (optional)

        Returns:
            dspy.Prediction with improved_prompt, role, directive, framework, guardrails

        Raises:
            ValueError: If inputs are None
            TypeError: If inputs are not strings
        """
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Strategy name for logging."""
        pass

    def _validate_inputs(self, original_idea: str, context: str) -> None:
        """
        Validate input parameters.

        Args:
            original_idea: User's original prompt idea
            context: Additional context (optional)

        Raises:
            ValueError: If inputs are None
            TypeError: If inputs are not strings
        """
        if original_idea is None or context is None:
            raise ValueError("original_idea and context must be non-None strings")
        if not isinstance(original_idea, str) or not isinstance(context, str):
            raise TypeError("original_idea and context must be strings")

    def _validate_prediction(self, result: dspy.Prediction) -> None:
        """
        Validate DSPy Prediction structure.

        Args:
            result: DSPy Prediction object

        Raises:
            ValueError: If required fields are missing
            AttributeError: If result is not a valid Prediction
        """
        if not hasattr(result, 'improved_prompt'):
            raise ValueError("DSPy Prediction missing required 'improved_prompt' field")

        if not result.improved_prompt or not isinstance(result.improved_prompt, str):
            raise ValueError("DSPy Prediction 'improved_prompt' must be a non-empty string")

    def _truncate_at_sentence(self, text: str, max_length: int, add_suffix: bool = True) -> str:
        """
        Truncate at last complete sentence within limit.

        Priority: period > newline > hard truncate
        Only adds boundary markers if they appear after 70% threshold.

        Args:
            text: Text to truncate
            max_length: Maximum length in characters
            add_suffix: Whether to add "..." suffix when hard truncating

        Returns:
            Truncated text
        """
        if not isinstance(text, str):
            raise TypeError(f"text must be string, got {type(text)}")

        truncated = text[:max_length]
        last_period = truncated.rfind('.')
        last_newline = truncated.rfind('\n')

        if last_period > max_length * self.TRUNCATION_THRESHOLD_RATIO:
            return truncated[:last_period + 1]
        elif last_newline > max_length * self.TRUNCATION_THRESHOLD_RATIO:
            return truncated[:last_newline]
        else:
            return truncated + ("..." if add_suffix else "")
