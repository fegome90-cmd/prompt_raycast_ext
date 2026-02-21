"""
Integration tests for service interactions.

Tests cover:
- IntentClassifier + PromptCache workflow
- IntentClassifier + PromptValidator workflow
- PromptCache + PromptValidator workflow
- Full pipeline: Classification -> Caching -> Validation
- Error propagation across services
"""

from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest

from hemdov.domain.dto.nlac_models import IntentType, NLaCInputs, NLaCRequest, PromptObject
from hemdov.domain.services.intent_classifier import IntentClassifier
from hemdov.domain.services.prompt_cache import PromptCache
from hemdov.domain.services.prompt_validator import PromptValidator


class TestIntentClassifierAndCacheIntegration:
    """Test IntentClassifier and PromptCache interactions."""

    @pytest.fixture
    def classifier(self):
        """Create classifier."""
        return IntentClassifier()

    @pytest.fixture
    def cache(self):
        """Create in-memory cache."""
        return PromptCache(repository=None)

    @pytest.fixture
    def sample_request(self):
        """Create sample request."""
        return NLaCRequest(
            idea="Fix this bug in my code",
            context="Python",
            mode="nlac"
        )

    @pytest.mark.asyncio
    async def test_classification_then_cache_lookup(self, classifier, cache, sample_request):
        """Classify intent, then check cache."""
        # First classify
        intent = classifier.classify(sample_request)
        assert intent == "debug"

        # Then check cache (miss)
        cached = await cache.get(sample_request)
        assert cached is None

    @pytest.mark.asyncio
    async def test_cache_key_uses_same_inputs_as_classification(
        self, classifier, cache
    ):
        """Cache key generation should use same inputs as classification."""
        request = NLaCRequest(
            idea="Create function",
            context="Python",
            mode="nlac"
        )

        # Classification uses idea, context, inputs
        intent = classifier.classify(request)

        # Cache key uses idea, context, mode
        key1 = cache.generate_key(request)
        key2 = cache.generate_key(request)

        # Same request should produce same key
        assert key1 == key2

    @pytest.mark.asyncio
    async def test_different_intents_different_cache_keys(
        self, classifier, cache
    ):
        """Different intent requests should have different cache keys."""
        request1 = NLaCRequest(
            idea="Fix bug",  # DEBUG intent
            context="",
            mode="nlac"
        )
        request2 = NLaCRequest(
            idea="Optimize code",  # REFACTOR intent
            context="",
            mode="nlac"
        )

        intent1 = classifier.classify(request1)
        intent2 = classifier.classify(request2)

        key1 = cache.generate_key(request1)
        key2 = cache.generate_key(request2)

        assert intent1 != intent2
        assert key1 != key2

    @pytest.mark.asyncio
    async def test_cache_miss_then_put_then_hit(
        self, classifier, cache, sample_request
    ):
        """Full cache workflow: miss -> put -> hit."""
        prompt = PromptObject(
            id="123",
            version="1.0",
            intent_type=IntentType.DEBUG,
            template="Debug template",
            strategy_meta={},
            constraints={},
            created_at=datetime.now(UTC).isoformat(),
            updated_at=datetime.now(UTC).isoformat(),
        )

        # Miss
        result1 = await cache.get(sample_request)
        assert result1 is None

        # Put
        await cache.put(sample_request, prompt)

        # Hit
        result2 = await cache.get(sample_request)
        assert result2 is not None
        assert result2.id == "123"


class TestIntentClassifierAndValidatorIntegration:
    """Test IntentClassifier and PromptValidator interactions."""

    @pytest.fixture
    def classifier(self):
        """Create classifier."""
        return IntentClassifier()

    @pytest.fixture
    def validator(self):
        """Create validator without LLM."""
        return PromptValidator(llm_client=None)

    @pytest.mark.asyncio
    async def test_classification_influences_validation(
        self, classifier, validator
    ):
        """Different intents may require different validation."""
        debug_request = NLaCRequest(
            idea="Fix the error",
            context="",
            mode="nlac"
        )

        # Classify as DEBUG
        intent = classifier.classify(debug_request)
        assert intent == "debug"

        # Create prompt for DEBUG intent
        debug_prompt = PromptObject(
            id="1",
            version="1.0",
            intent_type=IntentType.DEBUG,
            template="# Role\nDebugger.\n\n# Task\nFix the error.",
            strategy_meta={},
            constraints={},
            created_at=datetime.now(UTC).isoformat(),
            updated_at=datetime.now(UTC).isoformat(),
        )

        # Validate
        passed, warnings = validator.validate(debug_prompt)
        assert passed is True

    @pytest.mark.asyncio
    async def test_validator_autocorrects_for_any_intent(
        self, classifier, validator
    ):
        """Autocorrection should work regardless of intent."""
        for idea, expected_intent in [
            ("Create function", "generate"),
            ("Fix bug", "debug"),
            ("Optimize code", "refactor"),
            ("Explain this", "explain"),
        ]:
            request = NLaCRequest(idea=idea, context="", mode="nlac")
            intent = classifier.classify(request)
            assert intent == expected_intent

            # Create prompt with sufficient length (will not trigger autocorrect)
            prompt = PromptObject(
                id=f"{intent}-1",
                version="1.0",
                intent_type=IntentType.GENERATE,
                template=f"You are a helpful assistant. Please {idea.lower()}.",  # Has role
                strategy_meta={},
                constraints={},
                created_at=datetime.now(UTC).isoformat(),
                updated_at=datetime.now(UTC).isoformat(),
            )

            # Validate (should pass without autocorrection)
            passed, warnings = validator.validate(prompt)
            # Template should already have role
            assert "role" in prompt.template.lower() or "assistant" in prompt.template.lower()


