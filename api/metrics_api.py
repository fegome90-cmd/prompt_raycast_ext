# api/metrics_api.py
"""
FastAPI router for metrics analysis and trends.

Provides endpoints for:
- Getting metrics summary
- Trend analysis over time
- A/B testing comparison
"""

import logging
from datetime import UTC, datetime, timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query

from hemdov.domain.metrics.analyzers import (
    MetricsAnalyzer,
    TrendAnalysis,
)
from hemdov.domain.metrics.dimensions import PromptMetrics
from hemdov.infrastructure.persistence.metrics_repository import (
    SQLiteMetricsRepository,
)
from hemdov.interfaces import container

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/metrics", tags=["metrics"])


def _safe_percent(numerator: float, denominator: float) -> float | None:
    """Calculate percentage safely.

    Returns None if denominator is 0 (undefined).
    """
    return (numerator / denominator * 100) if denominator != 0 else None


def _format_percent(value: float | None) -> str:
    """Format percentage, showing N/A for undefined values."""
    return f"{value:+.1f}%" if value is not None else "N/A"


def _format_winner_recommendation(
    winner_label: str,
    overall_improvement: float | None,
    quality_change: float | None,
    performance_change: float | None,
    impact_change: float | None,
) -> str:
    """Format winner recommendation with percentage changes."""
    return (
        f"✅ {winner_label} wins: "
        f"{_format_percent(overall_improvement)} overall improvement "
        f"(Q: {_format_percent(quality_change)}, "
        f"P: {_format_percent(performance_change)}, "
        f"I: {_format_percent(impact_change)})"
    )


def _calculate_averages(metrics: list[PromptMetrics]) -> dict[str, float]:
    """Calculate average metrics from list.

    Args:
        metrics: List of PromptMetrics objects

    Returns:
        Dict with quality, performance, and impact averages (0.0 if empty list)
    """
    if not metrics:
        return {"quality": 0.0, "performance": 0.0, "impact": 0.0}

    return {
        "quality": sum(m.quality.composite_score for m in metrics) / len(metrics),
        "performance": sum(m.performance.performance_score for m in metrics) / len(metrics),
        "impact": sum(m.impact.impact_score for m in metrics) / len(metrics),
    }


async def get_metrics_repository() -> SQLiteMetricsRepository:
    """
    Get metrics repository instance from container.

    Returns:
        SQLiteMetricsRepository instance

    Raises:
        ConnectionError: If repository not registered in container
    """
    try:
        repo = container.get(SQLiteMetricsRepository)
        if repo is None:
            raise ConnectionError("Metrics repository not available")
        return repo
    except ValueError as e:
        raise ConnectionError(f"Repository not initialized: {e}") from e


@router.get("/summary")
async def get_metrics_summary(
    repo: SQLiteMetricsRepository = Depends(get_metrics_repository),
) -> dict[str, Any]:
    """
    Get overall metrics summary.

    Returns aggregate statistics across all recorded metrics:
    - total_prompts: Total number of prompts tracked
    - average_quality: Average quality score (0-1)
    - average_performance: Average performance score (0-1)
    - average_impact: Average impact score (0-1)
    - grade_distribution: Count of prompts per grade (A+, A, B, C, D)
    """
    try:
        # Get all metrics (limit to recent for performance)
        metrics = await repo.get_all(limit=1000)

        if not metrics:
            return {
                "total_prompts": 0,
                "average_quality": 0.0,
                "average_performance": 0.0,
                "average_impact": 0.0,
                "grade_distribution": {},
            }

        # Calculate averages using helper
        averages = _calculate_averages(metrics)

        # Grade distribution
        grade_dist: dict[str, int] = {}
        for m in metrics:
            grade = m.grade
            grade_dist[grade] = grade_dist.get(grade, 0) + 1

        return {
            "total_prompts": len(metrics),
            "average_quality": round(averages["quality"], 3),
            "average_performance": round(averages["performance"], 3),
            "average_impact": round(averages["impact"], 3),
            "grade_distribution": grade_dist,
        }

    # For calculation errors - log and re-raise
    except (AttributeError, TypeError, ZeroDivisionError) as e:
        logger.error(
            f"Metrics calculation error in get_metrics_summary: "
            f"{type(e).__name__}: {e}",
            exc_info=True
        )
        raise  # Global handler will convert to 500

    # For data errors - log and re-raise
    except (ValueError, KeyError) as e:
        logger.warning(f"Metrics data issue in get_metrics_summary: {type(e).__name__}: {e}")
        raise  # Global handler will convert to 400

    # For connection errors - log and re-raise
    except (ConnectionError, OSError, TimeoutError) as e:
        logger.error(
            f"Repository error in get_metrics_summary: {type(e).__name__}: {e}",
            exc_info=True
        )
        raise  # Global handler will convert to 503

    # All other exceptions propagate (KeyboardInterrupt, SystemExit, etc.)


