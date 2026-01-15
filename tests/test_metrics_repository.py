# tests/test_metrics_repository.py
from datetime import UTC, datetime

import pytest

from hemdov.domain.metrics.dimensions import (
    FrameworkType,
    ImpactMetrics,
    PerformanceMetrics,
    PromptMetrics,
    QualityMetrics,
)
from hemdov.infrastructure.persistence.metrics_repository import (
    SQLiteMetricsRepository,
)


@pytest.mark.asyncio
async def test_save_metrics():
    """Test saving metrics to database."""
    repo = SQLiteMetricsRepository(":memory:")
    await repo.initialize()

    # Create sample metrics
    metrics = PromptMetrics(
        prompt_id="test-123",
        original_idea="test idea",
        improved_prompt="# Role: Test\nThis is a test prompt.",
        quality=QualityMetrics(
            coherence_score=0.8,
            relevance_score=0.9,
            completeness_score=0.85,
            clarity_score=0.75,
            guardrails_count=3,
            has_required_structure=True,
        ),
        performance=PerformanceMetrics(
            latency_ms=5000,
            total_tokens=1500,
            cost_usd=0.005,
            provider="anthropic",
            model="claude-haiku-4-5-20251001",
            backend="zero-shot",
        ),
        impact=ImpactMetrics(),
        measured_at=datetime.now(UTC),
        framework=FrameworkType.CHAIN_OF_THOUGHT,
        provider="anthropic",
        model="claude-haiku-4-5-20251001",
        backend="zero-shot",
    )

    await repo.save(metrics)

    # Verify it was saved
    retrieved = await repo.get_by_id("test-123")
    assert retrieved is not None
    assert retrieved.prompt_id == "test-123"


@pytest.mark.asyncio
async def test_save_metrics_retrieves_full_data():
    """Test that saved and retrieved metrics contain all data."""
    repo = SQLiteMetricsRepository(":memory:")
    await repo.initialize()

    # Create sample metrics with all fields populated
    metrics = PromptMetrics(
        prompt_id="test-full-123",
        original_idea="test idea full",
        improved_prompt="# Role: Full Test\nThis is a full test prompt.",
        quality=QualityMetrics(
            coherence_score=0.85,
            relevance_score=0.92,
            completeness_score=0.88,
            clarity_score=0.78,
            guardrails_count=4,
            has_required_structure=True,
        ),
        performance=PerformanceMetrics(
            latency_ms=4500,
            total_tokens=1600,
            cost_usd=0.006,
            provider="anthropic",
            model="claude-haiku-4-5-20251001",
            backend="few-shot",
        ),
        impact=ImpactMetrics(
            copy_count=3,
            regeneration_count=0,
            feedback_score=5,
            reuse_count=2,
        ),
        measured_at=datetime.now(UTC),
        framework=FrameworkType.ROLE_PLAYING,
        provider="anthropic",
        model="claude-haiku-4-5-20251001",
        backend="few-shot",
    )

    await repo.save(metrics)

    # Verify full data retrieval
    retrieved = await repo.get_by_id("test-full-123")
    assert retrieved is not None
    assert retrieved.prompt_id == "test-full-123"
    assert retrieved.original_idea == "test idea full"
    assert retrieved.improved_prompt == "# Role: Full Test\nThis is a full test prompt."
    assert retrieved.quality.coherence_score == 0.85
    assert retrieved.quality.relevance_score == 0.92
    assert retrieved.performance.latency_ms == 4500
    assert retrieved.performance.total_tokens == 1600
    assert retrieved.impact.copy_count == 3
    assert retrieved.impact.feedback_score == 5
    assert retrieved.framework == FrameworkType.ROLE_PLAYING


@pytest.mark.asyncio
async def test_get_by_id_not_found():
    """Test retrieving non-existent prompt ID returns None."""
    repo = SQLiteMetricsRepository(":memory:")
    await repo.initialize()

    retrieved = await repo.get_by_id("nonexistent")
    assert retrieved is None


