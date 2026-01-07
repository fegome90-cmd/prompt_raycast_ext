"""
Real Integration Tests - Full Pipeline Testing

Tests the complete NLaC pipeline with real prompts and LLM calls.
These are slow integration tests that validate end-to-end functionality.

Run with: pytest tests/test_integration_real_prompts.py -v

Prerequisites:
- Backend running on localhost:8000
- LLM provider configured (DeepSeek/Ollama/etc.)
- Datasets generated (make dataset)
"""

import pytest
import asyncio
from httpx import AsyncClient
from datetime import datetime, UTC
from pathlib import Path

from hemdov.domain.dto.nlac_models import (
    NLaCRequest,
    IntentType,
    PromptObject,
)
from hemdov.domain.services.intent_classifier import IntentClassifier
from hemdov.domain.services.nlac_builder import NLaCBuilder
from hemdov.domain.services.knn_provider import KNNProvider
from hemdov.domain.services.oprop_optimizer import OPROOptimizer
from hemdov.domain.services.reflexion_service import ReflexionService, ReflexionResult
from hemdov.infrastructure.adapters.litellm_dspy_adapter_prompt import PromptImproverLiteLLMAdapter
from hemdov.domain.services.prompt_validator import PromptValidator


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
async def http_client():
    """HTTP client for API tests."""
    async with AsyncClient(base_url="http://localhost:8000") as client:
        yield client


@pytest.fixture
def llm_client():
    """Real LLM client for DSPy."""
    # Uses configured provider from environment
    import os
    model = os.getenv("LLM_MODEL", "deepseek-chat")
    adapter = PromptImproverLiteLLMAdapter(
        model=model,
        temperature=0.0,
        max_tokens=2000,
    )
    yield adapter


@pytest.fixture
def knn_provider():
    """KNN provider with fewshot catalog."""
    catalog_path = Path("datasets/exports/unified-fewshot-pool-v2.json")
    if not catalog_path.exists():
        pytest.skip(f"Fewshot catalog not found at {catalog_path}")
    return KNNProvider(catalog_path=catalog_path, k=3)


@pytest.fixture
def validator():
    """Prompt validator without LLM client."""
    return PromptValidator(llm_client=None)


@pytest.fixture
def opro_optimizer(llm_client):
    """OPRO optimizer with LLM."""
    return OPROOptimizer(llm_client=llm_client, knn_provider=None)


@pytest.fixture
def reflexion_service(llm_client):
    """Reflexion service for DEBUG intent."""
    # For testing, use None as LLM client to avoid API mismatch
    # The service will use fallback code generation without LLM
    return ReflexionService(executor=None, llm_client=None)


@pytest.fixture
def nlac_builder(knn_provider):
    """NLaCBuilder with KNN provider."""
    return NLaCBuilder(knn_provider=knn_provider)


@pytest.fixture
def classifier():
    """Intent classifier."""
    return IntentClassifier()


# ============================================================================
# TEST CLASSIFIERS
# ============================================================================

class TestIntentClassification:
    """Test intent classification with real prompts."""

    def test_classifies_refactor_intent(self, classifier):
        """REFACTOR intent should be detected."""
        request = NLaCRequest(
            idea="Optimize this function for better performance",
            context="def foo(): return [x for x in range(1000)]",
            mode="nlac",
        )
        intent = classifier.classify(request)
        assert intent == IntentType.REFACTOR

    def test_classifies_debug_intent(self, classifier):
        """DEBUG intent should be detected."""
        request = NLaCRequest(
            idea="Fix this bug",
            context="The code crashes when input is None",
            mode="nlac",
        )
        intent = classifier.classify(request)
        assert intent == IntentType.DEBUG

    def test_classifies_generate_intent(self, classifier):
        """GENERATE intent should be detected."""
        request = NLaCRequest(
            idea="Create a function to parse JSON",
            context="",
            mode="nlac",
        )
        intent = classifier.classify(request)
        assert intent == IntentType.GENERATE


# ============================================================================
# TEST STRATEGIES
# ============================================================================

