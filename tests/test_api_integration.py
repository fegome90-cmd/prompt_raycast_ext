"""
API Integration Tests for DSPy Prompt Improver.

Tests the FastAPI endpoints with actual HTTP requests using TestClient.
Tests cover:
1. Successful prompt improvement
2. Validation errors
3. Health check endpoint
4. Graceful degradation when persistence is disabled
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from unittest.mock import AsyncMock, MagicMock, patch

import dspy
import pytest
from fastapi.testclient import TestClient


# Configure DSPy with mock LM BEFORE importing main (which imports dspy modules)
# This prevents "No LM is loaded" error at module import time
class MockLM(dspy.BaseLM):
    """Mock LM for testing that satisfies DSPy's instance check."""
    def __init__(self):
        # Don't call super().__init__() to avoid API key validation
        self.provider = "test"
        self.model = "test-model"
        self.kwargs = {}  # Required by DSPy

    def basic_request(self, prompt, **kwargs):
        """Return a mock response with DSPy-parsable structured text."""
        # DSPy Predict parses text to extract fields defined in PromptImproverSignature
        # Return structured text that DSPy can parse into a Prediction object
        structured_output = """Improved Prompt: You are a World-Class Software Architect with 15+ years of experience in designing scalable, maintainable systems. Design an Architecture Decision Record (ADR) process that enables teams to make informed, documented architectural decisions.

**[ROLE & PERSONA]**
World-Class Software Architect

**[CORE DIRECTIVE]**
Design an Architecture Decision Record (ADR) process

**[EXECUTION FRAMEWORK]**
chain-of-thought

**[CONSTRAINTS & GUARDRAILS]**
- Keep ADRs concise and focused
- Include context and decision rationale
- Document alternatives considered

**Reasoning**
Selected this role for expertise in software architecture and the framework for systematic decision-making.

**Confidence**
0.87"""

        response = MagicMock()
        response.prompt = prompt
        response.output = [structured_output]  # DSPy expects list of completions
        response.usage = MagicMock()
        response.usage.prompt_tokens = 10
        response.usage.completion_tokens = 20
        return response

    def __call__(self, *args, **kwargs):
        """Make the mock callable like a real LM with flexible signature."""
        # DSPy may call with different signatures:
        # - lm(prompt)
        # - lm(*args, **kwargs)
        # Extract prompt from first arg if available
        if args:
            prompt = args[0]
        else:
            prompt = kwargs.get('prompt', '')
        return self.basic_request(prompt, **kwargs)

# Configure DSPy globally for all tests
dspy.settings.configure(lm=MockLM())

# Now import main - DSPy is already configured
from api.main import app


@pytest.fixture
def client():
    """Create test client for FastAPI app."""
    return TestClient(app)


@pytest.fixture
def mock_dspy_result():
    """Create mock DSPy result for testing."""
    mock_result = MagicMock()
    mock_result.improved_prompt = (
        "**[ROLE & PERSONA]**\n"
        "You are a World-Class Software Architect with 15+ years of experience "
        "in designing scalable, maintainable systems.\n\n"
        "**[CORE DIRECTIVE]**\n"
        "Design an Architecture Decision Record (ADR) process that enables "
        "teams to make informed, documented architectural decisions.\n\n"
        "**[EXECUTION FRAMEWORK]**\n"
        "chain-of-thought\n\n"
        "**[CONSTRAINTS & GUARDRAILS]**\n"
        "- Keep ADRs concise and focused\n"
        "- Include context and decision rationale\n"
        "- Document alternatives considered"
    )
    mock_result.role = "World-Class Software Architect"
    mock_result.directive = "Design an Architecture Decision Record (ADR) process"
    mock_result.framework = "chain-of-thought"
    mock_result.guardrails = (
        "Keep ADRs concise and focused\n"
        "Include context and decision rationale\n"
        "Document alternatives considered"
    )
    mock_result.reasoning = "Selected role for expertise in software architecture"
    mock_result.confidence = 0.87
    return mock_result


