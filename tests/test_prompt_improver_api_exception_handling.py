"""Test prompt improver API exception handling.

Tests cover:
- Metrics failures add warnings to response
- Strategy timeout returns 504
- LLM connection errors return 503
- Degradation flags in response
"""

import pytest
import asyncio
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, AsyncMock

# Import the FastAPI app
from api.main import app


@pytest.fixture
def client():
    """Create test client for FastAPI app."""
    return TestClient(app)


class TestMetricsExceptionHandling:
    """Test metrics calculation exception handling."""

    def test_metrics_failure_adds_warning_to_response(self, client):
        """Metrics persistence failure adds metadata."""
        with patch('api.prompt_improver_api._metrics_calculator') as mock_metrics, \
             patch('api.prompt_improver_api.get_strategy_selector') as mock_selector:
            # Mock metrics to fail with ConnectionError
            mock_metrics.calculate_from_history = Mock(side_effect=ConnectionError("DB down"))

            # Mock selector and strategy
            mock_selector_instance = Mock()
            mock_strategy = Mock()
            mock_strategy.name = "simple"
            mock_strategy.improve = Mock(return_value=Mock(
                improved_prompt="test improved prompt",
                role="Software Architect",
                directive="Design and implement",
                framework="chain-of-thought",
                guardrails="guard1\nguard2",
                reasoning=None,
                confidence=None,
            ))
            mock_selector_instance.select.return_value = mock_strategy
            mock_selector_instance.get_complexity.return_value = Mock(value="simple")
            mock_selector_instance.get_degradation_flags.return_value = {
                "knn_disabled": False,
                "complex_strategy_disabled": False,
            }
            mock_selector.return_value = mock_selector_instance

            response = client.post("/api/v1/improve-prompt", json={
                "idea": "Test idea",
                "mode": "legacy"
            })

            assert response.status_code == 200
            # DESIRED: metrics_warning should be present
            assert response.json()["metrics_warning"] is not None
            assert response.json()["degradation_flags"]["metrics_failed"] is True

    def test_metrics_value_error_skips_calculation(self, client):
        """ValueError skips metrics calculation gracefully."""
        with patch('api.prompt_improver_api._metrics_calculator') as mock_metrics, \
             patch('api.prompt_improver_api.get_strategy_selector') as mock_selector:
            # Mock metrics to fail with ValueError
            mock_metrics.calculate_from_history = Mock(side_effect=ValueError("Invalid data"))

            # Mock selector and strategy
            mock_selector_instance = Mock()
            mock_strategy = Mock()
            mock_strategy.name = "simple"
            mock_strategy.improve = Mock(return_value=Mock(
                improved_prompt="test improved prompt",
                role="Software Architect",
                directive="Design and implement",
                framework="chain-of-thought",
                guardrails="guard1\nguard2",
                reasoning=None,
                confidence=None,
            ))
            mock_selector_instance.select.return_value = mock_strategy
            mock_selector_instance.get_complexity.return_value = Mock(value="simple")
            mock_selector_instance.get_degradation_flags.return_value = {}
            mock_selector.return_value = mock_selector_instance

            response = client.post("/api/v1/improve-prompt", json={
                "idea": "Test idea",
                "mode": "legacy"
            })

            assert response.status_code == 200
            # DESIRED: metrics_warning should be present for ValueError
            assert response.json()["metrics_warning"] is not None


class TestTimeoutHandling:
    """Test strategy timeout exception handling."""

    def test_strategy_timeout_returns_504(self, client):
        """Timeout returns 504 Gateway Timeout."""
        with patch('api.prompt_improver_api.asyncio.wait_for') as mock_wait:
            mock_wait.side_effect = asyncio.TimeoutError()

            response = client.post("/api/v1/improve-prompt", json={
                "idea": "Test prompt idea",
                "mode": "legacy"
            })

            assert response.status_code == 504


class TestLLMErrorHandling:
    """Test LLM provider error handling."""

    def test_llm_connection_error_returns_503(self, client):
        """ConnectionError returns 503 Service Unavailable."""
        with patch('api.prompt_improver_api.get_strategy_selector') as mock_selector:
            mock_selector_instance = Mock()
            mock_strategy = Mock()
            mock_strategy.name = "simple"
            # Raise ConnectionError during strategy.improve() (inside try block)
            mock_strategy.improve = Mock(side_effect=ConnectionError("LLM down"))
            mock_selector_instance.select.return_value = mock_strategy
            mock_selector_instance.get_complexity.return_value = Mock(value="simple")
            mock_selector_instance.get_degradation_flags.return_value = {}
            mock_selector.return_value = mock_selector_instance

            response = client.post("/api/v1/improve-prompt", json={
                "idea": "Test prompt idea",
                "mode": "legacy"
            })

            assert response.status_code == 503