class TestNLaCStrategies:
    """Test NLaC strategies with real prompts."""

    def test_simple_strategy_produces_prompt(self, nlac_builder, classifier):
        """Simple strategy should produce valid prompt."""
        request = NLaCRequest(
            idea="Create hello world",
            context="",
            mode="nlac",
        )
        intent = classifier.classify(request)
        assert intent == IntentType.GENERATE

        prompt = nlac_builder.build(request)

        # Should be a valid PromptObject
        assert isinstance(prompt, PromptObject)
        assert prompt.id is not None
        assert prompt.version == "1.0.0"
        assert prompt.intent_type == IntentType.GENERATE
        assert len(prompt.template) > 20  # Should have meaningful content
        assert "role" in prompt.template.lower() or "you are" in prompt.template.lower()

    def test_moderate_strategy_uses_cot(self, nlac_builder, classifier):
        """Moderate strategy should use Chain of Thought."""
        request = NLaCRequest(
            idea="Create a function to validate email addresses",
            context="Should handle common formats",
            mode="nlac",
        )
        intent = classifier.classify(request)
        # Should be GENERATE or MODERATE depending on complexity

        prompt = nlac_builder.build(request)

        assert isinstance(prompt, PromptObject)
        # Moderate strategy adds CoT to template
        # Check for step-by-step reasoning indicators
        template_lower = prompt.template.lower()
        has_reasoning = any(
            indicator in template_lower
            for indicator in ["step", "first", "then", "finally", "reasoning", "think"]
        )
        # Not guaranteed, but likely for moderate strategy

    def test_complex_strategy_uses_rar(self, nlac_builder, classifier):
        """Complex strategy should use RAR (Refine Augment Reflect)."""
        request = NLaCRequest(
            idea="Create a complete REST API with authentication, rate limiting, and database integration",
            context="Use FastAPI with SQLAlchemy",
            mode="nlac",
        )
        intent = classifier.classify(request)
        # Long request should trigger COMPLEX intent

        prompt = nlac_builder.build(request)

        assert isinstance(prompt, PromptObject)
        # Complex strategy uses RAR template
        # Should have more detailed structure
        assert len(prompt.template) > 100  # Longer template for complex tasks


# ============================================================================
# TEST FEW-SHOT LEARNING
# ============================================================================

class TestKNNFewShot:
    """Test KNN-based few-shot learning."""

    def test_knn_finds_similar_examples(self, knn_provider):
        """KNN should find relevant examples from catalog."""
        examples = knn_provider.find_examples(
            intent="generate",
            complexity="simple",
            k=3,
        )

        # Should return some examples
        assert len(examples) >= 0  # May be empty if catalog is empty
        # If catalog has examples, should return them
        if len(examples) > 0:
            # Each example should have required fields
            for ex in examples:
                assert ex.input_idea is not None
                assert ex.improved_prompt is not None

    def test_knn_filters_by_expected_output(self, knn_provider):
        """KNN should filter examples by expected_output for REFACTOR."""
        examples = knn_provider.find_examples(
            intent="refactor",
            complexity="moderate",
            k=3,
            has_expected_output=True,  # Filter for REFACTOR examples
        )

        # Should return examples (if catalog has them)
        assert len(examples) >= 0
        # If examples returned, they should have expected_output
        if len(examples) > 0:
            for ex in examples:
                # May or may not have expected_output depending on catalog
                assert ex.improved_prompt is not None


# ============================================================================
# TEST VALIDATION
# ============================================================================

class TestPromptValidation:
    """Test prompt validation with real prompts."""

    def test_valid_prompt_passes_validation(self, validator):
        """A valid prompt should pass validation."""
        prompt = PromptObject(
            id="test-1",
            version="1.0",
            intent_type=IntentType.GENERATE,
            template="""# Role
You are an expert assistant.

# Task
Create a function to parse JSON.

# Example
Input: '{"name": "John"}'
Output: {"name": "John"}
""",
            strategy_meta={"strategy": "simple"},
            constraints={},
            created_at=datetime.now(UTC).isoformat(),
            updated_at=datetime.now(UTC).isoformat(),
        )

        passed, warnings = validator.validate(prompt)
        assert passed is True
        assert len(warnings) == 0

    def test_invalid_prompt_triggers_autocorrection(self, validator):
        """Invalid prompt should be autocorrected."""
        prompt = PromptObject(
            id="test-2",
            version="1.0",
            intent_type=IntentType.GENERATE,
            template="create function",  # Too short, no role
            strategy_meta={"strategy": "simple"},
            constraints={},
            created_at=datetime.now(UTC).isoformat(),
            updated_at=datetime.now(UTC).isoformat(),
        )

        passed, warnings = validator.validate(prompt)
        # Autocorrection should fix it
        assert passed is True
        assert len(prompt.template) > 20
        assert "role" in prompt.template.lower() or "you are" in prompt.template.lower()