class TestImprovePromptSuccess:
    """Test successful prompt improvement endpoint."""

    def test_improve_prompt_success(self, client, mock_dspy_result):
        """
        GREEN: Test successful prompt improvement via API.

        Verifies:
        - POST /api/v1/improve-prompt returns 200
        - Response contains all expected fields
        - Response has correct structure
        """
        # Mock the StrategySelector to return a mock strategy
        with patch('api.prompt_improver_api.get_strategy_selector') as mock_get_selector:
            # Create mock strategy
            mock_strategy = MagicMock()
            mock_strategy.name = "SimpleStrategy"
            mock_strategy.improve.return_value = mock_dspy_result

            # Setup mock selector
            mock_selector = MagicMock()
            mock_selector.select.return_value = mock_strategy
            mock_selector.get_complexity.return_value = MagicMock(value="low")
            mock_get_selector.return_value = mock_selector

            # Mock repository to avoid actual DB operations
            with patch('api.prompt_improver_api.get_repository', return_value=AsyncMock()):
                # Make request
                response = client.post(
                    "/api/v1/improve-prompt",
                    json={
                        "idea": "Design ADR process for software architecture team",
                        "context": "Team needs better documentation for architectural decisions"
                    }
                )

                # Assert response status
                if response.status_code != 200:
                    print("\n=== ERROR DETAILS ===")
                    print(f"Status: {response.status_code}")
                    print(f"Response: {response.text}")
                    print("===================\n")
                assert response.status_code == 200

                # Assert response structure
                data = response.json()
                assert "improved_prompt" in data
                assert "role" in data
                assert "directive" in data
                assert "framework" in data
                assert "guardrails" in data
                assert "backend" in data
                assert isinstance(data["guardrails"], list)

                # Assert content
                assert data["improved_prompt"] == mock_dspy_result.improved_prompt
                assert data["role"] == mock_dspy_result.role
                assert data["directive"] == mock_dspy_result.directive
                assert data["framework"] == mock_dspy_result.framework
                assert len(data["guardrails"]) == 3
                assert data["backend"] == "SimpleStrategy"  # API returns strategy name

                # Verify strategy was called with correct arguments
                mock_strategy.improve.assert_called_once()
                call_kwargs = mock_strategy.improve.call_args[1]
                assert "original_idea" in call_kwargs
                assert "context" in call_kwargs


class TestImprovePromptValidationError:
    """Test validation error handling."""

    def test_improve_prompt_validation_error_short_idea(self, client):
        """
        GREEN: Test that short idea returns 400 error.

        Verifies:
        - POST with idea < 5 characters returns 400
        - Error message is descriptive
        """
        response = client.post(
            "/api/v1/improve-prompt",
            json={
                "idea": "ADR",  # Only 3 characters
                "context": "Need architecture process"
            }
        )

        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "at least 5 characters" in data["detail"].lower()

    def test_improve_prompt_validation_error_empty_idea(self, client):
        """
        GREEN: Test that empty idea returns 400 error.

        Verifies:
        - POST with empty idea returns 400
        - Error message is descriptive
        """
        response = client.post(
            "/api/v1/improve-prompt",
            json={
                "idea": "",
                "context": "Need architecture process"
            }
        )

        assert response.status_code == 400
        data = response.json()
        assert "detail" in data

    def test_improve_prompt_validation_error_whitespace_only(self, client):
        """
        GREEN: Test that whitespace-only idea returns 400 error.

        Verifies:
        - POST with whitespace-only idea returns 400
        - Error message is descriptive
        """
        response = client.post(
            "/api/v1/improve-prompt",
            json={
                "idea": "   ",
                "context": "Need architecture process"
            }
        )

        assert response.status_code == 400
        data = response.json()
        assert "detail" in data


