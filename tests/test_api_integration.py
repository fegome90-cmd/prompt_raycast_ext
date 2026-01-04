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

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi.testclient import TestClient
from main import app


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
        # Mock the PromptImprover module
        with patch('api.prompt_improver_api.get_prompt_improver') as mock_get_improver:
            # Setup mock improver
            mock_improver = MagicMock()
            mock_improver.return_value = mock_dspy_result
            mock_get_improver.return_value = mock_improver

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
                assert data["backend"] == "zero-shot"

                # Verify improver was called with correct arguments
                mock_improver.assert_called_once()
                call_kwargs = mock_improver.call_args[1]
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
        # Mock the PromptImprover module
        with patch('api.prompt_improver_api.get_prompt_improver') as mock_get_improver:
            # Setup mock improver
            mock_improver = MagicMock()
            mock_improver.return_value = mock_dspy_result
            mock_get_improver.return_value = mock_improver

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

        # Mock the PromptImprover module
        with patch('api.prompt_improver_api.get_prompt_improver') as mock_get_improver:
            # Setup mock improver
            mock_improver = MagicMock()
            mock_improver.return_value = mock_dspy_result
            mock_get_improver.return_value = mock_improver

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
        # Mock the PromptImprover to raise an exception
        with patch('api.prompt_improver_api.get_prompt_improver') as mock_get_improver:
            mock_improver = MagicMock()
            mock_improver.side_effect = Exception("DSPy model error")
            mock_get_improver.return_value = mock_improver

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
            assert "Prompt improvement failed" in data["detail"]


class TestResponseFormat:
    """Test response format and structure."""

    def test_response_guardrails_is_list(self, client, mock_dspy_result):
        """
        GREEN: Test that guardrails are always returned as a list.

        Verifies:
        - Guardrails field is a list in response
        - String guardrails are converted to list
        """
        with patch('api.prompt_improver_api.get_prompt_improver') as mock_get_improver:
            mock_improver = MagicMock()
            mock_improver.return_value = mock_dspy_result
            mock_get_improver.return_value = mock_improver

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
        GREEN: Test that backend field indicates zero-shot or few-shot.

        Verifies:
        - Backend field is present in response
        - Backend value is either "zero-shot" or "few-shot"
        """
        with patch('api.prompt_improver_api.get_prompt_improver') as mock_get_improver:
            mock_improver = MagicMock()
            mock_improver.return_value = mock_dspy_result
            mock_get_improver.return_value = mock_improver

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
                assert data["backend"] in ["zero-shot", "few-shot"]