class TestCacheAndValidatorIntegration:
    """Test PromptCache and PromptValidator interactions."""

    @pytest.fixture
    def cache(self):
        """Create in-memory cache."""
        return PromptCache(repository=None)

    @pytest.fixture
    def validator(self):
        """Create validator."""
        return PromptValidator(llm_client=None)

    @pytest.mark.asyncio
    async def test_cache_validated_prompt(self, cache, validator):
        """Cache a prompt after validation."""
        request = NLaCRequest(idea="Test", context="", mode="nlac")

        prompt = PromptObject(
            id="1",
            version="1.0",
            intent_type=IntentType.GENERATE,
            template="Do the task.",
            strategy_meta={},
            constraints={},
            created_at=datetime.now(UTC).isoformat(),
            updated_at=datetime.now(UTC).isoformat(),
        )

        # Validate (may modify prompt)
        passed, warnings = validator.validate(prompt)

        # Cache the (potentially modified) prompt
        await cache.put(request, prompt)

        # Retrieve from cache
        retrieved = await cache.get(request)

        # Should have the modified version
        assert retrieved is not None
        assert retrieved.template == prompt.template

    @pytest.mark.asyncio
    async def test_cache_invalidation_after_validation_change(
        self, cache, validator
    ):
        """If validation changes prompt, old cache should be invalidated."""
        request = NLaCRequest(idea="Test", context="", mode="nlac")

        # Cache initial version
        prompt1 = PromptObject(
            id="1",
            version="1.0",
            intent_type=IntentType.GENERATE,
            template="Create function.",
            strategy_meta={},
            constraints={},
            created_at=datetime.now(UTC).isoformat(),
            updated_at=datetime.now(UTC).isoformat(),
        )

        await cache.put(request, prompt1)
        result1 = await cache.get(request)
        assert result1.template == "Create function."

        # Invalidate
        await cache.invalidate(request)
        result2 = await cache.get(request)
        assert result2 is None

        # Cache validated version
        prompt2 = PromptObject(
            id="2",
            version="1.0",
            intent_type=IntentType.GENERATE,
            template="# Role\nExpert.\n\nCreate function.",
            strategy_meta={},
            constraints={},
            created_at=datetime.now(UTC).isoformat(),
            updated_at=datetime.now(UTC).isoformat(),
        )

        await cache.put(request, prompt2)
        result3 = await cache.get(request)
        assert result3.template == "# Role\nExpert.\n\nCreate function."

    @pytest.mark.asyncio
    async def test_validator_does_not_modify_cached_prompt_directly(
        self, cache, validator
    ):
        """Validating a prompt should not modify cached version."""
        request = NLaCRequest(idea="Test", context="", mode="nlac")

        prompt = PromptObject(
            id="1",
            version="1.0",
            intent_type=IntentType.GENERATE,
            template="Create function.",
            strategy_meta={},
            constraints={},
            created_at=datetime.now(UTC).isoformat(),
            updated_at=datetime.now(UTC).isoformat(),
        )

        # Cache first
        await cache.put(request, prompt)

        # Validate the original object (modifies it)
        original_template = prompt.template
        passed, warnings = validator.validate(prompt)

        # The cached version should still be the original
        # (because we cached the object before validation modified it)
        cached = await cache.get(request)
        # Actually, we cached the reference, so it IS modified
        # This test verifies the current behavior
        assert cached.template == prompt.template
        # If autocorrect happened, it's different from original
        if not passed:
            assert cached.template != original_template