@pytest.mark.asyncio
async def test_get_all_pagination():
    """Test pagination in get_all."""
    repo = SQLiteMetricsRepository(":memory:")
    await repo.initialize()

    # Create 5 metrics
    for i in range(5):
        metrics = PromptMetrics(
            prompt_id=f"test-page-{i}",
            original_idea=f"idea {i}",
            improved_prompt=f"prompt {i}",
            quality=QualityMetrics(
                coherence_score=0.8,
                relevance_score=0.9,
                completeness_score=0.85,
                clarity_score=0.75,
                guardrails_count=3,
                has_required_structure=True,
            ),
            performance=PerformanceMetrics(
                latency_ms=5000,
                total_tokens=1500,
                cost_usd=0.005,
                provider="anthropic",
                model="claude-haiku-4-5-20251001",
                backend="zero-shot",
            ),
            impact=ImpactMetrics(),
            measured_at=datetime.now(UTC),
            framework=FrameworkType.CHAIN_OF_THOUGHT,
            provider="anthropic",
            model="claude-haiku-4-5-20251001",
            backend="zero-shot",
        )
        await repo.save(metrics)

    # Get first 3
    first_page = await repo.get_all(limit=3, offset=0)
    assert len(first_page) == 3

    # Get next 2
    second_page = await repo.get_all(limit=3, offset=3)
    assert len(second_page) == 2

    # Get beyond available
    empty_page = await repo.get_all(limit=3, offset=10)
    assert len(empty_page) == 0


@pytest.mark.asyncio
async def test_update_existing_metrics():
    """Test that saving with same prompt_id updates existing record."""
    repo = SQLiteMetricsRepository(":memory:")
    await repo.initialize()

    # Save initial metrics
    metrics = PromptMetrics(
        prompt_id="test-update",
        original_idea="original idea",
        improved_prompt="original prompt",
        quality=QualityMetrics(
            coherence_score=0.7,
            relevance_score=0.8,
            completeness_score=0.75,
            clarity_score=0.65,
            guardrails_count=2,
            has_required_structure=True,
        ),
        performance=PerformanceMetrics(
            latency_ms=6000,
            total_tokens=2000,
            cost_usd=0.010,
            provider="anthropic",
            model="claude-haiku-4-5-20251001",
            backend="zero-shot",
        ),
        impact=ImpactMetrics(),
        measured_at=datetime.now(UTC),
        framework=FrameworkType.CHAIN_OF_THOUGHT,
        provider="anthropic",
        model="claude-haiku-4-5-20251001",
        backend="zero-shot",
    )
    await repo.save(metrics)

    # Update with new metrics
    updated_metrics = PromptMetrics(
        prompt_id="test-update",
        original_idea="updated idea",
        improved_prompt="updated prompt",
        quality=QualityMetrics(
            coherence_score=0.9,
            relevance_score=0.95,
            completeness_score=0.90,
            clarity_score=0.85,
            guardrails_count=5,
            has_required_structure=True,
        ),
        performance=PerformanceMetrics(
            latency_ms=4000,
            total_tokens=1200,
            cost_usd=0.003,
            provider="anthropic",
            model="claude-haiku-4-5-20251001",
            backend="few-shot",
        ),
        impact=ImpactMetrics(copy_count=2),
        measured_at=datetime.now(UTC),
        framework=FrameworkType.TREE_OF_THOUGHTS,
        provider="anthropic",
        model="claude-haiku-4-5-20251001",
        backend="few-shot",
    )
    await repo.save(updated_metrics)

    # Verify update
    retrieved = await repo.get_by_id("test-update")
    assert retrieved is not None
    assert retrieved.original_idea == "updated idea"
    assert retrieved.improved_prompt == "updated prompt"
    assert retrieved.quality.coherence_score == 0.9
    assert retrieved.performance.latency_ms == 4000
    assert retrieved.framework == FrameworkType.TREE_OF_THOUGHTS


@pytest.mark.asyncio
async def test_close_connection():
    """Test closing database connection."""
    repo = SQLiteMetricsRepository(":memory:")
    await repo.initialize()

    # Save some data
    metrics = PromptMetrics(
        prompt_id="test-close",
        original_idea="test",
        improved_prompt="test",
        quality=QualityMetrics(
            coherence_score=0.8,
            relevance_score=0.9,
            completeness_score=0.85,
            clarity_score=0.75,
            guardrails_count=3,
            has_required_structure=True,
        ),
        performance=PerformanceMetrics(
            latency_ms=5000,
            total_tokens=1500,
            cost_usd=0.005,
            provider="anthropic",
            model="claude-haiku-4-5-20251001",
            backend="zero-shot",
        ),
        impact=ImpactMetrics(),
        measured_at=datetime.now(UTC),
        framework=FrameworkType.CHAIN_OF_THOUGHT,
        provider="anthropic",
        model="claude-haiku-4-5-20251001",
        backend="zero-shot",
    )
    await repo.save(metrics)

    # Close connection
    await repo.close()

    # Verify connection is closed
    assert repo._connection is None
