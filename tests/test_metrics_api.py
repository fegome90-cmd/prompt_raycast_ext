# tests/test_metrics_api.py
"""
Tests for metrics API endpoints.

Test coverage for:
- GET /api/v1/metrics/summary - Overall metrics summary
- GET /api/v1/metrics/trends - Trend analysis over time
- POST /api/v1/metrics/compare - A/B testing comparison
"""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime, UTC, timedelta
import asyncio

from main import app
from hemdov.domain.metrics.dimensions import (
    QualityMetrics,
    PerformanceMetrics,
    ImpactMetrics,
    PromptMetrics,
    FrameworkType,
)
from hemdov.infrastructure.persistence.metrics_repository import (
    SQLiteMetricsRepository,
)


@pytest.fixture
def test_client():
    """Create test client with in-memory database."""
    from hemdov.infrastructure.persistence.metrics_repository import (
        SQLiteMetricsRepository,
    )
    from hemdov.interfaces import container

    # Override repository with in-memory DB
    repo = SQLiteMetricsRepository(":memory:")

    # Initialize repository
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(repo.initialize())

    # Register in container
    container.register(SQLiteMetricsRepository, repo)

    client = TestClient(app)
    yield client

    # Cleanup
    loop.run_until_complete(repo.close())
    loop.close()


def test_get_metrics_summary(test_client):
    """Test GET /api/v1/metrics/summary endpoint."""
    # First, get the repository from container and insert test data
    from hemdov.infrastructure.persistence.metrics_repository import (
        SQLiteMetricsRepository,
    )
    from hemdov.interfaces import container

    repo = container.get(SQLiteMetricsRepository)

    # Create sample metrics
    metrics = PromptMetrics(
        prompt_id="test-123",
        original_idea="test idea",
        improved_prompt="# Role: Test\nThis is a test prompt.",
        quality=QualityMetrics(
            coherence_score=0.85,
            relevance_score=0.90,
            completeness_score=0.80,
            clarity_score=0.88,
            guardrails_count=3,
            has_required_structure=True,
        ),
        performance=PerformanceMetrics(
            latency_ms=5000,
            total_tokens=1000,
            cost_usd=0.01,
            provider="anthropic",
            model="claude-haiku-4-5-20251001",
            backend="zero-shot",
        ),
        impact=ImpactMetrics(
            copy_count=5,
            regeneration_count=1,
            feedback_score=4,
            reuse_count=2,
        ),
        measured_at=datetime.now(UTC),
        framework=FrameworkType.CHAIN_OF_THOUGHT,
        provider="anthropic",
        model="claude-haiku-4-5-20251001",
        backend="zero-shot",
    )

    # Save metrics
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(repo.save(metrics))
    loop.close()

    # Now call the endpoint
    response = test_client.get("/api/v1/metrics/summary")

    assert response.status_code == 200
    data = response.json()
    assert "total_prompts" in data
    assert "average_quality" in data
    assert "average_performance" in data
    assert "average_impact" in data
    assert data["total_prompts"] >= 1


def test_get_metrics_summary_empty(test_client):
    """Test GET /api/v1/metrics/summary with no data."""
    response = test_client.get("/api/v1/metrics/summary")

    assert response.status_code == 200
    data = response.json()
    assert data["total_prompts"] == 0
    assert data["average_quality"] == 0.0
    assert data["average_performance"] == 0.0
    assert data["average_impact"] == 0.0


