# eval/src/strategies/base.py
from abc import ABC, abstractmethod
import dspy


class PromptImproverStrategy(ABC):
    """Base strategy for prompt improvement."""

    @abstractmethod
    def improve(self, original_idea: str, context: str) -> dspy.Prediction:
        """
        Improve prompt according to strategy.

        Args:
            original_idea: User's original prompt idea
            context: Additional context (optional)

        Returns:
            dspy.Prediction with improved_prompt, role, directive, framework, guardrails
        """
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Strategy name for logging."""
        pass
