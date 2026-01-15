"""
Prompt Improver DSPy Module

Based on HemDov DSPy module patterns (BaselineExecutor, MultiStepExecutor).
"""

import dspy

from hemdov.domain.dspy_modules.augmenter_sig import PromptAugmenterSignature
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


class ContextAwarePromptImprover(dspy.Module):
    """
    Advanced DSPy module that integrates general context rules.
    Used for Gemini 3.0 Flash optimized context injection.
    """

    def __init__(self):
        super().__init__()
        # Step 1: Improve the prompt using standard signature
        self.improver = dspy.ChainOfThought(PromptImproverSignature)
        # Step 2: Augment with general context rules
        self.augmenter = dspy.ChainOfThought(PromptAugmenterSignature)

    def forward(
        self, original_idea: str, context: str = "", general_context: str = ""
    ) -> dspy.Prediction:
        """
        Two-step improvement process:
        1. Standard optimization.
        2. Context/Rule alignment.
        """
        # First step: Basic improvement
        basic_improvement = self.improver(original_idea=original_idea, context=context)

        # Second step: Rule alignment
        if not general_context:
            return basic_improvement

        final_improvement = self.augmenter(
            original_idea=basic_improvement.improved_prompt,
            general_context=general_context,
        )

        # Merge results: Keep structural metadata from first step, but content from second
        return dspy.Prediction(
            improved_prompt=final_improvement.improved_prompt,
            role=basic_improvement.role,
            directive=basic_improvement.directive,
            framework=basic_improvement.framework,
            guardrails=basic_improvement.guardrails,
            reasoning=basic_improvement.reasoning,
            confidence=final_improvement.confidence,
            rule_compliance_report=final_improvement.rule_compliance_report,
        )


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
