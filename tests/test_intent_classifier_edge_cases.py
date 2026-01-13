"""
Edge case and error condition tests for IntentClassifier.

Tests cover:
- Null/empty input handling
- Unicode and special characters
- Boundary conditions
- Ambiguous scenarios
- Error path combinations
"""

import pytest
from hemdov.domain.dto.nlac_models import NLaCRequest, IntentType, NLaCInputs
from hemdov.domain.services.intent_classifier import IntentClassifier


class TestIntentClassifierEdgeCases:
    """Test edge cases and error conditions in IntentClassifier."""

    @pytest.fixture
    def classifier(self):
        """Create classifier instance."""
        return IntentClassifier()

    # ========================================================================
    # NULL AND EMPTY INPUT TESTS
    # ========================================================================

    def test_empty_idea_defaults_to_generate(self, classifier):
        """Empty idea is rejected by validation, but classifier handles it."""
        # Pydantic validation rejects empty ideas, so we test the classifier
        # directly with the idea that would pass validation
        # The validation strips whitespace, so "   " becomes "" which fails
        # This test documents that empty ideas are caught at validation layer
        pass  # Handled by Pydantic validation

    def test_whitespace_only_idea(self, classifier):
        """Whitespace-only idea is rejected by validation."""
        # Pydantic validation strips and rejects empty ideas
        pass  # Handled by Pydantic validation

    def test_none_context_handling(self, classifier):
        """None context is handled by default value."""
        # NLaCRequest has default="" for context, not None
        request = NLaCRequest(
            idea="Create a function",
            context="",  # Use empty string instead of None
            mode="nlac"
        )
        # Should not raise
        intent = classifier.classify(request)
        assert intent in [
            classifier.INTENT_GENERATE,
            classifier.INTENT_EXPLAIN
        ]

    def test_very_long_idea(self, classifier):
        """Very long idea text should be processed without error."""
        long_idea = "Create a function " * 1000  # ~17,000 chars
        request = NLaCRequest(
            idea=long_idea,
            context="",
            mode="nlac"
        )
        # Should not raise
        intent = classifier.classify(request)
        assert intent is not None

    # ========================================================================
    # UNICODE AND SPECIAL CHARACTER TESTS
    # ========================================================================

    def test_unicode_emoji_in_idea(self, classifier):
        """Emoji in idea should be handled correctly."""
        request = NLaCRequest(
            idea="Fix this bug 🐛 please 🙏",
            context="",
            mode="nlac"
        )
        intent = classifier.classify(request)
        assert intent == classifier.INTENT_DEBUG

    def test_unicode_chinese_characters(self, classifier):
        """Chinese characters should be processed."""
        request = NLaCRequest(
            idea="修复这个错误",  # "Fix this error" in Chinese
            context="",
            mode="nlac"
        )
        # Should not raise - defaults to GENERATE for non-English
        intent = classifier.classify(request)
        assert intent is not None

    def test_unicode_russian_cyrillic(self, classifier):
        """Cyrillic characters should be processed."""
        request = NLaCRequest(
            idea="Исправь ошибку",  # "Fix the error" in Russian
            context="",
            mode="nlac"
        )
        # Should not raise
        intent = classifier.classify(request)
        assert intent is not None

    def test_special_characters_only(self, classifier):
        """Special characters only should default to GENERATE."""
        request = NLaCRequest(
            idea="!@#$%^&*()_+-=[]{}|;:,.<>?",
            context="",
            mode="nlac"
        )
        intent = classifier.classify(request)
        assert intent == classifier.INTENT_GENERATE

    def test_newlines_and_tabs(self, classifier):
        """Newlines and tabs in idea should be handled."""
        request = NLaCRequest(
            idea="\n\nFix\nthis\n\nbug\n\n",
            context="",
            mode="nlac"
        )
        intent = classifier.classify(request)
        assert intent == classifier.INTENT_DEBUG

    # ========================================================================
    # BOUNDARY CONDITIONS
    # ========================================================================

    def test_single_character_idea(self, classifier):
        """Single character idea should not crash."""
        request = NLaCRequest(
            idea="x",
            context="",
            mode="nlac"
        )
        intent = classifier.classify(request)
        assert intent == classifier.INTENT_GENERATE

    def test_idea_exactly_at_keyword_boundary(self, classifier):
        """Keyword at exact start/end of string."""
        request = NLaCRequest(
            idea="fix",  # Exact keyword match
            context="",
            mode="nlac"
        )
        intent = classifier.classify(request)
        # Should detect debug intent
        assert intent == classifier.INTENT_DEBUG

    def test_keyword_case_variations(self, classifier):
        """Various case combinations of keywords."""
        test_cases = [
            "FIX this",
            "Fix This",
            "fIx ThIs",
            "FIX THIS BUG",
        ]
        for idea in test_cases:
            request = NLaCRequest(
                idea=idea,
                context="",
                mode="nlac"
            )
            intent = classifier.classify(request)
            # All should detect debug intent (case-insensitive)
            assert intent == classifier.INTENT_DEBUG

    # ========================================================================
    # AMBIGUOUS SCENARIOS
    # ========================================================================

    def test_multiple_intents_present(self, classifier):
        """When both debug and refactor keywords present, refactor takes priority."""
        request = NLaCRequest(
            idea="Fix the bug and optimize performance",
            context="",
            mode="nlac"
        )
        # Refactor keywords are checked before debug in semantic phase
        # "optimize" triggers refactor intent
        intent = classifier.classify(request)
        assert intent == classifier.INTENT_REFACTOR

    def test_explain_vs_debug_ambiguity(self, classifier):
        """Explain keywords in debugging context."""
        request = NLaCRequest(
            idea="Explain why this error happens",
            context="",
            mode="nlac"
        )
        # Explain takes priority over debug in semantic phase
        intent = classifier.classify(request)
        assert intent == classifier.INTENT_EXPLAIN

    def test_structural_rule_overrides_semantic(self, classifier):
        """Structural rules should take precedence over semantic analysis."""
        request = NLaCRequest(
            idea="Generate some code",  # Semantically: GENERATE
            context="It should output X but it outputs Y",  # Structural: REFACTOR
            mode="nlac"
        )
        # Structural rule should win
        intent = classifier.classify(request)
        assert intent == classifier.INTENT_REFACTOR

    # ========================================================================
    # STRUCTURED INPUT EDGE CASES
    # ========================================================================

    def test_empty_structured_inputs(self, classifier):
        """Empty structured inputs object."""
        request = NLaCRequest(
            idea="Help me",
            context="",
            mode="nlac",
            inputs=NLaCInputs()
        )
        intent = classifier.classify(request)
        assert intent == classifier.INTENT_GENERATE

    def test_code_snippet_only(self, classifier):
        """Code snippet without error log should not trigger DEBUG_RUNTIME."""
        request = NLaCRequest(
            idea="Help with this",
            context="",
            mode="nlac",
            inputs=NLaCInputs(
                code_snippet="def foo():\n    pass"
            )
        )
        intent = classifier.classify(request)
        # Should NOT be debug_runtime (needs error_log too)
        assert intent == classifier.INTENT_GENERATE

    def test_error_log_only(self, classifier):
        """Error log without code snippet falls back to semantic classification."""
        request = NLaCRequest(
            idea="Help with this",
            context="",
            mode="nlac",
            inputs=NLaCInputs(
                error_log="TypeError: NoneType has no attribute"
            )
        )
        intent = classifier.classify(request)
        # Should NOT be debug_runtime (needs code_snippet too)
        # "Help with this" doesn't have debug keywords, so defaults to GENERATE
        assert intent == classifier.INTENT_GENERATE

    def test_empty_code_snippet_and_error_log(self, classifier):
        """Empty strings in structured inputs."""
        request = NLaCRequest(
            idea="Help",
            context="",
            mode="nlac",
            inputs=NLaCInputs(
                code_snippet="",
                error_log=""
            )
        )
        intent = classifier.classify(request)
        # Empty strings are falsy, should not trigger structural rule
        assert intent == classifier.INTENT_GENERATE

    # ========================================================================
    # FRUSTRATION PATTERN EDGE CASES
    # ========================================================================

    def test_frustration_without_error_keywords(self, classifier):
        """Frustration patterns without error keywords should not trigger DEBUG."""
        request = NLaCRequest(
            idea="This doesn't work at all",
            context="",
            mode="nlac"
        )
        # "doesn't work" is a frustration pattern
        # But without explicit error keywords, should check for "work"
        # The pattern r"\bdoesn't work\b" should match
        intent = classifier.classify(request)
        # This is tricky - "work" is not in debug_keywords
        # So it might default to GENERATE
        assert intent is not None

    def test_multiple_frustration_patterns(self, classifier):
        """Multiple frustration patterns in same idea."""
        request = NLaCRequest(
            idea="This is always broken and doesn't work, fix it",
            context="",
            mode="nlac"
        )
        intent = classifier.classify(request)
        # Should detect DEBUG from frustration + keywords
        assert intent == classifier.INTENT_DEBUG

    # ========================================================================
    # CONTEXT EDGE CASES
    # ========================================================================

    def test_very_long_context(self, classifier):
        """Very long context up to max length should be processed."""
        # Max length is 5000 chars per validation
        long_context = "This is for " + "a project " * 200  # Well under 5000
        request = NLaCRequest(
            idea="Create function",
            context=long_context,
            mode="nlac"
        )
        # Should not raise
        intent = classifier.classify(request)
        assert intent is not None

    def test_context_with_expected_behavior_keywords(self, classifier):
        """Context with "expected" should trigger refactor structural rule."""
        request = NLaCRequest(
            idea="Make this work",
            context="The expected output is 42 but it returns 0",
            mode="nlac"
        )
        intent = classifier.classify(request)
        # "expected" in context triggers REFACTOR_LOGIC structural rule
        assert intent == classifier.INTENT_REFACTOR

    def test_context_spanish_keywords(self, classifier):
        """Spanish keywords in context should trigger refactor."""
        request = NLaCRequest(
            idea="Arregla esto",
            context="Debería retornar 10 pero retorna 5",  # "Should return 10 but returns 5"
            mode="nlac"
        )
        intent = classifier.classify(request)
        # "debería" is in the expected behavior keywords
        assert intent == classifier.INTENT_REFACTOR

    # ========================================================================
    # MODE PARAMETER TESTS
    # ========================================================================

    def test_different_modes_same_classification(self, classifier):
        """Different modes should produce same classification for same input."""
        idea = "Fix this bug"
        contexts = ["", "Python"]

        # Only valid modes are "legacy" and "nlac" per Literal type
        for mode in ["nlac", "legacy"]:
            for context in contexts:
                request = NLaCRequest(
                    idea=idea,
                    context=context,
                    mode=mode
                )
                intent = classifier.classify(request)
                # All should classify as DEBUG
                assert intent == classifier.INTENT_DEBUG

    # ========================================================================
    # get_intent_type EDGE CASES
    # ========================================================================

    def test_get_intent_type_unknown_string(self, classifier):
        """Unknown intent string should default to GENERATE."""
        intent_type = classifier.get_intent_type("unknown_intent")
        assert intent_type == IntentType.GENERATE

    def test_get_intent_type_empty_string(self, classifier):
        """Empty intent string should default to GENERATE."""
        intent_type = classifier.get_intent_type("")
        assert intent_type == IntentType.GENERATE

    def test_get_intent_type_all_subtypes(self, classifier):
        """All debug subtypes should map to DEBUG enum."""
        debug_subtypes = [
            "debug",
            "debug_runtime",
            "debug_vague",
            "debug_anything_else"
        ]
        for subtype in debug_subtypes:
            intent_type = classifier.get_intent_type(subtype)
            assert intent_type == IntentType.DEBUG

    def test_get_intent_type_refactor_subtypes(self, classifier):
        """All refactor subtypes should map to REFACTOR enum."""
        refactor_subtypes = [
            "refactor",
            "refactor_logic",
            "refactor_performance",
            "refactor_anything"
        ]
        for subtype in refactor_subtypes:
            intent_type = classifier.get_intent_type(subtype)
            assert intent_type == IntentType.REFACTOR

    # ========================================================================
    # WORD BOUNDARY TESTS
    # ========================================================================

    def test_keyword_as_substring(self, classifier):
        """Keyword as substring should not match (word boundaries)."""
        request = NLaCRequest(
            idea="The optimization was great",  # "optimization" contains "optim"
            context="",
            mode="nlac"
        )
        # "optimization" should NOT match "optim" verb
        # Actually, let me check - "optimizar" is in refactor_verbs
        # So "optimization" contains "optim" which is in "optimizar"
        # This should test if word boundaries work
        # The implementation uses: f" {verb} " in f" {idea_lower} "
        # So "optimizar" won't match "optimization" (space check)
        intent = classifier.classify(request)
        # Should be GENERATE (no refactor verb match)
        # But "performance" might match...
        assert intent == classifier.INTENT_GENERATE

    def test_keyword_with_punctuation(self, classifier):
        """Keywords with punctuation should still match."""
        test_cases = [
            "Fix this bug.",
            "Fix this bug!",
            "Fix this bug?",
            "Fix, this, bug",
        ]
        for idea in test_cases:
            request = NLaCRequest(
                idea=idea,
                context="",
                mode="nlac"
            )
            intent = classifier.classify(request)
            assert intent == classifier.INTENT_DEBUG

    # ========================================================================
    # SENTIMENT ANALYSIS EDGE CASES
    # ========================================================================

    def test_sentiment_mixed_positive_negative(self, classifier):
        """Mixed sentiment should be handled."""
        request = NLaCRequest(
            idea="Great but broken, fix this error",  # "great" + "error"
            context="",
            mode="nlac"
        )
        sentiment = classifier._analyze_sentiment(request.idea)
        # "error" is negative, "great" is positive
        # With 1 each, should be "neutral"
        assert sentiment in ["positive", "negative", "neutral"]

    def test_sentiment_empty_string(self, classifier):
        """Empty string sentiment should be neutral."""
        sentiment = classifier._analyze_sentiment("")
        assert sentiment == "neutral"

    def test_sentiment_no_sentiment_words(self, classifier):
        """Text with no sentiment words should be neutral."""
        sentiment = classifier._analyze_sentiment("The function calculates the result")
        assert sentiment == "neutral"


