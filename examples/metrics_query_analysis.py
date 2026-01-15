#!/usr/bin/env python3
"""
Metrics Query and Analysis Example

Demonstrates how to query metrics from the database and analyze trends.
"""

import asyncio
from datetime import UTC, datetime, timedelta

from hemdov.domain.metrics.analyzers import MetricsAnalyzer
from hemdov.infrastructure.persistence.metrics_repository import (
    SQLiteMetricsRepository,
)


async def main() -> None:
    """Query metrics and analyze trends."""
    print("=" * 60)
    print("Metrics Framework: Query & Analysis Example")
    print("=" * 60)

    # Initialize repository
    repo = SQLiteMetricsRepository("data/prompts.db")
    try:
        await repo.initialize()
    except Exception as e:
        print(f"\nFailed to initialize database: {e}")
        return

    try:
        # Get recent metrics (last 30 days)
        end = datetime.now(UTC)
        start = end - timedelta(days=30)

        print(f"\nQuerying metrics from {start.date()} to {end.date()}...")
        metrics = await repo.get_by_date_range(start, end, limit=100)

        if not metrics:
            print("\nNo metrics found in database.")
            print("   Run some prompt improvements first!")
            return

        print(f"\nFound {len(metrics)} metric records")

        # Initialize analyzer
        analyzer = MetricsAnalyzer()

        # Get summary statistics
        print("\n" + "=" * 60)
        print("SUMMARY STATISTICS")
        print("=" * 60)

        summary = analyzer.summarize(metrics)

        print(f"\nTotal Prompts: {summary['count']}")
        print(f"Average Quality:   {summary['quality']['mean']:.2%}")
        print(f"Average Performance: {summary['performance']['mean']:.2%}")
        print(f"Average Impact:    {summary['impact']['mean']:.2%}")

        print("\n--- Grade Distribution ---")
        for grade, count in sorted(summary['grade_distribution'].items()):
            bar = "█" * (count // max(1, max(summary['grade_distribution'].values()) // 20))
            print(f"{grade:2s}: {count:3d} {bar}")

        # Analyze trends
        print("\n" + "=" * 60)
        print("TREND ANALYSIS")
        print("=" * 60)

        trends = analyzer.analyze_trends(metrics)

        print(f"\nQuality Trend:    {trends.quality_trend.trend.upper()}")
        print(f"  Change:          {trends.quality_delta:+.2%}")

        print(f"\nPerformance Trend: {trends.performance_trend.trend.upper()}")
        print(f"  Change:          {trends.performance_delta:+.2%}")

        print(f"\nImpact Trend:     {trends.impact_trend.trend.upper()}")
        print(f"  Change:          {trends.impact_delta:+.2%}")

        if trends.recommendations:
            print("\n--- Recommendations ---")
            for i, rec in enumerate(trends.recommendations, 1):
                print(f"{i}. {rec}")
    finally:
        # Close repository
        await repo.close()

    print("\n" + "=" * 60)
    print("Analysis complete!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