@router.get("/trends")
async def get_trends(
    days: int = Query(7, ge=1, le=90, description="Number of days to analyze"),
    repo: SQLiteMetricsRepository = Depends(get_metrics_repository),
) -> dict[str, Any]:
    """
    Get trend analysis over time.

    Analyzes how metrics have changed over the specified time period:
    - period_start: Start of analysis period
    - period_end: End of analysis period (now)
    - metrics_count: Number of data points
    - quality_trend: Quality score trend (improving/stable/declining)
    - performance_trend: Performance score trend
    - impact_trend: Impact score trend
    - quality_change: Quality score delta
    - performance_change: Performance score delta
    - impact_change: Impact score delta
    - recommendations: List of improvement recommendations
    """
    try:
        # Calculate date range
        end_date = datetime.now(UTC)
        start_date = end_date - timedelta(days=days)

        # Get metrics in date range using indexed query
        filtered = await repo.get_by_date_range(start_date, end_date, limit=5000)

        if len(filtered) < 2:
            return {
                "period_start": start_date.isoformat(),
                "period_end": end_date.isoformat(),
                "metrics_count": len(filtered),
                "quality_trend": "insufficient_data",
                "performance_trend": "insufficient_data",
                "impact_trend": "insufficient_data",
                "recommendations": [],
            }

        # Analyze trends using MetricsAnalyzer
        analyzer = MetricsAnalyzer()
        trends: TrendAnalysis = analyzer.analyze_trends(filtered)

        return {
            "period_start": start_date.isoformat(),
            "period_end": end_date.isoformat(),
            "metrics_count": len(filtered),
            "quality_trend": trends.quality_trend.trend,
            "performance_trend": trends.performance_trend.trend,
            "impact_trend": trends.impact_trend.trend,
            "quality_change": round(trends.quality_trend.change_rate, 3),
            "performance_change": round(trends.performance_trend.change_rate, 3),
            "impact_change": round(trends.impact_trend.change_rate, 3),
            "recommendations": trends.recommendations,
        }

    # For calculation errors - log and re-raise
    except (AttributeError, TypeError, ZeroDivisionError) as e:
        logger.error(
            f"Metrics calculation error in get_trends: {type(e).__name__}: {e}",
            exc_info=True
        )
        raise  # Global handler will convert to 500

    # For data errors - log and re-raise
    except (ValueError, KeyError) as e:
        logger.warning(f"Metrics data issue in get_trends: {type(e).__name__}: {e}")
        raise  # Global handler will convert to 400

    # For connection errors - log and re-raise
    except (ConnectionError, OSError, TimeoutError) as e:
        logger.error(f"Repository error in get_trends: {type(e).__name__}: {e}", exc_info=True)
        raise  # Global handler will convert to 503

    # All other exceptions propagate (KeyboardInterrupt, SystemExit, etc.)


