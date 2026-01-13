"""
Prompt Improver Optimizer

Following HemDov pattern from dspy_optimizer.py
"""

import logging
import dspy
from dspy.teleprompt import BootstrapFewShot
from eval.src.dspy_prompt_improver import PromptImprover
from eval.src.prompt_improvement_dataset import load_prompt_improvement_examples

logger = logging.getLogger(__name__)


def prompt_improver_metric(example, prediction, trace=None) -> float:
    """
    Metric to evaluate prompt improvement quality.

    Following HemDov's executor_production_metric pattern.
    """
    # 1. Must have all required components
    if not prediction.improved_prompt:
        return 0.0

    # 2. Must include role
    if not prediction.role or len(prediction.role) < 20:
        return 0.3

    # 3. Must include directive
    if not prediction.directive or len(prediction.directive) < 30:
        return 0.3

    # 4. Must include framework
    valid_frameworks = [
        "chain-of-thought",
        "tree-of-thoughts",
        "decomposition",
        "role-playing",
    ]
    if not prediction.framework or prediction.framework.lower() not in valid_frameworks:
        return 0.3

    # 5. Must include guardrails
    if not prediction.guardrails or len(prediction.guardrails) < 2:
        return 0.5

    # 6. Check for structured format
    required_sections = ["ROLE", "DIRECTIVE", "FRAMEWORK", "GUARDRAILS"]
    has_sections = sum(
        1
        for section in required_sections
        if section in prediction.improved_prompt.upper()
    )

    if has_sections < 3:
        return 0.7

    # Perfect
    return 1.0


def compile_prompt_improver(
    baseline: PromptImprover,
    max_bootstrapped_demos: int = 5,
    max_labeled_demos: int = 3,
) -> PromptImprover:
    """
    Compile PromptImprover using BootstrapFewShot optimization.

    This is the key step that makes DSPy powerful - it learns from examples.

    Args:
        baseline: Unoptimized PromptImprover module
        max_bootstrapped_demos: Maximum few-shot examples to generate
        max_labeled_demos: Maximum labeled examples to use

    Returns:
        Compiled (optimized) PromptImprover module
    """
    # Load training data
    trainset = load_prompt_improvement_examples()

    # Create optimizer
    optimizer = BootstrapFewShot(
        metric=prompt_improver_metric,
        max_bootstrapped_demos=max_bootstrapped_demos,
        max_labeled_demos=min(max_labeled_demos, len(trainset)),
    )

    # Compile (this may take a few minutes)
    logger = logging.getLogger(__name__)
    logger.info("Compiling PromptImprover with BootstrapFewShot...")
    compiled = optimizer.compile(baseline, trainset=trainset)
    logger.info("Compilation complete!")

    return compiled