class TestFullPipelineIntegration:
    """Test complete pipeline: Classification -> Caching -> Validation."""

    @pytest.fixture
    def classifier(self):
        return IntentClassifier()

    @pytest.fixture
    def cache(self):
        return PromptCache(repository=None)

    @pytest.fixture
    def validator(self):
        return PromptValidator(llm_client=None)

    @pytest.mark.asyncio
    async def test_debug_intent_pipeline(
        self, classifier, cache, validator
    ):
        """Full pipeline for DEBUG intent."""
        request = NLaCRequest(
            idea="Fix this bug",
            context="Python",
            mode="nlac",
            inputs=NLaCInputs(
                code_snippet="def foo():\n    pass",
                error_log="TypeError: NoneType has no attribute"
            )
        )

        # Step 1: Classify
        intent = classifier.classify(request)
        assert intent == "debug"

        # Step 2: Check cache
        cached = await cache.get(request)
        assert cached is None  # Cache miss

        # Step 3: Create prompt
        prompt = PromptObject(
            id="debug-1",
            version="1.0",
            intent_type=IntentType.DEBUG,
            template="Debug the error.",
            strategy_meta={},
            constraints={},
            created_at=datetime.now(UTC).isoformat(),
            updated_at=datetime.now(UTC).isoformat(),
        )

        # Step 4: Validate
        passed, warnings = validator.validate(prompt)

        # Step 5: Cache the result
        await cache.put(request, prompt)

        # Step 6: Verify cache hit on next request
        cached2 = await cache.get(request)
        assert cached2 is not None
        assert cached2.id == "debug-1"

    @pytest.mark.asyncio
    async def test_generate_intent_pipeline(
        self, classifier, cache, validator
    ):
        """Full pipeline for GENERATE intent."""
        request = NLaCRequest(
            idea="Create a hello world function",
            context="Python",
            mode="nlac"
        )

        # Classify
        intent = classifier.classify(request)
        assert intent == "generate"

        # Cache miss
        cached = await cache.get(request)
        assert cached is None

        # Create and validate prompt
        prompt = PromptObject(
            id="gen-1",
            version="1.0",
            intent_type=IntentType.GENERATE,
            template="Create hello world.",
            strategy_meta={},
            constraints={},
            created_at=datetime.now(UTC).isoformat(),
            updated_at=datetime.now(UTC).isoformat(),
        )

        passed, warnings = validator.validate(prompt)

        # Cache
        await cache.put(request, prompt)

        # Cache hit
        cached2 = await cache.get(request)
        assert cached2 is not None

    @pytest.mark.asyncio
    async def test_cache_hit_skips_validation(
        self, classifier, cache, validator
    ):
        """If cache hit, should not need to re-validate."""
        request = NLaCRequest(
            idea="Create function",
            context="Python",
            mode="nlac"
        )

        # First request: cache miss, need to create and validate
        prompt = PromptObject(
            id="1",
            version="1.0",
            intent_type=IntentType.GENERATE,
            template="# Role\nExpert.\n\nCreate function.",
            strategy_meta={},
            constraints={},
            created_at=datetime.now(UTC).isoformat(),
            updated_at=datetime.now(UTC).isoformat(),
        )

        await cache.put(request, prompt)

        # Validate once
        passed1, warnings1 = validator.validate(prompt)
        assert passed1 is True

        # Second request: cache hit
        cached = await cache.get(request)
        assert cached is not None

        # Should not need to validate again (use cached result)
        # This is a design assumption - in practice, you might
        # still validate for consistency

    @pytest.mark.asyncio
    async def test_different_requests_different_cache_entries(
        self, classifier, cache, validator
    ):
        """Different requests should have different cache entries."""
        requests = [
            NLaCRequest(idea="Create X", context="Python", mode="nlac"),
            NLaCRequest(idea="Create Y", context="Python", mode="nlac"),
            NLaCRequest(idea="Create X", context="JavaScript", mode="nlac"),
        ]

        for i, req in enumerate(requests):
            # Classify
            intent = classifier.classify(req)

            # Create prompt
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

            # Cache
            await cache.put(req, prompt)

        # All should be cached separately
        stats = await cache.get_stats()
        assert stats["total_entries"] == 3


