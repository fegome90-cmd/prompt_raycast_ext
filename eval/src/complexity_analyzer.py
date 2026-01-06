# eval/src/complexity_analyzer.py
from enum import Enum


class ComplexityLevel(Enum):
    """Complexity levels for prompt classification."""
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"