class TestDegradationFlags:
    """Test degradation flags in response."""

    def test_knn_disabled_flag_in_response(self, client):
        """knn_disabled flag appears in response when KNN fails."""
        with patch('api.prompt_improver_api._metrics_calculator') as mock_metrics, \
             patch('api.prompt_improver_api.get_strategy_selector') as mock_selector:
            # Mock metrics to succeed
            mock_metrics.calculate_from_history = Mock(return_value=Mock(
                overall_score=0.8,
                grade="A",
                quality=Mock(composite_score=0.8),
                performance=Mock(performance_score=0.7, latency_ms=100),
                impact=Mock(impact_score=0.9),
            ))

            # Mock selector and strategy
            mock_selector_instance = Mock()
            mock_strategy = Mock()
            mock_strategy.name = "nlac"
            mock_strategy.improve = Mock(return_value=Mock(
                improved_prompt="test improved prompt",
                role="Software Architect",
                directive="Design and implement",
                framework="chain-of-thought",
                guardrails="guard1\nguard2",
                reasoning=None,
                confidence=None,
            ))
            mock_selector_instance.select.return_value = mock_strategy
            mock_selector_instance.get_complexity.return_value = Mock(value="simple")
            mock_selector_instance.get_degradation_flags.return_value = {
                "knn_disabled": True,
                "complex_strategy_disabled": False,
            }
            mock_selector.return_value = mock_selector_instance

            response = client.post("/api/v1/improve-prompt", json={
                "idea": "Test prompt idea",
                "mode": "nlac"
            })

            assert response.json()["degradation_flags"]["knn_disabled"] is True

    def test_complex_strategy_disabled_flag_in_response(self, client):
        """complex_strategy_disabled flag appears in response."""
        with patch('api.prompt_improver_api._metrics_calculator') as mock_metrics, \
             patch('api.prompt_improver_api.get_strategy_selector') as mock_selector:
            # Mock metrics to succeed
            mock_metrics.calculate_from_history = Mock(return_value=Mock(
                overall_score=0.8,
                grade="A",
                quality=Mock(composite_score=0.8),
                performance=Mock(performance_score=0.7, latency_ms=100),
                impact=Mock(impact_score=0.9),
            ))

            # Mock selector and strategy
            mock_selector_instance = Mock()
            mock_strategy = Mock()
            mock_strategy.name = "moderate"
            mock_strategy.improve = Mock(return_value=Mock(
                improved_prompt="test improved prompt",
                role="Software Architect",
                directive="Design and implement",
                framework="chain-of-thought",
                guardrails="guard1\nguard2",
                reasoning=None,
                confidence=None,
            ))
            mock_selector_instance.select.return_value = mock_strategy
            mock_selector_instance.get_complexity.return_value = Mock(value="simple")
            mock_selector_instance.get_degradation_flags.return_value = {
                "knn_disabled": False,
                "complex_strategy_disabled": True,
            }
            mock_selector.return_value = mock_selector_instance

            response = client.post("/api/v1/improve-prompt", json={
                "idea": "Test prompt idea",
                "mode": "legacy"
            })

            assert response.json()["degradation_flags"]["complex_strategy_disabled"] is True

    def test_no_warning_when_metrics_succeed(self, client):
        """No warnings when metrics succeed."""
        with patch('api.prompt_improver_api._metrics_calculator') as mock_metrics, \
             patch('api.prompt_improver_api.get_strategy_selector') as mock_selector, \
             patch('api.prompt_improver_api.get_repository') as mock_repo:
            # Mock metrics to succeed
            mock_metrics.calculate_from_history = Mock(return_value=Mock(
                overall_score=0.8,
                grade="A",
                quality=Mock(composite_score=0.8),
                performance=Mock(performance_score=0.7, latency_ms=100),
                impact=Mock(impact_score=0.9),
            ))

            # Mock repository
            mock_repo.return_value = None  # SQLite disabled or circuit breaker open

            # Mock selector and strategy
            mock_selector_instance = Mock()
            mock_strategy = Mock()
            mock_strategy.name = "simple"
            mock_strategy.improve = Mock(return_value=Mock(
                improved_prompt="test improved prompt",
                role="Software Architect",
                directive="Design and implement",
                framework="chain-of-thought",
                guardrails="guard1\nguard2",
                reasoning=None,
                confidence=None,
            ))
            mock_selector_instance.select.return_value = mock_strategy
            mock_selector_instance.get_complexity.return_value = Mock(value="simple")
            mock_selector_instance.get_degradation_flags.return_value = {}
            mock_selector.return_value = mock_selector_instance

            response = client.post("/api/v1/improve-prompt", json={
                "idea": "Test prompt idea",
                "mode": "legacy"
            })

            # DESIRED: No metrics_warning when all succeeds
            assert response.json()["metrics_warning"] is None
            assert response.json()["degradation_flags"]["metrics_failed"] is False

    def test_degradation_flags_all_false_when_healthy(self, client):
        """All degradation flags are False when system is healthy."""
        with patch('api.prompt_improver_api._metrics_calculator') as mock_metrics, \
             patch('api.prompt_improver_api.get_strategy_selector') as mock_selector:
            # Mock metrics to succeed
            mock_metrics.calculate_from_history = Mock(return_value=Mock(
                overall_score=0.8,
                grade="A",
                quality=Mock(composite_score=0.8),
                performance=Mock(performance_score=0.7, latency_ms=100),
                impact=Mock(impact_score=0.9),
            ))

            # Mock selector and strategy
            mock_selector_instance = Mock()
            mock_strategy = Mock()
            mock_strategy.name = "simple"
            mock_strategy.improve = Mock(return_value=Mock(
                improved_prompt="test improved prompt",
                role="Software Architect",
                directive="Design and implement",
                framework="chain-of-thought",
                guardrails="guard1\nguard2",
                reasoning=None,
                confidence=None,
            ))
            mock_selector_instance.select.return_value = mock_strategy
            mock_selector_instance.get_complexity.return_value = Mock(value="simple")
            mock_selector_instance.get_degradation_flags.return_value = {
                "knn_disabled": False,
                "complex_strategy_disabled": False,
            }
            mock_selector.return_value = mock_selector_instance

            response = client.post("/api/v1/improve-prompt", json={
                "idea": "Test prompt idea",
                "mode": "legacy"
            })

            flags = response.json()["degradation_flags"]
            assert flags["metrics_failed"] is False
            assert flags["knn_disabled"] is False
            assert flags["complex_strategy_disabled"] is False