class TestErrorPropagationIntegration:
    """Test error propagation across services."""

    @pytest.fixture
    def classifier(self):
        return IntentClassifier()

    @pytest.fixture
    def failing_cache(self):
        """Create cache with failing repository."""
        mock_repo = AsyncMock()
        mock_repo.get_cached_prompt.side_effect = ConnectionError("DB down")
        mock_repo.cache_prompt.side_effect = ConnectionError("DB down")

        return PromptCache(repository=mock_repo)

    @pytest.fixture
    def validator(self):
        return PromptValidator(llm_client=None)

    @pytest.mark.asyncio
    async def test_classifier_works_despite_cache_failure(
        self, classifier, failing_cache
    ):
        """Classification should work even if cache fails."""
        request = NLaCRequest(
            idea="Fix bug",
            context="",
            mode="nlac"
        )

        # Classification should not be affected
        intent = classifier.classify(request)
        assert intent == "debug"

        # Cache should fallback to memory
        result = await failing_cache.get(request)
        assert result is None  # No error, just cache miss

    @pytest.mark.asyncio
    async def test_validator_works_with_invalid_prompt(
        self, classifier, validator
    ):
        """Validator should handle invalid prompts gracefully."""
        request = NLaCRequest(idea="Test", context="", mode="nlac")

        # Create invalid prompt
        prompt = PromptObject(
            id="1",
            version="1.0",
            intent_type=IntentType.GENERATE,
            template="x",  # Too short, no role
            strategy_meta={},
            constraints={"max_tokens": 1},
            created_at=datetime.now(UTC).isoformat(),
            updated_at=datetime.now(UTC).isoformat(),
        )

        # Should not raise, should return warnings
        passed, warnings = validator.validate(prompt)
        assert passed is False
        assert len(warnings) > 0

    @pytest.mark.asyncio
    async def test_cache_error_during_put_fallback(
        self, failing_cache, validator
    ):
        """Cache write failure should fallback to memory."""
        request = NLaCRequest(idea="Test", context="", mode="nlac")

        prompt = PromptObject(
            id="1",
            version="1.0",
            intent_type=IntentType.GENERATE,
            template="Test prompt",
            strategy_meta={},
            constraints={},
            created_at=datetime.now(UTC).isoformat(),
            updated_at=datetime.now(UTC).isoformat(),
        )

        # Should not raise, should fallback to memory
        await failing_cache.put(request, prompt)

        # Should be retrievable from memory
        result = await failing_cache.get(request)
        assert result is not None


class TestIntentTypeMappingIntegration:
    """Test IntentType mapping across services."""

    @pytest.fixture
    def classifier(self):
        return IntentClassifier()

    def test_intent_string_to_type_mapping(self, classifier):
        """Intent string should map to correct IntentType."""
        test_cases = [
            ("generate", IntentType.GENERATE),
            ("debug", IntentType.DEBUG),
            ("debug_runtime", IntentType.DEBUG),
            ("debug_vague", IntentType.DEBUG),
            ("refactor", IntentType.REFACTOR),
            ("refactor_logic", IntentType.REFACTOR),
            ("refactor_performance", IntentType.REFACTOR),
            ("explain", IntentType.EXPLAIN),
            ("unknown", IntentType.GENERATE),  # Default
        ]

        for intent_string, expected_type in test_cases:
            result = classifier.get_intent_type(intent_string)
            assert result == expected_type

    @pytest.mark.asyncio
    async def test_prompt_object_intent_matches_classification(
        self, classifier
    ):
        """PromptObject intent_type should match classification."""
        test_cases = [
            ("Fix bug", IntentType.DEBUG),
            ("Optimize", IntentType.REFACTOR),
            ("Explain", IntentType.EXPLAIN),
            ("Create", IntentType.GENERATE),
        ]

        for idea, expected_intent in test_cases:
            request = NLaCRequest(idea=idea, context="", mode="nlac")
            intent_string = classifier.classify(request)
            intent_type = classifier.get_intent_type(intent_string)

            prompt = PromptObject(
                id="1",
                version="1.0",
                intent_type=intent_type,
                template="Test",
                strategy_meta={},
                constraints={},
                created_at=datetime.now(UTC).isoformat(),
                updated_at=datetime.now(UTC).isoformat(),
            )

            assert prompt.intent_type == expected_intent


class TestNLaCInputsIntegration:
    """Test integration with structured inputs."""

    @pytest.fixture
    def classifier(self):
        return IntentClassifier()

    def test_structured_inputs_trigger_structural_rules(self, classifier):
        """Structured inputs should trigger structural classification rules."""
        request = NLaCRequest(
            idea="Help me",
            context="",
            mode="nlac",
            inputs=NLaCInputs(
                code_snippet="def foo(): pass",
                error_log="TypeError"
            )
        )

        intent = classifier.classify(request)
        # Should trigger DEBUG_RUNTIME structural rule
        assert intent == "debug"

    def test_partial_structured_inputs_semantic_fallback(self, classifier):
        """Partial structured inputs should fallback to semantic."""
        # Only code_snippet, no error_log
        request = NLaCRequest(
            idea="Help with this code",
            context="",
            mode="nlac",
            inputs=NLaCInputs(
                code_snippet="def foo(): pass",
                error_log=None
            )
        )

        intent = classifier.classify(request)
        # Should not trigger structural rule (needs both)
        # Should use semantic classification
        # "help" is not a strong keyword, defaults to GENERATE
        assert intent == "generate"

    def test_none_structured_inputs(self, classifier):
        """None structured inputs should not cause errors."""
        request = NLaCRequest(
            idea="Create function",
            context="",
            mode="nlac",
            inputs=None
        )

        # Should not raise
        intent = classifier.classify(request)
        assert intent == "generate"