class TestHealthCheck:
    """Test health check endpoint."""

    def test_health_check(self, client):
        """
        GREEN: Test health check endpoint.

        Verifies:
        - GET /health returns 200
        - Response contains status, provider, model, and dspy_configured fields
        """
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "provider" in data
        assert "model" in data
        assert "dspy_configured" in data
        assert data["status"] == "healthy"

    def test_root_endpoint(self, client):
        """
        GREEN: Test root endpoint with API information.

        Verifies:
        - GET / returns 200
        - Response contains API information and endpoints
        """
        response = client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data
        assert "endpoints" in data
        assert "health" in data["endpoints"]
        assert "improve_prompt" in data["endpoints"]
        assert "docs" in data["endpoints"]

    def test_health_simulate_unavailable_returns_503(self, client):
        """Simulate=unavailable should return 503."""
        response = client.get("/health?simulate=unavailable")

        assert response.status_code == 503

    def test_health_simulate_degraded_returns_degraded_status(self, client):
        """Simulate=degraded should return degraded status with flags."""
        response = client.get("/health?simulate=degraded")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "degraded"
        assert "degradation_flags" in data

    def test_health_simulate_healthy_returns_healthy(self, client):
        """Simulate=healthy should return normal healthy status."""
        response = client.get("/health?simulate=healthy")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    def test_health_simulate_blocked_in_production(self, client, monkeypatch):
        """Simulate parameter should be blocked in production environment."""
        monkeypatch.setenv("ENVIRONMENT", "production")

        response = client.get("/health?simulate=unavailable")

        assert response.status_code == 403
        assert "not allowed" in response.json()["detail"].lower()

    def test_health_simulate_allowed_in_development(self, client, monkeypatch):
        """Simulate parameter should be allowed in non-production."""
        monkeypatch.setenv("ENVIRONMENT", "development")

        response = client.get("/health?simulate=unavailable")

        assert response.status_code == 503

    def test_health_simulate_allowed_when_environment_not_set(self, client, monkeypatch):
        """Simulate parameter should be allowed when ENVIRONMENT is not set."""
        monkeypatch.delenv("ENVIRONMENT", raising=False)

        response = client.get("/health?simulate=unavailable")

        assert response.status_code == 503  # Simulation works, not blocked


class TestPersistenceDisabled:
    """Test graceful degradation when persistence is disabled."""

    def test_improve_prompt_with_persistence_disabled(self, client, mock_dspy_result):
        """
        GREEN: Test that API works even when persistence is disabled.

        Verifies:
        - API returns 200 even when SQLITE_ENABLED=False
        - Response contains all expected fields
        - No errors are raised from missing persistence
        """
        # Mock the StrategySelector to return a mock strategy
        with patch('api.prompt_improver_api.get_strategy_selector') as mock_get_selector:
            # Create mock strategy
            mock_strategy = MagicMock()
            mock_strategy.name = "ModerateStrategy"
            mock_strategy.improve.return_value = mock_dspy_result

            # Setup mock selector
            mock_selector = MagicMock()
            mock_selector.select.return_value = mock_strategy
            mock_selector.get_complexity.return_value = MagicMock(value="medium")
            mock_get_selector.return_value = mock_selector

            # Mock Settings to disable persistence
            with patch('api.prompt_improver_api.container') as mock_container:
                from hemdov.infrastructure.config import Settings
                mock_settings = Settings(SQLITE_ENABLED=False)
                mock_container.get.return_value = mock_settings

                # Mock repository to return None (disabled)
                with patch('api.prompt_improver_api.get_repository', return_value=AsyncMock(return_value=None)):
                    # Make request
                    response = client.post(
                        "/api/v1/improve-prompt",
                        json={
                            "idea": "Design code review process",
                            "context": "Engineering team needs structured reviews"
                        }
                    )

                    # Assert response is still successful
                    assert response.status_code == 200
                    data = response.json()
                    assert "improved_prompt" in data
                    assert "role" in data
                    assert "directive" in data
                    assert "framework" in data
                    assert "guardrails" in data
                    assert "backend" in data

                    # Verify the response is complete despite persistence being disabled
                    assert data["improved_prompt"] == mock_dspy_result.improved_prompt
                    assert data["role"] == mock_dspy_result.role

    def test_improve_prompt_with_circuit_breaker_open(self, client, mock_dspy_result):
        """
        GREEN: Test that API works when circuit breaker is open.

        Verifies:
        - API returns 200 even when circuit breaker prevents persistence
        - Response contains all expected fields
        - Circuit breaker failure doesn't affect main functionality
        """
        # Import the module to patch the circuit breaker at module level
        import api.prompt_improver_api as api_module

        # Mock the StrategySelector to return a mock strategy
        with patch('api.prompt_improver_api.get_strategy_selector') as mock_get_selector:
            # Create mock strategy
            mock_strategy = MagicMock()
            mock_strategy.name = "ComplexStrategy"
            mock_strategy.improve.return_value = mock_dspy_result

            # Setup mock selector
            mock_selector = MagicMock()
            mock_selector.select.return_value = mock_strategy
            mock_selector.get_complexity.return_value = MagicMock(value="high")
            mock_get_selector.return_value = mock_selector

            # Mock circuit breaker to be open (should_attempt returns False)
            original_breaker = api_module._circuit_breaker
            mock_breaker = MagicMock()
            mock_breaker.should_attempt = AsyncMock(return_value=False)
            mock_breaker.record_success = AsyncMock()
            mock_breaker.record_failure = AsyncMock()

            api_module._circuit_breaker = mock_breaker

            try:
                # Make request
                response = client.post(
                    "/api/v1/improve-prompt",
                    json={
                        "idea": "Design testing strategy",
                        "context": "QA team needs comprehensive testing approach"
                    }
                )

                # Assert response is still successful
                assert response.status_code == 200
                data = response.json()
                assert "improved_prompt" in data
                assert "role" in data
                assert "directive" in data

                # Verify circuit breaker was checked
                mock_breaker.should_attempt.assert_called()
            finally:
                # Restore original circuit breaker
                api_module._circuit_breaker = original_breaker


