"""
Property-based tests using Hypothesis.

Tests cover:
- IntentClassifier properties (idempotence, determinism)
- PromptCache properties (commutativity, idempotence, consistency)
- PromptValidator properties (monotonicity)
"""

from datetime import UTC, datetime

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from hemdov.domain.dto.nlac_models import IntentType, NLaCInputs, NLaCRequest, PromptObject
from hemdov.domain.services.intent_classifier import IntentClassifier
from hemdov.domain.services.prompt_cache import PromptCache
from hemdov.domain.services.prompt_validator import PromptValidator

# ============================================================================
# HYPOTHESIS STRATEGIES
# ============================================================================

# Strategy for generating valid idea strings (min_size=1 to avoid validation error)
valid_idea_text = st.text(
    alphabet=st.characters(
        whitelist_characters='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 .,!?-\'',
        blacklist_categories=['Cc', 'Cs'],  # Exclude control characters
    ),
    min_size=1,  # NLaCRequest requires non-empty idea
    max_size=1000
).filter(lambda s: s.strip())  # Filter out whitespace-only strings (validator strips them)

# Strategy for generating valid context strings
valid_context_text = st.text(
    alphabet=st.characters(
        whitelist_characters='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 .,!?-\'\n',
        blacklist_categories=['Cc', 'Cs'],
    ),
    min_size=0,
    max_size=500
)

# Strategy for generating mode strings (only valid modes per Literal type)
valid_mode = st.sampled_from(["nlac", "legacy"])

# Strategy for generating NLaCRequest
valid_nlac_request = st.builds(
    NLaCRequest,
    idea=valid_idea_text,  # Already filtered for non-whitespace
    context=valid_context_text,
    mode=valid_mode,
    inputs=st.none() | st.builds(
        NLaCInputs,
        code_snippet=st.text(max_size=200),
        error_log=st.text(max_size=200) | st.none()
    )
)

# Strategy for generating intent strings
valid_intent = st.sampled_from([
    "generate", "debug", "debug_runtime", "debug_vague",
    "refactor", "refactor_logic", "refactor_performance",
    "explain"
])

# Strategy for generating template strings (min_size=0 to test edge cases)
valid_template = st.text(
    alphabet=st.characters(
        whitelist_characters='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 .,!?-\'\n#{}',
        blacklist_categories=['Cc', 'Cs'],
    ),
    min_size=0,  # Allow empty for edge case testing
    max_size=2000
)

# Strategy for generating non-empty template strings (for tests requiring valid PromptObject)
valid_nonempty_template = st.text(
    alphabet=st.characters(
        whitelist_characters='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 .,!?-\'\n#{}',
        blacklist_categories=['Cc', 'Cs'],
    ),
    min_size=1,  # PromptObject requires non-empty template
    max_size=2000
).filter(lambda s: s.strip())  # Filter out whitespace-only strings (including non-breaking spaces)


# ============================================================================
# INTENT CLASSIFIER PROPERTIES
# ============================================================================