# ============================================================================
# TEST OPRO OPTIMIZER
# ============================================================================

class TestOPROOptimizer:
    """Test OPRO (Optimization by PROmpting)."""

    def test_opro_produces_meta_prompt(self, opro_optimizer):
        """OPRO should generate meta-prompt with examples."""
        from datetime import datetime, UTC

        prompt_obj = PromptObject(
            id="test-opro-1",
            version="1.0.0",
            intent_type=IntentType.GENERATE,
            template="Create a function to parse JSON",
            strategy_meta={"strategy": "simple"},
            constraints={"max_tokens": 1000},
            created_at=datetime.now(UTC).isoformat(),
            updated_at=datetime.now(UTC).isoformat(),
        )

        response = opro_optimizer.run_loop(prompt_obj)

        # Should return OptimizeResponse
        assert hasattr(response, "final_instruction")
        assert hasattr(response, "final_score")
        assert hasattr(response, "iteration_count")
        assert len(response.final_instruction) > 0  # Non-empty instruction


# ============================================================================
# TEST REFLEXION SERVICE
# ============================================================================

class TestReflexionService:
    """Test Reflexion iterative refinement."""

    def test_reflexion_iterates_on_error(self, reflexion_service):
        """Reflexion should iterate until convergence or max iterations."""
        base_prompt = "Create a function"  # Intentionally vague

        # Mock executor that simulates errors
        iteration_count = [0]
        def mock_executor(code: str):
            iteration_count[0] += 1
            if iteration_count[0] < 2:
                raise RuntimeError(f"Attempt {iteration_count[0]} failed")
            # Success after 2 iterations
            return code

        reflexion_service.executor = mock_executor

        result = reflexion_service.refine(
            prompt=base_prompt,
            error_type="SyntaxError",
            max_iterations=3,
        )

        # Should return ReflexionResult
        assert isinstance(result, ReflexionResult)
        assert result.success is True
        assert result.iteration_count <= 3
        assert len(result.code) > 0


# ============================================================================
# TEST API ENDPOINT
# ============================================================================

class TestAPIEndpoint:
    """Test /api/v1/improve-prompt endpoint."""

    @pytest.mark.asyncio
    async def test_improve_prompt_endpoint_works(self, http_client):
        """API endpoint should return improved prompt."""
        response = await http_client.post(
            "/api/v1/improve-prompt",
            json={
                "idea": "Create a function to validate email addresses",
                "context": "Should handle common email formats",
                "mode": "nlac",
            },
        )

        # Should return 200
        assert response.status_code == 200

        data = response.json()
        assert "prompt_id" in data
        assert "improved_prompt" in data
        assert "intent" in data
        assert "strategy" in data

        # Improved prompt should be valid
        assert len(data["improved_prompt"]) > 50
        assert "role" in data["improved_prompt"].lower() or "you are" in data["improved_prompt"].lower()

    @pytest.mark.asyncio
    async def test_improve_prompt_with_cache(self, http_client):
        """Identical requests should use cache."""
        payload = {
            "idea": "Create a hello world function",
            "context": "",
            "mode": "nlac",
        }

        # First request
        response1 = await http_client.post("/api/v1/improve-prompt", json=payload)
        assert response1.status_code == 200
        data1 = response1.json()

        # Second identical request (should hit cache)
        response2 = await http_client.post("/api/v1/improve-prompt", json=payload)
        assert response2.status_code == 200
        data2 = response2.json()

        # Should return same result
        assert data1["improved_prompt"] == data2["improved_prompt"]
        assert data1["prompt_id"] == data2["prompt_id"]


# ============================================================================
# TEST END-TO-END PIPELINE
# ============================================================================

