"""
Prompt Improver DSPy Signature

Based on HemDov DSPy patterns for prompt optimization.
"""

import dspy


class PromptImproverSignature(dspy.Signature):
    """
    Improve a user's raw idea into a high-quality, structured prompt.

    This signature transforms vague or incomplete ideas into State-of-the-Art (SOTA)
    prompts following the Architect pattern: Role + Directive + Framework + Guardrails.
    """

    # Input fields
    original_idea = dspy.InputField(
        desc="User's raw idea or objective that needs improvement"
    )

    context = dspy.InputField(
        desc="Additional context about the use case, audience, or constraints (optional)",
        default="",
    )

    # Optional: Few-shot examples for better quality (commented for MVP)
    # )

    # Output fields
    improved_prompt = dspy.OutputField(
        desc="Complete, structured SOTA prompt with role, directive, framework, and guardrails"
    )

    role = dspy.OutputField(
        desc="AI role description extracted from the improved prompt"
    )

    directive = dspy.OutputField(
        desc="Core directive/mission extracted from the improved prompt"
    )

    framework = dspy.OutputField(
        desc="Recommended reasoning framework (chain-of-thought, tree-of-thoughts, decomposition, role-playing)"
    )

    guardrails = dspy.OutputField(desc="List of 3-5 key constraints or guardrails")

    reasoning = dspy.OutputField(
        desc="Explanation of why these improvements were made", default=None
    )

    confidence = dspy.OutputField(
        desc="Confidence score (0-1) in the quality of the improved prompt",
        default=None,
    )
