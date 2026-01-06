# eval/src/strategies/__init__.py
"""
Strategy Pattern implementation for prompt improvement.

Exports three strategies based on input complexity:
- SimpleStrategy: Zero-shot with dspy.Predict (800 char max)
- ModerateStrategy: ChainOfThought with dspy.ChainOfThought (2000 char max)
- ComplexStrategy: Few-shot with KNNFewShot (5000 char max)
"""

from .base import PromptImproverStrategy
from .simple_strategy import SimpleStrategy
from .moderate_strategy import ModerateStrategy
from .complex_strategy import ComplexStrategy

__all__ = [
    "PromptImproverStrategy",
    "SimpleStrategy",
    "ModerateStrategy",
    "ComplexStrategy",
]