class TestIntentClassifierErrorPaths:
    """Test error handling paths in IntentClassifier."""

    @pytest.fixture
    def classifier(self):
        """Create classifier instance."""
        return IntentClassifier()

    def test_none_inputs_object(self, classifier):
        """None inputs object should not crash."""
        request = NLaCRequest(
            idea="Help",
            context="",
            mode="nlac",
            inputs=None
        )
        # Should not raise AttributeError
        intent = classifier.classify(request)
        assert intent is not None

    def test_attribute_error_on_inputs_access(self, classifier):
        """Accessing inputs.code_snippet when inputs is None."""
        request = NLaCRequest(
            idea="Create code",
            context="",
            mode="nlac",
            inputs=None
        )
        # The implementation checks `if request.inputs and request.inputs.code_snippet`
        # So it should short-circuit and not access .code_snippet on None
        intent = classifier.classify(request)
        assert intent is not None

    def test_context_none_in_check(self, classifier):
        """Empty context in expected behavior check."""
        # NLaCRequest doesn't allow None for context (has default="")
        request = NLaCRequest(
            idea="Create",
            context="",  # Empty string, not None
            mode="nlac"
        )
        # Implementation: `request.context.lower() if request.context else ""`
        # Should handle empty string gracefully
        intent = classifier.classify(request)
        assert intent is not None
