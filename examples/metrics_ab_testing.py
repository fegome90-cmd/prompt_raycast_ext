#!/usr/bin/env python3
"""
Metrics A/B Testing Example

Demonstrates how to compare two groups of prompts using the metrics framework.
"""

import asyncio
from datetime import datetime, UTC, timedelta
from hemdov.infrastructure.persistence.metrics_repository import (
    SQLiteMetricsRepository,
)
from hemdov.domain.metrics.analyzers import MetricsAnalyzer


async def main() -> None:
    """Run A/B test comparison."""
    print("=" * 60)
    print("Metrics Framework: A/B Testing Example")
    print("=" * 60)

    # Initialize repository
    repo = SQLiteMetricsRepository("data/prompts.db")
    try:
        await repo.initialize()
    except Exception as e:
        print(f"\nFailed to initialize database: {e}")
        return

    try:
        # Get recent metrics
        end = datetime.now(UTC)
        start = end - timedelta(days=30)
        all_metrics = await repo.get_by_date_range(start, end, limit=500)

        if len(all_metrics) < 20:
            print("\nNeed at least 20 metrics for meaningful A/B test.")
            print(f"   Found: {len(all_metrics)}")
            return

        # Split into two groups (by model)
        print("\nSplitting metrics by model...")

        haiku_metrics = [m for m in all_metrics if "haiku" in m.model.lower()]
        sonnet_metrics = [m for m in all_metrics if "sonnet" in m.model.lower()]

        print(f"\nGroup A (Haiku):  {len(haiku_metrics)} prompts")
        print(f"Group B (Sonnet):  {len(sonnet_metrics)} prompts")

        if len(haiku_metrics) < 5 or len(sonnet_metrics) < 5:
            print("\nEach group needs at least 5 prompts for comparison.")
            return

        # Run comparison
        analyzer = MetricsAnalyzer()

        print("\n" + "=" * 60)
        print("A/B TEST RESULTS")
        print("=" * 60)

        comparison = analyzer.compare_versions(
            baseline=haiku_metrics,
            treatment=sonnet_metrics,
            baseline_name="Claude Haiku",
            treatment_name="Claude Sonnet",
        )

        # Display results
        print(f"\n{'Metric':<15} {'Haiku':>10} {'Sonnet':>10} {'Delta':>10}")
        print("-" * 50)
        print(f"{'Quality':<15} {comparison.group_a_avg_quality:>10.2%} {comparison.group_b_avg_quality:>10.2%} {comparison.quality_delta:>+9.2%}")
        print(f"{'Performance':<15} {comparison.group_a_avg_performance:>10.2%} {comparison.group_b_avg_performance:>10.2%} {comparison.performance_delta:>+9.2%}")
        print(f"{'Impact':<15} {comparison.group_a_avg_impact:>10.2%} {comparison.group_b_avg_impact:>10.2%} {comparison.impact_delta:>+9.2%}")
        print(f"{'Overall':<15} {comparison.group_a_avg_overall:>10.2%} {comparison.group_b_avg_overall:>10.2%} {comparison.overall_delta:>+9.2%}")

        print("\n" + "=" * 60)
        print(f"WINNER: {comparison.winner.replace('_', ' ').title()}")
        print("=" * 60)

        print(f"\n{comparison.recommendation}")

        # Show detailed breakdowns
        print("\n--- Haiku Grade Distribution ---")
        for grade, count in sorted(comparison.group_a_grade_dist.items()):
            print(f"  {grade}: {count}")

        print("\n--- Sonnet Grade Distribution ---")
        for grade, count in sorted(comparison.group_b_grade_dist.items()):
            print(f"  {grade}: {count}")
    finally:
        # Close repository
        await repo.close()

    print("\n" + "=" * 60)
    print("A/B test complete!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