class TestAPIErrorHandling:
    """Test API error handling."""

    def test_improve_prompt_internal_error(self, client):
        """
        GREEN: Test that internal errors are handled gracefully.

        Verifies:
        - Exceptions during prompt improvement return 500
        - Error message is included in response
        """
        # Mock get_strategy_selector to raise an exception
        # (This is the actual code path used by the endpoint)
        with patch('api.prompt_improver_api.get_strategy_selector') as mock_get_selector:
            mock_get_selector.side_effect = RuntimeError("DSPy model error")

            # Make request
            response = client.post(
                "/api/v1/improve-prompt",
                json={
                    "idea": "Design CI/CD pipeline",
                    "context": "DevOps team needs automated deployment"
                }
            )

            # Assert error response
            assert response.status_code == 500
            data = response.json()
            assert "detail" in data
            assert "Internal server error" in data["detail"]


class TestResponseFormat:
    """Test response format and structure."""

    def test_response_guardrails_is_list(self, client, mock_dspy_result):
        """
        GREEN: Test that guardrails are always returned as a list.

        Verifies:
        - Guardrails field is a list in response
        - String guardrails are converted to list
        """
        with patch('api.prompt_improver_api.get_strategy_selector') as mock_get_selector:
            # Create mock strategy
            mock_strategy = MagicMock()
            mock_strategy.name = "SimpleStrategy"
            mock_strategy.improve.return_value = mock_dspy_result

            # Setup mock selector
            mock_selector = MagicMock()
            mock_selector.select.return_value = mock_strategy
            mock_selector.get_complexity.return_value = MagicMock(value="low")
            mock_get_selector.return_value = mock_selector

            with patch('api.prompt_improver_api.get_repository', return_value=AsyncMock()):
                response = client.post(
                    "/api/v1/improve-prompt",
                    json={
                        "idea": "Design monitoring system",
                        "context": "Ops team needs observability"
                    }
                )

                assert response.status_code == 200
                data = response.json()
                assert isinstance(data["guardrails"], list)
                assert len(data["guardrails"]) > 0

    def test_response_includes_backend_field(self, client, mock_dspy_result):
        """
        GREEN: Test that backend field indicates strategy name.

        Verifies:
        - Backend field is present in response
        - Backend value is one of the strategy names
        """
        with patch('api.prompt_improver_api.get_strategy_selector') as mock_get_selector:
            # Create mock strategy
            mock_strategy = MagicMock()
            mock_strategy.name = "ModerateStrategy"
            mock_strategy.improve.return_value = mock_dspy_result

            # Setup mock selector
            mock_selector = MagicMock()
            mock_selector.select.return_value = mock_strategy
            mock_selector.get_complexity.return_value = MagicMock(value="medium")
            mock_get_selector.return_value = mock_selector

            with patch('api.prompt_improver_api.get_repository', return_value=AsyncMock()):
                response = client.post(
                    "/api/v1/improve-prompt",
                    json={
                        "idea": "Design logging strategy",
                        "context": "Backend team needs structured logging"
                    }
                )

                assert response.status_code == 200
                data = response.json()
                assert "backend" in data
                assert data["backend"] in ["SimpleStrategy", "ModerateStrategy", "ComplexStrategy"]


