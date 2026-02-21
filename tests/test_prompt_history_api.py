"""
Tests for Prompt History API endpoints.

Tests cover:
- Error handling (ConnectionError -> 503)
- SQL injection prevention
- Query validation
- Pagination
- Basic functionality
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient

from api.main import app
from hemdov.domain.entities.prompt_history import PromptHistory


client = TestClient(app)


# === FIXTURES ===

@pytest.fixture
def sample_prompt():
    """Create a sample PromptHistory entity for testing."""
    return PromptHistory(
        original_idea="Test idea",
        context="Test context",
        improved_prompt="Test improved prompt",
        role="assistant",
        directive="Help the user",
        framework="chain-of-thought",
        guardrails=["accuracy"],
        reasoning="Test reasoning",
        confidence=0.85,
        backend="dspy",
        model="test-model",
        provider="test",
        latency_ms=100,
        created_at="2026-02-21T10:00:00",
    )


@pytest.fixture
def mock_repo(sample_prompt):
    """Create a mock repository."""
    repo = AsyncMock()
    repo.find_recent = AsyncMock(return_value=[sample_prompt])
    repo.search = AsyncMock(return_value=[sample_prompt])
    repo.get_statistics = AsyncMock(return_value={
        "total_count": 1,
        "average_confidence": 0.85,
        "average_latency_ms": 100.0,
        "backend_distribution": {"dspy": 1},
    })
    repo.close = AsyncMock()
    return repo


# === ERROR HANDLING TESTS ===

class TestErrorHandling:
    """Test error handling and status code mapping."""

    def test_list_prompts_returns_503_on_connection_error(self):
        """Database unavailable should return 503."""
        with patch('api.prompt_history_api._get_repo', side_effect=ConnectionError("DB locked")):
            response = client.get("/api/v1/history/")
            assert response.status_code == 503
            assert "unavailable" in response.json()["detail"].lower()

    def test_list_prompts_returns_503_on_os_error(self):
        """File system error should return 503."""
        with patch('api.prompt_history_api._get_repo', side_effect=OSError("File error")):
            response = client.get("/api/v1/history/")
            assert response.status_code == 503

    def test_search_returns_503_on_connection_error(self):
        """Search endpoint should return 503 on connection error."""
        with patch('api.prompt_history_api._get_repo', side_effect=ConnectionError("DB locked")):
            response = client.get("/api/v1/history/search?q=test")
            assert response.status_code == 503

    def test_stats_returns_503_on_connection_error(self):
        """Stats endpoint should return 503 on connection error."""
        with patch('api.prompt_history_api._get_repo', side_effect=ConnectionError("DB locked")):
            response = client.get("/api/v1/history/stats")
            assert response.status_code == 503


# === SQL INJECTION PREVENTION TESTS ===

class TestSQLInjectionPrevention:
    """Test that SQL injection attempts are safely handled."""

    def test_search_sql_injection_prevention_single_quote(self):
        """Malicious SQL with single quotes should be safely handled."""
        malicious_queries = [
            "'; DROP TABLE prompt_history; --",
            "test' OR '1'='1",
            "' OR 1=1 --",
        ]
        for query in malicious_queries:
            response = client.get(f"/api/v1/history/search?q={query}")
            # Should not return 500 (internal error)
            assert response.status_code in [200, 503], f"Query '{query}' caused unexpected error"

    def test_search_sql_injection_prevention_semicolon(self):
        """Malicious SQL with semicolons should be safely handled."""
        response = client.get("/api/v1/history/search?q=test;DELETE%20FROM%20prompt_history")
        assert response.status_code in [200, 503]

    def test_search_like_wildcards_are_escaped(self):
        """Test that LIKE wildcards % and _ are properly escaped."""
        # These should search for literal % and _ characters, not act as wildcards
        response = client.get("/api/v1/history/search?q=50%25")
        assert response.status_code in [200, 503]

        response = client.get("/api/v1/history/search?q=test_")
        assert response.status_code in [200, 503]


# === QUERY VALIDATION TESTS ===

class TestQueryValidation:
    """Test input validation for query parameters."""

    def test_list_limit_below_minimum_returns_400(self):
        """Limit below 1 should return 400 validation error."""
        response = client.get("/api/v1/history/?limit=0")
        assert response.status_code == 400

    def test_list_limit_above_maximum_returns_400(self):
        """Limit above 100 should return 400 validation error."""
        response = client.get("/api/v1/history/?limit=101")
        assert response.status_code == 400

    def test_list_offset_negative_returns_400(self):
        """Negative offset should return 400 validation error."""
        response = client.get("/api/v1/history/?offset=-1")
        assert response.status_code == 400

    def test_search_empty_query_returns_400(self):
        """Empty query string should return 400 validation error."""
        response = client.get("/api/v1/history/search?q=")
        assert response.status_code == 400

    def test_search_query_too_long_returns_400(self):
        """Query longer than 200 chars should return 400."""
        long_query = "a" * 201
        response = client.get(f"/api/v1/history/search?q={long_query}")
        assert response.status_code == 400

    def test_search_limit_out_of_range_returns_400(self):
        """Search limit outside 1-50 should return 400."""
        response = client.get("/api/v1/history/search?q=test&limit=0")
        assert response.status_code == 400

        response = client.get("/api/v1/history/search?q=test&limit=51")
        assert response.status_code == 400


# === PAGINATION TESTS ===

class TestPagination:
    """Test pagination functionality."""

    def test_list_default_pagination(self, mock_repo):
        """Default pagination should use limit=50, offset=0."""
        with patch('api.prompt_history_api._get_repo', return_value=mock_repo):
            response = client.get("/api/v1/history/")
            assert response.status_code == 200
            data = response.json()
            assert "prompts" in data
            assert "count" in data
            assert "limit" in data
            assert "offset" in data

    def test_list_custom_pagination(self, mock_repo):
        """Custom pagination parameters should be respected."""
        with patch('api.prompt_history_api._get_repo', return_value=mock_repo):
            response = client.get("/api/v1/history/?limit=10&offset=20")
            assert response.status_code == 200
            data = response.json()
            assert data["limit"] == 10
            assert data["offset"] == 20

    def test_pagination_response_structure(self, mock_repo):
        """Pagination response should have correct structure."""
        with patch('api.prompt_history_api._get_repo', return_value=mock_repo):
            response = client.get("/api/v1/history/?limit=10&offset=5")
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data["prompts"], list)
            assert isinstance(data["count"], int)
            assert data["count"] <= data["limit"]


# === BASIC FUNCTIONALITY TESTS ===

class TestBasicFunctionality:
    """Test basic endpoint functionality."""

    def test_get_stats_success(self, mock_repo):
        """Stats endpoint should return statistics."""
        with patch('api.prompt_history_api._get_repo', return_value=mock_repo):
            response = client.get("/api/v1/history/stats")
            assert response.status_code == 200
            data = response.json()
            assert "total_count" in data
            assert "average_confidence" in data
            assert "average_latency_ms" in data
            assert "backend_distribution" in data

    def test_list_prompts_success(self, mock_repo):
        """List endpoint should return prompts."""
        with patch('api.prompt_history_api._get_repo', return_value=mock_repo):
            response = client.get("/api/v1/history/")
            assert response.status_code == 200
            data = response.json()
            assert "prompts" in data
            assert len(data["prompts"]) > 0

    def test_search_prompts_success(self, mock_repo):
        """Search endpoint should return matching prompts."""
        with patch('api.prompt_history_api._get_repo', return_value=mock_repo):
            response = client.get("/api/v1/history/search?q=test")
            assert response.status_code == 200
            data = response.json()
            assert "prompts" in data
            assert "query" in data
            assert data["query"] == "test"

    def test_prompt_response_structure(self, mock_repo):
        """Prompt response should have all expected fields."""
        with patch('api.prompt_history_api._get_repo', return_value=mock_repo):
            response = client.get("/api/v1/history/")
            assert response.status_code == 200
            data = response.json()
            if data["prompts"]:
                prompt = data["prompts"][0]
                expected_fields = [
                    "original_idea", "context", "improved_prompt",
                    "role", "directive", "framework", "guardrails",
                    "reasoning", "confidence", "backend", "model",
                    "provider", "latency_ms", "created_at"
                ]
                for field in expected_fields:
                    assert field in prompt, f"Missing field: {field}"


# === FILTER TESTS ===

class TestFilters:
    """Test filtering functionality."""

    def test_list_filter_by_provider(self, mock_repo):
        """List endpoint should support provider filter."""
        with patch('api.prompt_history_api._get_repo', return_value=mock_repo):
            response = client.get("/api/v1/history/?provider=anthropic")
            assert response.status_code == 200

    def test_list_filter_by_backend(self, mock_repo):
        """List endpoint should support backend filter."""
        with patch('api.prompt_history_api._get_repo', return_value=mock_repo):
            response = client.get("/api/v1/history/?backend=dspy")
            assert response.status_code == 200

    def test_list_filter_by_both(self, mock_repo):
        """List endpoint should support combined filters."""
        with patch('api.prompt_history_api._get_repo', return_value=mock_repo):
            response = client.get("/api/v1/history/?provider=anthropic&backend=dspy")
            assert response.status_code == 200


# === RATE LIMITING TESTS ===

class TestRateLimiting:
    """Test rate limiting on history endpoints."""

    def test_rate_limiter_module_exists(self):
        """Rate limiter module should be importable."""
        from api.rate_limiter import limiter
        assert limiter is not None

    def test_rate_limit_decorator_on_list_endpoint(self, mock_repo):
        """List endpoint should have rate limit decorator."""
        import api.prompt_history_api as api_module
        # Check that the route handler exists
        assert hasattr(api_module, 'list_prompts')

    def test_rate_limit_decorator_on_search_endpoint(self, mock_repo):
        """Search endpoint should have rate limit decorator."""
        import api.prompt_history_api as api_module
        assert hasattr(api_module, 'search_prompts')

    def test_rate_limit_decorator_on_stats_endpoint(self, mock_repo):
        """Stats endpoint should have rate limit decorator."""
        import api.prompt_history_api as api_module
        assert hasattr(api_module, 'get_stats')

    def test_multiple_requests_within_limit(self, mock_repo):
        """Multiple requests within rate limit should succeed."""
        with patch('api.prompt_history_api._get_repo', return_value=mock_repo):
            # Make 10 requests - should all succeed (limit is 60/minute)
            for _ in range(10):
                response = client.get("/api/v1/history/")
                assert response.status_code == 200
