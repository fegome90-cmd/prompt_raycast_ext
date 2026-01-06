"""
Prompt Improver DSPy Module

Based on HemDov DSPy module patterns (BaselineExecutor, MultiStepExecutor).
"""

import dspy
from hemdov.domain.dspy_modules.prompt_improver import PromptImproverSignature


class PromptImprover(dspy.Module):
    """
    DSPy Module for improving user ideas into high-quality prompts.

    Uses Chain of Thought to reason through the improvement process step by step.
    """

    def __init__(self, *, pass_back_context: list[str] | None = None):
        super().__init__()
        # Use ChainOfThought for better reasoning quality
        self.improver = dspy.ChainOfThought(PromptImproverSignature)
        self.pass_back_context = pass_back_context or []

    def forward(self, original_idea: str, context: str = "") -> dspy.Prediction:
        """
        Improve a raw idea into a structured SOTA prompt.

        Args:
            original_idea: User's raw idea or objective
            context: Additional context (optional)

        Returns:
            dspy.Prediction with improved_prompt, role, directive, framework, guardrails, reasoning
        """
        return self.improver(original_idea=original_idea, context=context)


# Alternative: Zero-shot version (faster)
class PromptImproverZeroShot(dspy.Module):
    """
    Zero-shot version of PromptImprover (faster, lower quality).
    """

    def __init__(self):
        super().__init__()
        self.improver = dspy.Predict(PromptImproverSignature)

    def forward(self, original_idea: str, context: str = "") -> dspy.Prediction:
        return self.improver(original_idea=original_idea, context=context)