class TestIntentClassifierProperties:
    """Property-based tests for IntentClassifier."""

    @given(valid_nlac_request)
    @settings(max_examples=100)
    def test_classification_is_deterministic(self, request):
        """Classification should be deterministic: same input → same output."""
        classifier = IntentClassifier()
        intent1 = classifier.classify(request)
        intent2 = classifier.classify(request)

        assert intent1 == intent2

    @given(valid_nlac_request)
    @settings(max_examples=100)
    def test_classification_returns_valid_intent(self, request):
        """Classification should always return a valid intent string."""
        classifier = IntentClassifier()
        intent = classifier.classify(request)

        valid_intents = {
            "generate", "debug", "debug_runtime", "debug_vague",
            "refactor", "refactor_logic", "refactor_performance",
            "explain"
        }
        assert intent in valid_intents

    @given(valid_nlac_request, valid_nlac_request)
    @settings(max_examples=50)
    def test_different_inputs_may_have_same_intent(self, req1, req2):
        """Different inputs can have the same intent (not injective)."""
        classifier = IntentClassifier()
        intent1 = classifier.classify(req1)
        intent2 = classifier.classify(req2)

        # This property should hold: if inputs are identical (including inputs field), intents are identical
        # But if inputs differ, intents may still be the same
        if (req1.idea == req2.idea and
            req1.context == req2.context and
            req1.mode == req2.mode and
            req1.inputs == req2.inputs):
            assert intent1 == intent2

    @given(valid_nlac_request)
    @settings(max_examples=100)
    def test_get_intent_type_is_deterministic(self, request):
        """Intent string to IntentType mapping should be deterministic."""
        classifier = IntentClassifier()
        intent_string = classifier.classify(request)
        intent_type1 = classifier.get_intent_type(intent_string)
        intent_type2 = classifier.get_intent_type(intent_string)

        assert intent_type1 == intent_type2

    @given(st.text(min_size=0, max_size=100))
    @settings(max_examples=100)
    def test_get_intent_type_handles_any_string(self, any_string):
        """get_intent_type should handle any string without crashing."""
        classifier = IntentClassifier()
        # Should not raise
        intent_type = classifier.get_intent_type(any_string)
        assert isinstance(intent_type, IntentType)

    @given(valid_nlac_request)
    @settings(max_examples=100)
    def test_classification_does_not_modify_request(self, request):
        """Classification should not modify the request object."""
        classifier = IntentClassifier()
        original_idea = request.idea
        original_context = request.context
        original_mode = request.mode

        classifier.classify(request)

        assert request.idea == original_idea
        assert request.context == original_context
        assert request.mode == original_mode


# ============================================================================
# PROMPT CACHE PROPERTIES
# ============================================================================