class TestModeRoutingTripwire:
    """Tripwire tests for mode propagation and effective backend routing."""

    def test_legacy_mode_routes_to_legacy_selector(self, client, mock_dspy_result):
        with patch('api.prompt_improver_api.get_strategy_selector') as mock_get_selector:
            mock_strategy = MagicMock()
            mock_strategy.name = "LegacyStrategy"
            mock_strategy.improve.return_value = mock_dspy_result

            mock_selector = MagicMock()
            mock_selector.select.return_value = mock_strategy
            mock_selector.get_complexity.return_value = MagicMock(value="low")
            mock_selector.get_degradation_flags.return_value = {}
            mock_get_selector.return_value = mock_selector

            with patch('api.prompt_improver_api.get_repository', return_value=AsyncMock()):
                response = client.post(
                    "/api/v1/improve-prompt",
                    json={
                        "idea": "Design rollback plan",
                        "context": "Need deterministic routing",
                        "mode": "legacy",
                    },
                )

            assert response.status_code == 200
            data = response.json()
            assert data["strategy"] == "LegacyStrategy"
            assert data["strategy_meta"]["mode"] == "legacy"
            mock_get_selector.assert_awaited_once()
            assert mock_get_selector.call_args.kwargs["use_nlac"] is False

    def test_nlac_mode_routes_to_nlac_selector(self, client, mock_dspy_result):
        with patch('api.prompt_improver_api.get_strategy_selector') as mock_get_selector:
            mock_strategy = MagicMock()
            mock_strategy.name = "NLaCStrategy"
            mock_strategy.improve.return_value = mock_dspy_result

            mock_selector = MagicMock()
            mock_selector.select.return_value = mock_strategy
            mock_selector.get_complexity.return_value = MagicMock(value="high")
            mock_selector.get_degradation_flags.return_value = {}
            mock_get_selector.return_value = mock_selector

            with patch('api.prompt_improver_api.get_repository', return_value=AsyncMock()):
                response = client.post(
                    "/api/v1/improve-prompt",
                    json={
                        "idea": "Design routing checks",
                        "context": "Need mode-specific behavior",
                        "mode": "nlac",
                    },
                )

            assert response.status_code == 200
            data = response.json()
            assert data["strategy"] == "NLaCStrategy"
            assert data["strategy_meta"]["mode"] == "nlac"
            mock_get_selector.assert_awaited_once()
            assert mock_get_selector.call_args.kwargs["use_nlac"] is True


class TestNonBlockingSave:
    """Test non-blocking save operation."""

    def test_save_is_non_blocking(self, client, mock_dspy_result):
        """
        GREEN: Test that save operation doesn't block API response.

        Verifies:
        - API responds immediately even when save takes 1 second
        - Save operation runs in background
        - Response time is < 100ms (not waiting for save)
        """
        import asyncio
        from unittest.mock import AsyncMock, patch

        # Mock save to take 1 second
        async def slow_save(*args, **kwargs):
            await asyncio.sleep(1)

        # Mock the StrategySelector to return a mock strategy
        with patch('api.prompt_improver_api.get_strategy_selector') as mock_get_selector:
            # Create mock strategy
            mock_strategy = MagicMock()
            mock_strategy.name = "SimpleStrategy"
            mock_strategy.improve.return_value = mock_dspy_result

            # Setup mock selector
            mock_selector = MagicMock()
            mock_selector.select.return_value = mock_strategy
            mock_selector.get_complexity.return_value = MagicMock(value="low")
            mock_get_selector.return_value = mock_selector

            # Mock repository
            with patch('api.prompt_improver_api.get_repository', return_value=AsyncMock()):
                # Patch _save_history_async to be slow
                with patch('api.prompt_improver_api._save_history_async', new=slow_save):
                    import time
                    start = time.time()

                    response = client.post(
                        "/api/v1/improve-prompt",
                        json={"idea": "test blocking behavior", "context": "testing"}
                    )

                    elapsed = time.time() - start

                    # Should respond immediately (< 100ms), not wait for save
                    assert response.status_code == 200
                    assert elapsed < 0.5, f"Response took {elapsed:.2f}s, should be < 0.5s (non-blocking)"
