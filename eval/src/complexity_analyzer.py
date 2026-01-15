# eval/src/complexity_analyzer.py
# DEPRECATED: This module has moved to hemdov/domain/services/complexity_analyzer.py
# This file is kept for backward compatibility but should not be used in new code.
# Please import from: from hemdov.domain.services import ComplexityAnalyzer, ComplexityLevel
import re
from enum import Enum


class ComplexityLevel(Enum):
    """Complexity levels for prompt classification."""
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"


class ComplexityAnalyzer:
    """
    Analyzes prompt complexity using multi-dimensional scoring.

    DEPRECATED: This class has moved to hemdov.domain.services.complexity_analyzer.
    Import from there instead.
    """

    # Thresholds for length-based classification
    SIMPLE_MAX_LENGTH = 50
    MODERATE_MAX_LENGTH = 150
    AUTO_COMPLEX_LENGTH = 300

    # Score thresholds for classification
    SCORE_THRESHOLD_SIMPLE = 0.25
    SCORE_THRESHOLD_MODERATE = 0.6

    # Technical terms that indicate complexity (multilingual: Spanish/English)
    TECHNICAL_TERMS = [
        "framework", "arquitectura", "patrón", "diseño",
        "metrics", "metrica", "evaluación", "calidad", "optimización",
        "sistema", "componente", "integración", "pipeline", "api",
        "repositorio", "adaptador", "dominio", "infraestructura"
    ]

    def analyze(self, original_idea: str, context: str) -> ComplexityLevel:
        """
        Analyze input complexity across multiple dimensions.

        Args:
            original_idea: User's original prompt idea
            context: Additional context (optional)

        Returns:
            ComplexityLevel: SIMPLE, MODERATE, or COMPLEX

        Raises:
            ValueError: If inputs are None
            TypeError: If inputs are not strings
        """
        # Input validation
        if original_idea is None or context is None:
            raise ValueError("original_idea and context must be non-None strings")
        if not isinstance(original_idea, str) or not isinstance(context, str):
            raise TypeError("original_idea and context must be strings")

        total_length = len(original_idea) + len(context)
        combined_text = (original_idea + " " + context).lower()

        # 1. Length analysis (categorical: 0.0/0.5/1.0, weighted at 40%)
        if total_length <= self.SIMPLE_MAX_LENGTH:
            length_score = 0.0
        elif total_length <= self.MODERATE_MAX_LENGTH:
            length_score = 0.5
        else:
            length_score = 1.0

        # 2. Technical term detection (0-1 terms=0.0, 2+ terms=1.0, weighted at 30%)
        # Uses word boundary matching to avoid substring false positives
        word_pattern = r'\b(' + '|'.join(re.escape(term) for term in self.TECHNICAL_TERMS) + r')\b'
        technical_count = len(re.findall(word_pattern, combined_text))
        technical_score = min(technical_count * 0.5, 1.0)

        # 3. Structure analysis (0.1 per punctuation mark, max 1.0, weighted at 20%)
        sentence_count = combined_text.count('.') + combined_text.count(',') + combined_text.count(';')
        structure_score = min(sentence_count * 0.1, 1.0)

        # 4. Context provided (binary scoring: 1.0 or 0.0, weighted at 10%)
        context_score = 1.0 if context and context.strip() else 0.0

        # Combine weighted scores
        total_score = (
            length_score * 0.4 +
            technical_score * 0.3 +
            structure_score * 0.2 +
            context_score * 0.1
        )

        # Map to complexity levels
        # Very long inputs automatically COMPLEX
        if total_length > self.AUTO_COMPLEX_LENGTH:
            return ComplexityLevel.COMPLEX
        elif total_score < self.SCORE_THRESHOLD_SIMPLE:
            return ComplexityLevel.SIMPLE
        elif total_score < self.SCORE_THRESHOLD_MODERATE:
            return ComplexityLevel.MODERATE
        else:
            return ComplexityLevel.COMPLEX
