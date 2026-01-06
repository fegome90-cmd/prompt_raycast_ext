# eval/src/complexity_analyzer.py
from enum import Enum


class ComplexityLevel(Enum):
    """Complexity levels for prompt classification."""
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"


class ComplexityAnalyzer:
    """Analyzes prompt complexity using multi-dimensional scoring."""

    # Thresholds for length-based classification
    SIMPLE_MAX_LENGTH = 50
    MODERATE_MAX_LENGTH = 150

    # Technical terms that indicate complexity
    TECHNICAL_TERMS = [
        "framework", "arquitectura", "arquitectura", "patrón", "diseño",
        "metrics", "metrica", "evaluación", "calidad", "optimización",
        "sistema", "componente", "integración", "pipeline", "api",
        "repositorio", "adaptador", "dominio", "infraestructura"
    ]

    def analyze(self, original_idea: str, context: str) -> ComplexityLevel:
        """
        Analyze input complexity across multiple dimensions.

        Returns:
            ComplexityLevel: SIMPLE, MODERATE, or COMPLEX
        """
        total_length = len(original_idea) + len(context)

        # 1. Length analysis (primary signal)
        if total_length <= self.SIMPLE_MAX_LENGTH:
            return ComplexityLevel.SIMPLE
        elif total_length <= self.MODERATE_MAX_LENGTH:
            return ComplexityLevel.MODERATE
        else:
            return ComplexityLevel.COMPLEX