@router.post("/compare")
async def compare_metrics(
    group_a: str = Query(..., description="Filter for group A (e.g., 'model:haiku')"),
    group_b: str = Query(..., description="Filter for group B (e.g., 'model:sonnet')"),
    repo: SQLiteMetricsRepository = Depends(get_metrics_repository),
) -> dict[str, Any]:
    """
    Compare metrics between two groups (A/B testing).

    Performs statistical comparison between two groups of metrics:
    - group_a_stats: Statistics for group A
    - group_b_stats: Statistics for group B
    - comparison: Statistical comparison (winner, significance, etc.)
    - recommendation: Which group performs better

    Filter format: 'field:value' (e.g., 'model:claude-haiku-4-5-20251001')

    Supported fields: model, provider, backend, framework
    """
    try:
        # Get all metrics
        all_metrics = await repo.get_all(limit=5000)

        # Parse filters (simple key:value format)
        def parse_filter(f: str) -> tuple[str, str]:
            parts = f.split(":", 1)
            if len(parts) != 2:
                raise ValueError(f"Invalid filter format: {f}. Expected 'field:value'")
            return parts[0], parts[1]

        key_a, value_a = parse_filter(group_a)
        key_b, value_b = parse_filter(group_b)

        # Map field names to PromptMetrics attributes
        field_mapping = {
            "model": "model",
            "provider": "provider",
            "backend": "backend",
            "framework": "framework",
        }

        if key_a not in field_mapping or key_b not in field_mapping:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid filter field. Supported: {list(field_mapping.keys())}"
            )

        attr_a = field_mapping[key_a]
        attr_b = field_mapping[key_b]

        # Filter metrics into groups
        group_a_metrics = []
        group_b_metrics = []

        for m in all_metrics:
            # Get attribute value
            attr_val_a = getattr(m, attr_a, None)
            attr_val_b = getattr(m, attr_b, None)

            # Handle enum values
            if hasattr(attr_val_a, 'value'):
                attr_val_a = attr_val_a.value
            if hasattr(attr_val_b, 'value'):
                attr_val_b = attr_val_b.value

            if attr_val_a == value_a:
                group_a_metrics.append(m)
            if attr_val_b == value_b:
                group_b_metrics.append(m)

        if not group_a_metrics or not group_b_metrics:
            raise HTTPException(
                status_code=404,
                detail=(
                    f"One or both groups have no data. "
                    f"Group A: {len(group_a_metrics)}, Group B: {len(group_b_metrics)}"
                )
            )

        # Calculate averages using helper
        averages_a = _calculate_averages(group_a_metrics)
        averages_b = _calculate_averages(group_b_metrics)

        # Extract averages for clarity
        avg_quality_a = averages_a["quality"]
        avg_performance_a = averages_a["performance"]
        avg_impact_a = averages_a["impact"]
        avg_quality_b = averages_b["quality"]
        avg_performance_b = averages_b["performance"]
        avg_impact_b = averages_b["impact"]

        # Calculate deltas
        quality_delta = avg_quality_b - avg_quality_a
        performance_delta = avg_performance_b - avg_performance_a
        impact_delta = avg_impact_b - avg_impact_a

        # Determine winner (simple approach: overall score comparison)
        overall_a = (avg_quality_a * 0.5 + avg_performance_a * 0.25 + avg_impact_a * 0.25)
        overall_b = (avg_quality_b * 0.5 + avg_performance_b * 0.25 + avg_impact_b * 0.25)

        # Calculate percentage changes safely (handles division by zero)
        overall_improvement = _safe_percent(overall_b - overall_a, overall_a)
        quality_change = _safe_percent(quality_delta, avg_quality_a)
        performance_change = _safe_percent(performance_delta, avg_performance_a)
        impact_change = _safe_percent(impact_delta, avg_impact_a)

        # Check if metrics are valid for comparison
        metrics_valid = avg_quality_a > 0 and avg_performance_a > 0 and avg_impact_a > 0

        if overall_b > overall_a + 0.05:
            winner = "group_b"
            recommendation = _format_winner_recommendation(
                "Group B",
                overall_improvement,
                quality_change,
                performance_change,
                impact_change,
            )
        elif overall_a > overall_b + 0.05:
            winner = "group_a"
            # Recalculate for Group A perspective
            overall_improvement_a = _safe_percent(overall_a - overall_b, overall_b)
            quality_change_a = _safe_percent(-quality_delta, avg_quality_b)
            performance_change_a = _safe_percent(-performance_delta, avg_performance_b)
            impact_change_a = _safe_percent(-impact_delta, avg_impact_b)
            recommendation = _format_winner_recommendation(
                "Group A",
                overall_improvement_a,
                quality_change_a,
                performance_change_a,
                impact_change_a,
            )
        else:
            winner = "inconclusive"
            recommendation = (
                "⚖️ Results inconclusive: Insufficient evidence to declare winner. "
                "Consider increasing sample size or refining the comparison."
            )

        return {
            "group_a": {
                "filter": group_a,
                "count": len(group_a_metrics),
                "avg_quality": round(avg_quality_a, 3),
                "avg_performance": round(avg_performance_a, 3),
                "avg_impact": round(avg_impact_a, 3),
            },
            "group_b": {
                "filter": group_b,
                "count": len(group_b_metrics),
                "avg_quality": round(avg_quality_b, 3),
                "avg_performance": round(avg_performance_b, 3),
                "avg_impact": round(avg_impact_b, 3),
            },
            "comparison": {
                "quality_delta": round(quality_delta, 3),
                "performance_delta": round(performance_delta, 3),
                "impact_delta": round(impact_delta, 3),
                "winner": winner,
                "significance": "not_calculated",  # Could add t-test later
                "metrics_valid": metrics_valid,
            },
            "recommendation": recommendation,
        }

    except HTTPException:
        raise
    # For calculation errors - log and re-raise
    except (AttributeError, TypeError, ZeroDivisionError) as e:
        logger.error(
            f"Metrics calculation error in compare_metrics: {type(e).__name__}: {e}",
            exc_info=True
        )
        raise  # Global handler will convert to 500

    # For data errors - log and re-raise
    except (ValueError, KeyError) as e:
        logger.warning(f"Metrics data issue in compare_metrics: {type(e).__name__}: {e}")
        raise  # Global handler will convert to 400

    # For connection errors - log and re-raise
    except (ConnectionError, OSError, TimeoutError) as e:
        logger.error(f"Repository error in compare_metrics: {type(e).__name__}: {e}", exc_info=True)
        raise  # Global handler will convert to 503

    # All other exceptions propagate (KeyboardInterrupt, SystemExit, etc.)