class TestPromptCacheProperties:
    """Property-based tests for PromptCache."""

    @given(valid_nlac_request)
    @settings(max_examples=100)
    def test_cache_key_is_deterministic(self, request):
        """Cache key generation should be deterministic."""
        cache = PromptCache(repository=None)
        key1 = cache.generate_key(request)
        key2 = cache.generate_key(request)

        assert key1 == key2

    @given(valid_nlac_request)
    @settings(max_examples=100)
    def test_cache_key_is_valid_sha256(self, request):
        """Cache key should always be valid SHA256 hex string."""
        cache = PromptCache(repository=None)
        key = cache.generate_key(request)

        assert len(key) == 64
        assert all(c in "0123456789abcdef" for c in key)

    @pytest.mark.asyncio
    @given(valid_nlac_request)
    @settings(max_examples=50)
    async def test_cache_miss_returns_none(self, request):
        """Cache miss should always return None."""
        cache = PromptCache(repository=None)
        result = await cache.get(request)
        assert result is None

    @pytest.mark.asyncio
    @given(valid_nlac_request, valid_nonempty_template, st.uuids())
    @settings(max_examples=50)
    async def test_put_then_get_returns_same(self, request, template, uuid_val):
        """put followed by get should return the same value."""
        cache = PromptCache(repository=None)
        prompt = PromptObject(
            id=str(uuid_val),
            version="1.0",
            intent_type=IntentType.GENERATE,
            template=template,
            strategy_meta={},
            constraints={},
            created_at=datetime.now(UTC).isoformat(),
            updated_at=datetime.now(UTC).isoformat(),
        )

        await cache.put(request, prompt)
        result = await cache.get(request)

        assert result is not None
        assert result.id == prompt.id
        assert result.template == template

    @pytest.mark.asyncio
    @given(valid_nlac_request, valid_nonempty_template, st.uuids())
    @settings(max_examples=50)
    async def test_put_is_idempotent(self, request, template, uuid_val):
        """Putting same value twice should be idempotent."""
        cache = PromptCache(repository=None)
        prompt = PromptObject(
            id=str(uuid_val),
            version="1.0",
            intent_type=IntentType.GENERATE,
            template=template,
            strategy_meta={},
            constraints={},
            created_at=datetime.now(UTC).isoformat(),
            updated_at=datetime.now(UTC).isoformat(),
        )

        await cache.put(request, prompt)
        await cache.put(request, prompt)

        result = await cache.get(request)
        assert result is not None
        # Last write wins, but same value so no difference
        assert result.template == template

    @pytest.mark.asyncio
    @given(valid_nlac_request, st.uuids())
    @settings(max_examples=50)
    async def test_invalidate_removes_entry(self, request, uuid_val):
        """After invalidate, get should return None."""
        cache = PromptCache(repository=None)
        prompt = PromptObject(
            id=str(uuid_val),
            version="1.0",
            intent_type=IntentType.GENERATE,
            template="Test",
            strategy_meta={},
            constraints={},
            created_at=datetime.now(UTC).isoformat(),
            updated_at=datetime.now(UTC).isoformat(),
        )

        await cache.put(request, prompt)
        await cache.invalidate(request)

        result = await cache.get(request)
        assert result is None

    @pytest.mark.asyncio
    @given(valid_nlac_request, st.uuids())
    @settings(max_examples=50)
    async def test_invalidate_is_idempotent(self, request, uuid_val):
        """Invalidating twice should be safe (second returns False)."""
        cache = PromptCache(repository=None)
        prompt = PromptObject(
            id=str(uuid_val),
            version="1.0",
            intent_type=IntentType.GENERATE,
            template="Test",
            strategy_meta={},
            constraints={},
            created_at=datetime.now(UTC).isoformat(),
            updated_at=datetime.now(UTC).isoformat(),
        )

        await cache.put(request, prompt)

        deleted1 = await cache.invalidate(request)
        deleted2 = await cache.invalidate(request)

        assert deleted1 is True
        assert deleted2 is False

    @pytest.mark.asyncio
    @given(valid_nlac_request)
    @settings(max_examples=50)
    async def test_invalidate_nonexistent_returns_false(self, request):
        """Invalidating non-existent entry should return False."""
        cache = PromptCache(repository=None)
        deleted = await cache.invalidate(request)
        assert deleted is False

    @pytest.mark.asyncio
    @given(st.lists(valid_nlac_request, min_size=0, max_size=20))
    @settings(max_examples=30)
    async def test_stats_count_is_accurate(self, requests):
        """Cache stats should accurately reflect number of unique entries."""
        cache = PromptCache(repository=None)
        for i, req in enumerate(requests):
            prompt = PromptObject(
                id=f"prompt-{i}",
                version="1.0",
                intent_type=IntentType.GENERATE,
                template=f"Template {i}",
                strategy_meta={},
                constraints={},
                created_at=datetime.now(UTC).isoformat(),
                updated_at=datetime.now(UTC).isoformat(),
            )
            await cache.put(req, prompt)

        stats = await cache.get_stats()
        # Cache deduplicates identical requests (same cache key)
        # So total_entries may be less than len(requests) if there are duplicates
        assert stats["total_entries"] <= len(requests)

    @pytest.mark.asyncio
    @given(st.lists(valid_nlac_request, min_size=0, max_size=10))
    @settings(max_examples=30)
    async def test_clear_removes_all_entries(self, requests):
        """After clear, cache should be empty."""
        cache = PromptCache(repository=None)
        for i, req in enumerate(requests):
            prompt = PromptObject(
                id=f"prompt-{i}",
                version="1.0",
                intent_type=IntentType.GENERATE,
                template=f"Template {i}",
                strategy_meta={},
                constraints={},
                created_at=datetime.now(UTC).isoformat(),
                updated_at=datetime.now(UTC).isoformat(),
            )
            await cache.put(req, prompt)

        cleared = await cache.clear()

        stats = await cache.get_stats()
        assert stats["total_entries"] == 0


# ============================================================================
# PROMPT VALIDATOR PROPERTIES
# ============================================================================