def test_get_trends(test_client):
    """Test GET /api/v1/metrics/trends endpoint."""
    from hemdov.infrastructure.persistence.metrics_repository import (
        SQLiteMetricsRepository,
    )
    from hemdov.interfaces import container

    repo = container.get(SQLiteMetricsRepository)

    # Create sample metrics over time
    base_time = datetime.now(UTC) - timedelta(days=2)

    async def create_metrics():
        for i in range(5):
            metrics = PromptMetrics(
                prompt_id=f"test-{i}",
                original_idea=f"test idea {i}",
                improved_prompt=f"# Role: Test {i}\nThis is a test prompt.",
                quality=QualityMetrics(
                    coherence_score=0.80 + (i * 0.02),
                    relevance_score=0.85 + (i * 0.02),
                    completeness_score=0.75 + (i * 0.02),
                    clarity_score=0.82 + (i * 0.02),
                    guardrails_count=3,
                    has_required_structure=True,
                ),
                performance=PerformanceMetrics(
                    latency_ms=5000,
                    total_tokens=1000,
                    cost_usd=0.01,
                    provider="anthropic",
                    model="claude-haiku-4-5-20251001",
                    backend="zero-shot",
                ),
                impact=ImpactMetrics(
                    copy_count=5,
                    regeneration_count=1,
                    feedback_score=4,
                    reuse_count=2,
                ),
                measured_at=base_time + timedelta(hours=i),
                framework=FrameworkType.CHAIN_OF_THOUGHT,
                provider="anthropic",
                model="claude-haiku-4-5-20251001",
                backend="zero-shot",
            )
            await repo.save(metrics)

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(create_metrics())
    loop.close()

    # Call the trends endpoint
    response = test_client.get("/api/v1/metrics/trends?days=7")

    assert response.status_code == 200
    data = response.json()
    assert "period_start" in data
    assert "period_end" in data
    assert "metrics_count" in data
    assert "quality_trend" in data
    assert "performance_trend" in data
    assert "impact_trend" in data
    assert data["metrics_count"] >= 5


def test_compare_metrics(test_client):
    """Test POST /api/v1/metrics/compare endpoint for A/B testing."""
    from hemdov.infrastructure.persistence.metrics_repository import (
        SQLiteMetricsRepository,
    )
    from hemdov.interfaces import container

    repo = container.get(SQLiteMetricsRepository)

    async def create_metrics():
        # Create group A metrics (haiku model)
        for i in range(5):
            metrics = PromptMetrics(
                prompt_id=f"haiku-{i}",
                original_idea=f"test idea {i}",
                improved_prompt=f"# Role: Test {i}\nThis is a test prompt.",
                quality=QualityMetrics(
                    coherence_score=0.80,
                    relevance_score=0.85,
                    completeness_score=0.75,
                    clarity_score=0.82,
                    guardrails_count=3,
                    has_required_structure=True,
                ),
                performance=PerformanceMetrics(
                    latency_ms=5000,
                    total_tokens=1000,
                    cost_usd=0.01,
                    provider="anthropic",
                    model="claude-haiku-4-5-20251001",
                    backend="zero-shot",
                ),
                impact=ImpactMetrics(
                    copy_count=5,
                    regeneration_count=1,
                    feedback_score=4,
                    reuse_count=2,
                ),
                measured_at=datetime.now(UTC),
                framework=FrameworkType.CHAIN_OF_THOUGHT,
                provider="anthropic",
                model="claude-haiku-4-5-20251001",
                backend="zero-shot",
            )
            await repo.save(metrics)

        # Create group B metrics (sonnet model)
        for i in range(5):
            metrics = PromptMetrics(
                prompt_id=f"sonnet-{i}",
                original_idea=f"test idea {i}",
                improved_prompt=f"# Role: Test {i}\nThis is a test prompt.",
                quality=QualityMetrics(
                    coherence_score=0.85,
                    relevance_score=0.90,
                    completeness_score=0.80,
                    clarity_score=0.87,
                    guardrails_count=3,
                    has_required_structure=True,
                ),
                performance=PerformanceMetrics(
                    latency_ms=7000,
                    total_tokens=1200,
                    cost_usd=0.03,
                    provider="anthropic",
                    model="claude-sonnet-4-5-20251001",
                    backend="zero-shot",
                ),
                impact=ImpactMetrics(
                    copy_count=6,
                    regeneration_count=0,
                    feedback_score=5,
                    reuse_count=3,
                ),
                measured_at=datetime.now(UTC),
                framework=FrameworkType.CHAIN_OF_THOUGHT,
                provider="anthropic",
                model="claude-sonnet-4-5-20251001",
                backend="zero-shot",
            )
            await repo.save(metrics)

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(create_metrics())
    loop.close()

    # Call the compare endpoint
    response = test_client.post(
        "/api/v1/metrics/compare?group_a=model:claude-haiku-4-5-20251001&group_b=model:claude-sonnet-4-5-20251001"
    )

    assert response.status_code == 200
    data = response.json()
    assert "group_a" in data
    assert "group_b" in data
    assert "comparison" in data
    assert "recommendation" in data
    assert data["group_a"]["count"] >= 5
    assert data["group_b"]["count"] >= 5
