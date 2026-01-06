"""
Intent Classifier - Hybrid Router for NLaC API.

Routes requests to appropriate intent based on:
1. Structural rules (fast path)
2. Semantic analysis (slow path, LLM-assisted)

Based on MultiAIGCD scenarios:
- Scenario I: Lazy Prompting → GENERATE
- Scenario II: Runtime Errors → DEBUG_RUNTIME
- Scenario III: Incorrect Outputs → REFACTOR_LOGIC
"""

import logging
import re
from typing import Optional

from hemdov.domain.dto.nlac_models import NLaCRequest, IntentType

logger = logging.getLogger(__name__)


class IntentClassifier:
    """
    Router híbrido: Reglas estructurales → LLM si duda.

    Two-phase classification:
    1. **Fast Path**: Structural rules (instant, no LLM call)
    2. **Slow Path**: Semantic analysis (sentiment, verb detection, keywords)
    """

    # Intent constants (matching IntentType enum values)
    INTENT_GENERATE = "generate"
    INTENT_DEBUG = "debug"
    INTENT_REFACTOR = "refactor"
    INTENT_EXPLAIN = "explain"

    # Debug sub-types (for routing to different strategies)
    DEBUG_RUNTIME = "debug_runtime"      # Scenario II: code + error_log
    DEBUG_VAGUE = "debug_vague"          # Vague error description

    # Refactor sub-types
    REFACTOR_LOGIC = "refactor_logic"    # Scenario III: incorrect outputs
    REFACTOR_PERFORMANCE = "refactor_performance"

    def __init__(self):
        """Initialize classifier with keyword patterns."""
        # Debug keywords (negative sentiment + error indicators)
        self._debug_keywords = {
            "error", "bug", "fix", "broken", "crash", "fail",
            "incorrecto", "error", "fallo", "rompe", "no funciona"
        }

        # Refactor/Optimization verbs
        self._refactor_verbs = {
            "optimizar", "mejorar", "refactorizar", "optimise",
            "improve", "refactor", "optimize", "clean up"
        }

        # Explain keywords
        self._explain_keywords = {
            "explain", "how does", "why", "qué es", "cómo funciona",
            "explicar", "entender", "understand"
        }

        # Frustration indicators (negative sentiment)
        self._frustration_patterns = [
            r"\bno funciona\b",
            r"\bdoesn't work\b",
            r"\bnot working\b",
            r"\bsiempre falla\b",
            r"\balways fails\b",
        ]

    def classify(self, request: NLaCRequest) -> str:
        """
        Classify request intent using hybrid routing.

        Phase 1: Structural rules (MultiAIGCD scenarios)
        Phase 2: Semantic analysis (keyword + sentiment detection)

        Args:
            request: NLaCRequest with idea, context, and optional structured inputs

        Returns:
            Intent type string matching IntentType enum
        """
        # =====================================================================
        # PHASE 1: STRUCTURAL RULES (Fast Path - No LLM)
        # =====================================================================

        # Scenario II: Fixing Runtime Errors
        # Structured signal: code_snippet + error_log present
        if request.inputs and request.inputs.code_snippet and request.inputs.error_log:
            logger.debug(
                f"Intent: DEBUG_RUNTIME (code_snippet + error_log) | "
                f"error_log preview: {request.inputs.error_log[:50]}..."
            )
            return self.INTENT_DEBUG

        # Scenario III: Incorrect Outputs (Logic Errors)
        # Context mentions expected behavior
        if request.context and any(
            keyword in request.context.lower()
            for keyword in ["expected", "debería", "should output", "but it"]
        ):
            logger.debug("Intent: REFACTOR_LOGIC (expected behavior mismatch)")
            return self.INTENT_REFACTOR

        # =====================================================================
        # PHASE 2: SEMANTIC CLASSIFICATION (Keyword + Sentiment)
        # =====================================================================

        idea_lower = request.idea.lower()
        context_lower = request.context.lower() if request.context else ""

        # Check for explicit explain keywords
        if self._has_explain_intent(idea_lower, context_lower):
            logger.debug("Intent: EXPLAIN (explicit explain keywords)")
            return self.INTENT_EXPLAIN

        # Check for refactor/optimize verbs
        if self._has_refactor_intent(idea_lower):
            logger.debug("Intent: REFACTOR (optimization verbs detected)")
            return self.INTENT_REFACTOR

        # Check for debug intent with frustration → prioritize debug
        if self._has_debug_intent_with_frustration(request.idea, idea_lower):
            logger.debug("Intent: DEBUG (frustration + error keywords)")
            return self.INTENT_DEBUG

        # Check for debug intent without explicit error
        if self._has_debug_intent(idea_lower):
            logger.debug("Intent: DEBUG (error keywords)")
            return self.INTENT_DEBUG

        # Default: Text-to-Code Generation (Scenario I: Lazy Prompting)
        logger.debug("Intent: GENERATE (default)")
        return self.INTENT_GENERATE

    def _has_explain_intent(self, idea_lower: str, context_lower: str) -> bool:
        """Check if user wants explanation."""
        combined = idea_lower + " " + context_lower
        return any(keyword in combined for keyword in self._explain_keywords)

    def _has_refactor_intent(self, idea_lower: str) -> bool:
        """Check if user wants to refactor/optimize."""
        # Check for explicit refactor verbs
        has_verb = any(
            f" {verb} " in f" {idea_lower} "  # Word boundary check
            for verb in self._refactor_verbs
        )

        # Check for performance keywords
        performance_keywords = ["slow", "lento", "inefficient", "ineficiente"]
        has_performance = any(keyword in idea_lower for keyword in performance_keywords)

        return has_verb or has_performance

    def _has_debug_intent(self, text_lower: str) -> bool:
        """Check for debug/intent keywords."""
        return any(keyword in text_lower for keyword in self._debug_keywords)

    def _has_debug_intent_with_frustration(self, idea: str, idea_lower: str) -> bool:
        """
        Check for debug intent with negative sentiment.

        Frustration patterns indicate higher priority for debug.
        """
        # Check for frustration patterns
        has_frustration = any(
            re.search(pattern, idea_lower, re.IGNORECASE)
            for pattern in self._frustration_patterns
        )

        # Check for negative emotion + error keywords
        negative_emotions = ["frustrated", "annoying", "stuck", "atascado", "frustrado"]
        has_negative = any(emotion in idea_lower for emotion in negative_emotions)

        has_error = self._has_debug_intent(idea_lower)

        return (has_frustration or has_negative) and has_error

    def _analyze_sentiment(self, text: str) -> str:
        """
        Analyze sentiment of user input.

        Simple rule-based sentiment analysis.
        In production, this could use an LLM or sentiment model.

        Returns:
            "positive", "neutral", or "negative"
        """
        negative_words = {
            "error", "fail", "broken", "wrong", "bad", "frustrating",
            "error", "fallo", "roto", "mal", "frustrante"
        }

        positive_words = {
            "good", "great", "perfect", "excellent", "thanks",
            "bien", "genial", "perfecto", "excelente", "gracias"
        }

        text_lower = text.lower()

        negative_count = sum(1 for word in negative_words if word in text_lower)
        positive_count = sum(1 for word in positive_words if word in text_lower)

        if negative_count > positive_count:
            return "negative"
        elif positive_count > negative_count:
            return "positive"
        else:
            return "neutral"

    def get_intent_type(self, intent_string: str) -> IntentType:
        """
        Convert intent string to IntentType enum.

        Maps sub-types (debug_runtime, debug_vague, etc.) to main IntentType values.
        """
        if intent_string.startswith("debug"):
            return IntentType.DEBUG
        elif intent_string.startswith("refactor"):
            return IntentType.REFACTOR
        elif intent_string == "explain":
            return IntentType.EXPLAIN
        else:
            return IntentType.GENERATE
