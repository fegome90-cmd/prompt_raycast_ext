"""Test metrics API exception handling.

Tests cover:
- Specific exception types (AttributeError, TypeError, ValueError, etc.)
- Database connection failures
- Repository errors
- Unexpected errors propagate (not caught)
"""

from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi.testclient import TestClient

# Import the FastAPI app
from api.main import app


@pytest.fixture
def client():
    """Create test client for FastAPI app."""
    return TestClient(app)


class TestMetricsSummaryExceptionHandling:
    """Test get_metrics_summary exception handling."""

    def test_attribute_error_returns_500(self, client):
        """AttributeError from None.quality returns 500."""
        with patch('api.metrics_api.container.get') as mock_get:
            mock_repo = Mock()
            # Create a mock metric with None quality to trigger AttributeError
            mock_metric = Mock()
            mock_metric.quality = None  # This will cause AttributeError when accessing .composite_score
            # Use AsyncMock for async methods
            mock_repo.get_all = AsyncMock(return_value=[mock_metric])
            mock_get.return_value = mock_repo

            response = client.get("/api/v1/metrics/summary")

            # Current behavior: returns 500 with generic error
            # After fix: should return 500 with specific error message
            assert response.status_code == 500

    def test_value_error_returns_400(self, client):
        """ValueError from invalid data returns 400."""
        with patch('api.metrics_api.container.get') as mock_get:
            mock_repo = Mock()
            # Use AsyncMock for async methods
            mock_repo.get_all = AsyncMock(side_effect=ValueError("Invalid filter"))
            mock_get.return_value = mock_repo

            response = client.get("/api/v1/metrics/summary")

            # DESIRED: ValueError should return 400 (bad request)
            assert response.status_code == 400

    def test_connection_error_returns_503(self, client):
        """ConnectionError returns 503 Service Unavailable."""
        with patch('api.metrics_api.container.get') as mock_get:
            mock_repo = Mock()
            # Use AsyncMock for async methods
            mock_repo.get_all = AsyncMock(side_effect=ConnectionError("DB down"))
            mock_get.return_value = mock_repo

            response = client.get("/api/v1/metrics/summary")

            # DESIRED: ConnectionError should return 503 (service unavailable)
            assert response.status_code == 503

    def test_unexpected_error_propagates(self, client):
        """Unexpected errors are caught by global handler and return 500."""
        with patch('api.metrics_api.container.get') as mock_get:
            mock_repo = Mock()
            # Use AsyncMock for async methods
            mock_repo.get_all = AsyncMock(side_effect=RuntimeError("Unexpected bug!"))
            mock_get.return_value = mock_repo

            # After fix: RuntimeError is caught by global handler and returns 500
            response = client.get("/api/v1/metrics/summary")
            assert response.status_code == 500
            assert "Internal server error" in response.json()["detail"]


class TestTrendsExceptionHandling:
    """Test get_trends exception handling."""

    def test_timeout_error_returns_504(self, client):
        """TimeoutError returns 504 Gateway Timeout."""
        with patch('api.metrics_api.container.get') as mock_get:
            mock_repo = Mock()
            # Use AsyncMock for async methods
            mock_repo.get_by_date_range = AsyncMock(side_effect=TimeoutError("Query timeout"))
            mock_get.return_value = mock_repo

            response = client.get("/api/v1/metrics/trends")

            # After fix: TimeoutError returns 504 (gateway timeout)
            assert response.status_code == 504

    def test_analyzer_initialization_error(self, client):
        """MetricsAnalyzer initialization error is caught by global handler."""
        with patch('api.metrics_api.MetricsAnalyzer') as mock_analyzer, \
             patch('api.metrics_api.container.get') as mock_get:
            mock_repo = Mock()
            # Return valid metrics to get past get_by_date_range
            mock_metric = Mock()
            mock_metric.quality.composite_score = 0.8
            mock_metric.performance.performance_score = 0.7
            mock_metric.impact.impact_score = 0.9
            mock_metric.grade = "A"
            from datetime import UTC, datetime
            mock_metric.measured_at = datetime.now(UTC)
            # Use AsyncMock for async methods
            mock_repo.get_by_date_range = AsyncMock(return_value=[mock_metric, mock_metric])
            mock_get.return_value = mock_repo

            # Mock MetricsAnalyzer to fail
            mock_analyzer.side_effect = RuntimeError("Analyzer init failed")

            # After fix: RuntimeError is caught by global handler and returns 500
            response = client.get("/api/v1/metrics/trends")
            assert response.status_code == 500
            assert "Internal server error" in response.json()["detail"]


class TestCompareExceptionHandling:
    """Test compare_metrics exception handling."""

    def test_invalid_filter_format_returns_400(self, client):
        """Invalid filter format returns 400."""
        with patch('api.metrics_api.container.get') as mock_get:
            mock_repo = Mock()
            # Use AsyncMock for async methods
            mock_repo.get_all = AsyncMock(return_value=[])
            mock_get.return_value = mock_repo

            response = client.post(
                "/api/v1/metrics/compare",
                params={"group_a": "invalid", "group_b": "model:haiku"}
            )
            # DESIRED: ValueError (invalid filter) should return 400
            assert response.status_code == 400

    def test_keyboard_interrupt_not_caught(self, client):
        """KeyboardInterrupt is NOT caught."""
        with patch('api.metrics_api.container.get') as mock_get:
            mock_repo = Mock()
            # Use AsyncMock for async methods
            mock_repo.get_all = AsyncMock(side_effect=KeyboardInterrupt())
            mock_get.return_value = mock_repo

            # Current behavior: catches and returns 500
            # After fix: should propagate KeyboardInterrupt
            # For now, expecting it to be caught (current state)
            with pytest.raises(KeyboardInterrupt):
                client.post("/api/v1/metrics/compare", params={
                    "group_a": "model:haiku",
                    "group_b": "model:sonnet"
                })

    def test_insufficient_data_returns_early(self, client):
        """Graceful handling of <2 data points."""
        with patch('api.metrics_api.container.get') as mock_get:
            mock_repo = Mock()
            # Use AsyncMock for async methods
            mock_repo.get_all = AsyncMock(return_value=[])
            mock_get.return_value = mock_repo

            response = client.post("/api/v1/metrics/compare", params={
                "group_a": "model:haiku",
                "group_b": "model:sonnet"
            })

            # Should return 404 when groups have no data
            assert response.status_code == 404

    def test_group_not_found_returns_404(self, client):
        """No metrics for comparison group returns 404."""
        with patch('api.metrics_api.container.get') as mock_get:
            mock_repo = Mock()
            # Return metrics but none match the filters
            mock_metric = Mock()
            mock_metric.quality.composite_score = 0.8
            mock_metric.performance.performance_score = 0.7
            mock_metric.impact.impact_score = 0.9
            mock_metric.model = "claude-opus-4-5"
            mock_metric.provider = "anthropic"
            # Use AsyncMock for async methods
            mock_repo.get_all = AsyncMock(return_value=[mock_metric])
            mock_get.return_value = mock_repo

            response = client.post("/api/v1/metrics/compare", params={
                "group_a": "model:nonexistent",
                "group_b": "model:haiku"
            })

            # Should return 404 when no metrics match
            assert response.status_code == 404
