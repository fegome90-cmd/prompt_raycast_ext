"""
DSPy Prompt Improver Evaluation Scripts.
"""

from eval.src.dspy_prompt_improver import PromptImprover, PromptImproverZeroShot
from eval.src.dspy_prompt_optimizer import (
    compile_prompt_improver,
    prompt_improver_metric,
)
from eval.src.prompt_improvement_dataset import load_prompt_improvement_examples

__all__ = [
    "PromptImprover",
    "PromptImproverZeroShot",
    "compile_prompt_improver",
    "prompt_improver_metric",
    "load_prompt_improvement_examples",
]

# Few-shot module is imported lazily in API to avoid long compilation times
