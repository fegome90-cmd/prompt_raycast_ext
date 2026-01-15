"""
Prompt Augmenter DSPy Signature.
Specialized for integrating general context rules into the prompt optimization process.
"""

import dspy


class PromptAugmenterSignature(dspy.Signature):
    """
    Integrate general context rules and agent instructions into the prompt.

    Ensures that the final prompt aligns with business logic, guardrails,
    and specific agent personas defined in the context files.
    """

    original_idea = dspy.InputField(desc="User's raw idea or objective")
    general_context = dspy.InputField(
        desc="Aggregated rules and agent instructions from context files"
    )

    improved_prompt = dspy.OutputField(
        desc="Optimized prompt that strictly follows the provided general context rules"
    )

    rule_compliance_report = dspy.OutputField(
        desc="Analysis of how each critical rule from the general context was integrated"
    )

    confidence = dspy.OutputField(
        desc="Confidence score (0-1) regarding rule alignment", default=None
    )