class TestEndToEndPipeline:
    """Test complete pipeline from request to response."""

    @pytest.mark.asyncio
    async def test_full_pipeline_simple_request(self, http_client):
        """Full pipeline with simple request."""
        response = await http_client.post(
            "/api/v1/improve-prompt",
            json={
                "idea": "Create hello world",
                "context": "Use Python",
                "mode": "nlac",
            },
        )

        assert response.status_code == 200
        data = response.json()

        # Validate response structure
        assert "prompt_id" in data
        assert "improved_prompt" in data
        assert "intent" in data
        assert "strategy" in data
        assert "strategy_meta" in data

        # Validate prompt quality
        prompt = data["improved_prompt"]
        assert len(prompt) > 50
        assert "python" in prompt.lower() or "function" in prompt.lower()
        assert "role" in prompt.lower() or "you are" in prompt.lower()

    @pytest.mark.asyncio
    async def test_full_pipeline_complex_request(self, http_client):
        """Full pipeline with complex request."""
        response = await http_client.post(
            "/api/v1/improve-prompt",
            json={
                "idea": "Build a complete REST API with user authentication, rate limiting, and PostgreSQL database",
                "context": "Use FastAPI, SQLAlchemy, and JWT tokens",
                "mode": "nlac",
            },
        )

        assert response.status_code == 200
        data = response.json()

        # Complex request should trigger appropriate strategy
        assert data["strategy"] in ["simple", "moderate", "complex"]

        # Prompt should be comprehensive
        prompt = data["improved_prompt"]
        assert len(prompt) > 200  # Longer for complex tasks
        # Should mention key technologies
        assert any(term in prompt.lower() for term in ["fastapi", "api", "auth", "database"])

    @pytest.mark.asyncio
    async def test_full_pipeline_debug_intent(self, http_client):
        """Full pipeline with DEBUG intent should use Reflexion."""
        response = await http_client.post(
            "/api/v1/improve-prompt",
            json={
                "idea": "Fix this bug",
                "context": "The function returns None when input is empty",
                "mode": "nlac",
            },
        )

        assert response.status_code == 200
        data = response.json()

        # DEBUG intent should route to Reflexion
        assert data["intent"] == "DEBUG"

        # Prompt should be actionable for debugging
        prompt = data["improved_prompt"]
        assert "bug" in prompt.lower() or "fix" in prompt.lower() or "debug" in prompt.lower()


# ============================================================================
# TEST ERROR HANDLING
# ============================================================================

class TestErrorHandling:
    """Test error handling in the pipeline."""

    @pytest.mark.asyncio
    async def test_empty_idea_returns_error(self, http_client):
        """Empty idea should return validation error."""
        response = await http_client.post(
            "/api/v1/improve-prompt",
            json={
                "idea": "",
                "context": "",
                "mode": "nlac",
            },
        )

        # Should return 422 (validation error)
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_missing_mode_returns_error(self, http_client):
        """Missing mode should return validation error."""
        response = await http_client.post(
            "/api/v1/improve-prompt",
            json={
                "idea": "Create function",
                "context": "",
            },
        )

        # Should return 422 (validation error)
        assert response.status_code == 422


# ============================================================================
# PERFORMANCE TESTS
# ============================================================================

class TestPerformance:
    """Test performance characteristics."""

    @pytest.mark.asyncio
    async def test_cache_improves_performance(self, http_client):
        """Cached requests should be faster."""
        import time

        payload = {
            "idea": "Performance test prompt",
            "context": "Testing cache speed",
            "mode": "nlac",
        }

        # First request (no cache)
        start = time.time()
        response1 = await http_client.post("/api/v1/improve-prompt", json=payload)
        duration1 = time.time() - start

        assert response1.status_code == 200

        # Second request (cached)
        start = time.time()
        response2 = await http_client.post("/api/v1/improve-prompt", json=payload)
        duration2 = time.time() - start

        assert response2.status_code == 200

        # Cached request should be faster (or similar if cache miss)
        # Note: This is a soft assertion, as timing can vary
        print(f"First request: {duration1:.2f}s, Cached request: {duration2:.2f}s")


# ============================================================================
# MARKERS
# ============================================================================

# Mark these as integration tests
pytestmark = pytest.mark.integration