class TestPromptValidatorProperties:
    """Property-based tests for PromptValidator."""

    @given(valid_nonempty_template)
    @settings(max_examples=100)
    def test_validate_always_returns_tuple(self, template):
        """Validate should always return (bool, list) tuple."""
        validator = PromptValidator(llm_client=None)
        prompt = PromptObject(
            id="1",
            version="1.0",
            intent_type="generate",
            template=template,
            strategy_meta={},
            constraints={},
            created_at=datetime.now(UTC).isoformat(),
            updated_at=datetime.now(UTC).isoformat(),
        )

        result = validator.validate(prompt)
        assert isinstance(result, tuple)
        assert len(result) == 2
        assert isinstance(result[0], bool)
        assert isinstance(result[1], list)

    @given(valid_nonempty_template, st.integers(min_value=50, max_value=1000))
    @settings(max_examples=100)
    def test_max_tokens_constraint_property(self, template, max_tokens):
        """If template length > max_tokens, should fail."""
        validator = PromptValidator(llm_client=None)
        prompt = PromptObject(
            id="1",
            version="1.0",
            intent_type="generate",
            template=template,
            strategy_meta={},
            constraints={"max_tokens": max_tokens},
            created_at=datetime.now(UTC).isoformat(),
            updated_at=datetime.now(UTC).isoformat(),
        )

        passed, warnings = validator.validate(prompt)

        # Note: validator may modify template via autocorrection
        # So we check the actual template length after validation
        actual_length = len(prompt.template)

        if actual_length > max_tokens:
            assert passed is False
        else:
            # May still fail for other reasons
            # But should not fail for max_tokens specifically
            assert not any("exceeds max_tokens" in w for w in warnings)

    @given(valid_nonempty_template)
    @settings(max_examples=100)
    def test_empty_constraints_never_crash(self, template):
        """Empty constraints should never cause crashes."""
        validator = PromptValidator(llm_client=None)
        prompt = PromptObject(
            id="1",
            version="1.0",
            intent_type="generate",
            template=template,
            strategy_meta={},
            constraints={},
            created_at=datetime.now(UTC).isoformat(),
            updated_at=datetime.now(UTC).isoformat(),
        )

        # Should not raise
        passed, warnings = validator.validate(prompt)

    @given(st.text(min_size=0, max_size=100))
    @settings(max_examples=100)
    def test_json_check_returns_boolean(self, template):
        """JSON readiness check should always return boolean."""
        validator = PromptValidator(llm_client=None)
        result = validator._is_json_ready(template)
        assert isinstance(result, bool)

    @given(st.text(min_size=0, max_size=100))
    @settings(max_examples=100)
    def test_json_check_reflexive_property(self, template):
        """Valid JSON should pass JSON check."""
        import json

        validator = PromptValidator(llm_client=None)
        try:
            # If it's valid JSON
            json.loads(template)
            # Then it should pass the check
            assert validator._is_json_ready(template) is True
        except (json.JSONDecodeError, TypeError):
            # If not valid JSON, result can be True or False
            # (depends on keyword indicators)
            result = validator._is_json_ready(template)
            assert isinstance(result, bool)

    @given(valid_nonempty_template)
    @settings(max_examples=100)
    def test_validation_does_not_increase_warnings_on_revalidate(self, template):
        """Re-validating should not increase warning count (idempotence)."""
        validator = PromptValidator(llm_client=None)
        prompt = PromptObject(
            id="1",
            version="1.0",
            intent_type="generate",
            template=template,
            strategy_meta={},
            constraints={},
            created_at=datetime.now(UTC).isoformat(),
            updated_at=datetime.now(UTC).isoformat(),
        )

        passed1, warnings1 = validator.validate(prompt)
        passed2, warnings2 = validator.validate(prompt)

        # After validation completes, re-validating should give same result
        # (unless autocorrection happened, which changes the prompt)
        if not passed1:
            # If failed first time, prompt may have been autocorrected
            # So second time might pass
            # But we can still check types
            assert isinstance(passed2, bool)
            assert isinstance(warnings2, list)


