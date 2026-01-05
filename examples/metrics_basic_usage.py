#!/usr/bin/env python3
"""
Basic Metrics Framework Usage Example

Demonstrates how to calculate metrics for a prompt improvement.
"""

import asyncio
from datetime import datetime
from hemdov.domain.metrics.evaluators import (
    PromptMetricsCalculator,
    ImpactData,
)
from hemdov.domain.metrics.dimensions import (
    QualityMetrics,
    PerformanceMetrics,
    ImpactMetrics,
    PromptMetrics,
    FrameworkType,
)


async def main() -> None:
    """Calculate metrics for a sample prompt improvement."""
    print("=" * 60)
    print("Metrics Framework: Basic Usage Example")
    print("=" * 60)

    # Initialize calculator
    calculator = PromptMetricsCalculator()

    # Original idea from user
    original_idea = "Create a data analysis script"

    # Simulated DSPy improvement result
    result = {
        "improved_prompt": """# Role: Data Analyst

## Task
Write a Python script to analyze CSV data and generate visualizations.

## Context
You are working with sales data that needs to be analyzed for trends.

## Steps
1. Load the CSV file using pandas
2. Clean and preprocess the data
3. Generate summary statistics
4. Create visualizations with matplotlib
5. Export results to a report

## Guardrails
- Handle missing data gracefully
- Validate input data format
- Include error handling
""",
        "role": "Data Analyst",
        "directive": "Write a Python script",
        "framework": "chain-of-thought",
        "guardrails": ["Handle missing data", "Validate input"],
        "reasoning": None,
        "confidence": None,
        "latency_ms": 3247,
        "token_count": 847,
        "cost_usd": 0.00423,
    }

    # Impact data (user interactions)
    impact_data = ImpactData(
        copy_count=1,
        regeneration_count=0,
        feedback_score=5,  # 1-5 rating
        reuse_count=1,
    )

    # Calculate metrics
    print("\nCalculating metrics...")
    metrics = calculator.calculate(
        original_idea=original_idea,
        result=result,
        impact_data=impact_data,
    )

    # Display results
    print("\n" + "=" * 60)
    print("METRICS RESULTS")
    print("=" * 60)

    print(f"\nOverall Score: {metrics.overall_score:.2%}")
    print(f"Grade: {metrics.grade}")
    print(f"Acceptable: {metrics.is_acceptable}")

    print("\n--- Quality Dimensions ---")
    print(f"Coherence:     {metrics.quality.coherence_score:.2%}")
    print(f"Relevance:     {metrics.quality.relevance_score:.2%}")
    print(f"Completeness:  {metrics.quality.completeness_score:.2%}")
    print(f"Clarity:       {metrics.quality.clarity_score:.2%}")
    print(f"Composite:     {metrics.quality.composite_score:.2%}")
    if metrics.quality.guardrails_count > 0:
        print(f"Guardrails:    +{metrics.quality.guardrails_bonus:.2%} bonus")

    print("\n--- Performance Metrics ---")
    print(f"Latency:       {metrics.performance.latency_ms}ms")
    print(f"Tokens:        {metrics.performance.token_count}")
    print(f"Cost:          ${metrics.performance.estimated_cost_usd:.5f}")
    print(f"Performance:   {metrics.performance.performance_score:.2%}")

    print("\n--- Impact Metrics ---")
    print(f"Success Rate:  {metrics.impact.success_rate:.2%}")
    print(f"Satisfaction:  {metrics.impact.feedback_score}/5")
    print(f"Reuses:        {metrics.impact.reuse_count}")
    print(f"Impact:        {metrics.impact.impact_score:.2%}")

    print("\n" + "=" * 60)
    print("Metrics calculation complete!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
