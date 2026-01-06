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
        combined_text = (original_idea + " " + context).lower()

        # 1. Length analysis (40% weight)
        if total_length <= self.SIMPLE_MAX_LENGTH:
            length_score = 0.0
        elif total_length <= self.MODERATE_MAX_LENGTH:
            length_score = 0.5
        else:
            length_score = 1.0

        # 2. Technical term detection (30% weight)
        # Each technical term contributes 0.5, maxing at 1.0
        technical_count = sum(1 for term in self.TECHNICAL_TERMS if term.lower() in combined_text)
        technical_score = min(technical_count * 0.5, 1.0)

        # 3. Structure analysis (20% weight) - multiple sentences/commas
        sentence_count = combined_text.count('.') + combined_text.count(',') + combined_text.count(';')
        structure_score = min(sentence_count * 0.1, 1.0)

        # 4. Context provided (10% weight)
        context_score = 1.0 if context.strip() else 0.0

        # Combine scores
        total_score = (
            length_score * 0.4 +
            technical_score * 0.3 +
            structure_score * 0.2 +
            context_score * 0.1
        )

        # Map to complexity levels with adjusted thresholds
        # Very long inputs (>300 chars) automatically COMPLEX
        if total_length > 300:
            return ComplexityLevel.COMPLEX
        elif total_score < 0.25:
            return ComplexityLevel.SIMPLE
        elif total_score < 0.6:
            return ComplexityLevel.MODERATE
        else:
            return ComplexityLevel.COMPLEX
