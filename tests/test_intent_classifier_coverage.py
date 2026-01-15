"""
Coverage tests for IntentClassifier.

This file provides comprehensive coverage tests that complement
the edge case tests in test_intent_classifier_edge_cases.py.

Tests cover:
- All intent types classification (comprehensive)
- Context-driven classification scenarios
- Intent mapping accuracy
"""

import pytest
from hemdov.domain.dto.nlac_models import NLaCRequest, IntentType, NLaCInputs
from hemdov.domain.services.intent_classifier import IntentClassifier


class TestIntentClassifierCoverage:
    """Comprehensive coverage tests for IntentClassifier."""

    @pytest.fixture
    def classifier(self):
        """Create classifier instance."""
        return IntentClassifier()

    # ========================================================================
    # COMPREHENSIVE ALL INTENTS CLASSIFICATION
    # ========================================================================

    def test_classify_all_intents(self, classifier):
        """
        Test that ALL intent types are correctly classified.

        This comprehensive test ensures:
        - GENERATE intent (default)
        - DEBUG intent (with error keywords)
        - REFACTOR intent (with optimization verbs)
        - EXPLAIN intent (with explain keywords)

        Each scenario tests the classification end-to-end.
        """
        # GENERATE intent - default (Scenario I: Lazy Prompting)
        generate_request = NLaCRequest(
            idea="Create a hello world function",
            context="In Python please",
            mode="nlac"
        )
        assert classifier.classify(generate_request) == classifier.INTENT_GENERATE

        # DEBUG intent - runtime error (Scenario II: Runtime Errors)
        debug_request = NLaCRequest(
            idea="Fix this bug",
            context="Getting an error",
            inputs=NLaCInputs(
                code_snippet="def foo():\n    return 1/0",
                error_log="ZeroDivisionError: division by zero"
            )
        )
        assert classifier.classify(debug_request) == classifier.INTENT_DEBUG

        # REFACTOR intent - incorrect output (Scenario III: Logic Errors)
        refactor_request = NLaCRequest(
            idea="Optimize this function",
            context="It's too slow",
            mode="nlac"
        )
        assert classifier.classify(refactor_request) == classifier.INTENT_REFACTOR

        # EXPLAIN intent - understanding request
        explain_request = NLaCRequest(
            idea="Explain how recursion works",
            context="Need to understand the concept",
            mode="nlac"
        )
        assert classifier.classify(explain_request) == classifier.INTENT_EXPLAIN

    # ========================================================================
    # CONTEXT-DRIVEN CLASSIFICATION
    # ========================================================================

    def test_classify_with_context(self, classifier):
        """
        Test classification with various context scenarios.

        Context should influence classification when:
        1. Context contains "expected" behavior keywords → REFACTOR
        2. Context contains explain keywords → EXPLAIN
        3. Context influences default classification
        """
        # Context with expected behavior mismatch → REFACTOR
        request_refactor = NLaCRequest(
            idea="Make this work",
            context="The expected output is 42 but it returns 0",
            mode="nlac"
        )
        intent = classifier.classify(request_refactor)
        assert intent == classifier.INTENT_REFACTOR, \
            f"Expected REFACTOR for context with 'expected', got {intent}"

        # Context with explain keywords → EXPLAIN
        request_explain = NLaCRequest(
            idea="Help me understand",
            context="I need to review this code for analysis",
            mode="nlac"
        )
        intent = classifier.classify(request_explain)
        assert intent == classifier.INTENT_EXPLAIN, \
            f"Expected EXPLAIN for context with review/analysis, got {intent}"

        # Note: Semantic debug check only looks at idea, not context
        # Debug in context only triggers if frustration pattern is present
        request_debug_context_only = NLaCRequest(
            idea="Something is broken",  # "broken" is in debug_keywords
            context="This code doesn't work",
            mode="nlac"
        )
        intent = classifier.classify(request_debug_context_only)
        assert intent == classifier.INTENT_DEBUG, \
            f"Expected DEBUG for idea with debug keyword, got {intent}"

        # Empty context → default classification based on idea
        request_default = NLaCRequest(
            idea="Create a function",
            context="",
            mode="nlac"
        )
        intent = classifier.classify(request_default)
        assert intent == classifier.INTENT_GENERATE, \
            f"Expected GENERATE for simple request with empty context, got {intent}"

    # ========================================================================
    # INTENT MAPPING ACCURACY
    # ========================================================================

    def test_intent_mapping_accuracy(self, classifier):
        """
        Test that get_intent_type accurately maps intent strings to IntentType enum.

        This ensures the mapping function handles:
        - Main intent types (generate, debug, refactor, explain)
        - Debug subtypes (debug_runtime, debug_vague)
        - Refactor subtypes (refactor_logic, refactor_performance)
        - Unknown/empty strings (default to GENERATE)
        """
        # Main intent types map correctly
        assert classifier.get_intent_type("generate") == IntentType.GENERATE
        assert classifier.get_intent_type("debug") == IntentType.DEBUG
        assert classifier.get_intent_type("refactor") == IntentType.REFACTOR
        assert classifier.get_intent_type("explain") == IntentType.EXPLAIN

        # Debug subtypes all map to DEBUG
        debug_subtypes = ["debug_runtime", "debug_vague", "debug_anything"]
        for subtype in debug_subtypes:
            assert classifier.get_intent_type(subtype) == IntentType.DEBUG, \
                f"Debug subtype '{subtype}' should map to DEBUG"

        # Refactor subtypes all map to REFACTOR
        refactor_subtypes = ["refactor_logic", "refactor_performance", "refactor_custom"]
        for subtype in refactor_subtypes:
            assert classifier.get_intent_type(subtype) == IntentType.REFACTOR, \
                f"Refactor subtype '{subtype}' should map to REFACTOR"

        # Unknown strings default to GENERATE
        assert classifier.get_intent_type("unknown") == IntentType.GENERATE
        assert classifier.get_intent_type("") == IntentType.GENERATE
        assert classifier.get_intent_type("random_text") == IntentType.GENERATE

    # ========================================================================
    # PHASE 1 STRUCTURAL RULES PRIORITY
    # ========================================================================

    def test_structural_rules_override_semantic_classification(self, classifier):
        """
        Test that Phase 1 structural rules take priority over Phase 2 semantic analysis.

        Structural rules:
        1. code_snippet + error_log → DEBUG_RUNTIME
        2. "expected"/"debería" in context → REFACTOR_LOGIC
        """
        # Structural rule (Scenario II) overrides semantic "generate" keywords
        request_scenario2 = NLaCRequest(
            idea="Create new code",  # Semantically: GENERATE
            inputs=NLaCInputs(      # Structurally: DEBUG_RUNTIME
                code_snippet="def foo(): pass",
                error_log="TypeError"
            )
        )
        intent = classifier.classify(request_scenario2)
        assert intent == classifier.INTENT_DEBUG, \
            "Structural rule (code + error) should override semantic 'create'"

        # Structural rule (Scenario III) overrides semantic classification
        request_scenario3 = NLaCRequest(
            idea="Generate a function",  # Semantically: GENERATE
            context="It should output X but outputs Y"  # Structurally: REFACTOR
        )
        intent = classifier.classify(request_scenario3)
        assert intent == classifier.INTENT_REFACTOR, \
            "Structural rule (expected behavior) should override semantic 'generate'"

    # ========================================================================
    # SEMANTIC PHASE PRIORITY ORDER
    # ========================================================================

    def test_semantic_phase_priority_order(self, classifier):
        """
        Test that semantic phase follows the correct priority order:
        1. EXPLAIN (checked first)
        2. REFACTOR (checked second)
        3. DEBUG with frustration (checked third)
        4. DEBUG without frustration (checked fourth)
        5. GENERATE (default)
        """
        # Explain takes priority over debug
        request_explain_over_debug = NLaCRequest(
            idea="Explain the error in my code",  # Has explain + debug keywords
            context="",
            mode="nlac"
        )
        intent = classifier.classify(request_explain_over_debug)
        assert intent == classifier.INTENT_EXPLAIN, \
            "EXPLAIN should take priority over DEBUG"

        # Refactor takes priority over debug
        request_refactor_over_debug = NLaCRequest(
            idea="Optimize and fix the broken code",  # Has refactor + debug
            context="",
            mode="nlac"
        )
        intent = classifier.classify(request_refactor_over_debug)
        assert intent == classifier.INTENT_REFACTOR, \
            "REFACTOR should take priority over DEBUG"

        # Debug with frustration takes priority over simple debug
        request_frustration_priority = NLaCRequest(
            idea="This is always broken and doesn't work",
            context="",
            mode="nlac"
        )
        intent = classifier.classify(request_frustration_priority)
        assert intent == classifier.INTENT_DEBUG, \
            "DEBUG with frustration should be detected"