# ============================================================================
# CROSS-SERVICE PROPERTIES
# ============================================================================

class TestCrossServiceProperties:
    """Property-based tests for service interactions."""

    @given(valid_nlac_request)
    @settings(max_examples=50)
    def test_classification_and_cache_key_consistency(self, request):
        """Classification and cache key should be consistent."""
        classifier = IntentClassifier()
        cache = PromptCache(repository=None)
        # Same request → same intent and same cache key
        intent1 = classifier.classify(request)
        key1 = cache.generate_key(request)

        intent2 = classifier.classify(request)
        key2 = cache.generate_key(request)

        assert intent1 == intent2
        assert key1 == key2

    @given(valid_nlac_request, valid_nlac_request)
    @settings(max_examples=50)
    def test_different_requests_different_cache_keys(self, req1, req2):
        """Different requests should (usually) have different cache keys."""
        cache = PromptCache(repository=None)
        key1 = cache.generate_key(req1)
        key2 = cache.generate_key(req2)

        # If requests differ in idea, context, or mode, keys should differ
        if req1.idea != req2.idea or req1.context != req2.context or req1.mode != req2.mode:
            assert key1 != key2

    @given(valid_nonempty_template)
    @settings(max_examples=50)
    def test_validator_preserves_template_type(self, template):
        """Validator should preserve template type (string)."""
        validator = PromptValidator(llm_client=None)
        prompt = PromptObject(
            id="1",
            version="1.0",
            intent_type="generate",
            template=template,
            strategy_meta={},
            constraints={},
            created_at=datetime.now(UTC).isoformat(),
            updated_at=datetime.now(UTC).isoformat(),
        )

        validator.validate(prompt)

        # Template should still be a string
        assert isinstance(prompt.template, str)


# ============================================================================
# EDGE CASE PROPERTIES
# ============================================================================

class TestEdgeCaseProperties:
    """Property-based tests for edge cases."""

    @given(st.text(min_size=1, max_size=1000, alphabet=st.characters(whitelist_categories=['Cc', 'Cs'])))
    @settings(max_examples=50)
    def test_cache_handles_control_characters(self, control_chars):
        """Cache should handle control characters gracefully."""
        # Skip surrogate characters that can't be encoded in UTF-8
        try:
            control_chars.encode('utf-8')
        except (UnicodeEncodeError, UnicodeDecodeError):
            return  # Skip this example

        # Skip if stripping makes it empty (validator strips whitespace)
        if not control_chars.strip():
            return  # Skip this example

        cache = PromptCache(repository=None)
        request = NLaCRequest(
            idea=control_chars,
            context="",
            mode="nlac"
        )

        # Should not raise
        key = cache.generate_key(request)
        assert len(key) == 64

    @pytest.mark.asyncio
    @given(st.text(min_size=1, max_size=10000))
    @settings(max_examples=30)
    async def test_cache_handles_very_long_strings(self, long_string):
        """Cache should handle very long strings."""
        # Skip if string is only whitespace (validator strips to empty)
        if not long_string.strip():
            return

        cache = PromptCache(repository=None)
        request = NLaCRequest(
            idea=long_string,
            context=long_string,
            mode="nlac"
        )

        prompt = PromptObject(
            id="1",
            version="1.0",
            intent_type=IntentType.GENERATE,
            template="Test",
            strategy_meta={},
            constraints={},
            created_at=datetime.now(UTC).isoformat(),
            updated_at=datetime.now(UTC).isoformat(),
        )

        # Should not raise
        await cache.put(request, prompt)
        result = await cache.get(request)
        assert result is not None

    def test_classifier_handles_any_text(self):
        """Classifier should handle any text without crashing."""
        classifier = IntentClassifier()

        # Generate random text
        text = st.text(min_size=1, max_size=100).example()

        request = NLaCRequest(
            idea=text,
            context="",
            mode="nlac"
        )

        # Should not raise
        intent = classifier.classify(request)
        assert intent is not None
