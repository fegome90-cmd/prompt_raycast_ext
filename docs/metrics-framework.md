# Prompt Metrics Framework

> Multi-dimensional metrics system for evaluating prompt quality, performance, and impact over time.

## Overview

The metrics framework provides comprehensive tracking and analysis of prompt improvements across four dimensions:

- **Quality**: Coherence, relevance, completeness, clarity
- **Performance**: Latency, token usage, cost
- **Impact**: Success rate, user satisfaction, reuse
- **Improvement**: Delta between versions, convergence speed

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                    API Layer                        │
│  /api/v1/improve-prompt → metrics calculated       │
│  /api/v1/metrics/* → query & analysis              │
└────────────────────┬────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────┐
│                   Domain Layer                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────┐ │
│  │  Evaluators  │  │   Analyzers  │  │ Registry │ │
│  └──────────────┘  └──────────────┘  └──────────┘ │
└────────────────────┬────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────┐
│              Infrastructure Layer                   │
│  ┌──────────────────────────────────────────────┐ │
│  │   SQLiteMetricsRepository                   │ │
│  └──────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────┘
```

## Data Flow

1. **Prompt Improvement** → DSPy module generates improved prompt
2. **Metrics Calculation** → PromptMetricsCalculator computes all dimensions
3. **Storage** → SQLiteMetricsRepository persists metrics
4. **Analysis** → MetricsAnalyzer provides trends and comparisons

## API Reference

### GET /api/v1/metrics/summary

Get overall metrics summary.

**Response:**
```json
{
  "total_prompts": 150,
  "average_quality": 0.834,
  "average_performance": 0.767,
  "average_impact": 0.812,
  "grade_distribution": {
    "A+": 45,
    "A": 20,
    "A-": 18,
    "B+": 15,
    "B": 12,
    "B-": 10,
    "C+": 8,
    "C": 5,
    "D": 2
  }
}
```

**Example:**
```bash
curl http://localhost:8000/api/v1/metrics/summary
```

### GET /api/v1/metrics/trends

Analyze metric trends over time.

**Query Parameters:**
- `days` (int, optional): Number of days to analyze (1-90, default: 7)

**Response:**
```json
{
  "period_start": "2026-01-01T00:00:00",
  "period_end": "2026-01-08T00:00:00",
  "metrics_count": 42,
  "quality_trend": "improving",
  "performance_trend": "stable",
  "impact_trend": "improving",
  "quality_change": 0.056,
  "performance_change": 0.012,
  "impact_change": 0.034,
  "recommendations": [
    "Quality has improved by 5.6% over the last 7 days",
    "Consider optimizing prompts for lower latency"
  ]
}
```

**Trend Values:** Possible values are `improving`, `declining`, `stable`, or `insufficient_data` (when fewer than 3 data points are available).

**Example:**
```bash
curl "http://localhost:8000/api/v1/metrics/trends?days=30"
```

### POST /api/v1/metrics/compare

Compare metrics between two groups (A/B testing).

**Query Parameters:**
- `group_a` (str, required): Filter for group A (e.g., `model:claude-haiku-4-5-20251001`)
- `group_b` (str, required): Filter for group B (e.g., `model:claude-sonnet-4-5-20251001`)

**Supported Fields:** `model`, `provider`, `backend`, `framework`

**Response:**
```json
{
  "group_a": {
    "filter": "model:claude-haiku-4-5-20251001",
    "count": 75,
    "avg_quality": 0.823,
    "avg_performance": 0.789,
    "avg_impact": 0.801
  },
  "group_b": {
    "filter": "model:claude-sonnet-4-5-20251001",
    "count": 75,
    "avg_quality": 0.867,
    "avg_performance": 0.812,
    "avg_impact": 0.834
  },
  "comparison": {
    "quality_delta": -0.044,
    "performance_delta": -0.023,
    "impact_delta": -0.033,
    "winner": "group_b",
    "significance": "not_calculated"
  },
  "recommendation": "✅ Group B wins: +5.3% overall improvement"
}
```

**Note:** The `significance` field is currently hardcoded as `"not_calculated"` and will be implemented in a future update (statistical significance testing via t-test).

**Example:**
```bash
curl "http://localhost:8000/api/v1/metrics/compare?group_a=model:claude-haiku-4-5-20251001&group_b=model:claude-sonnet-4-5-20251001"
```

## Domain Model

### PromptMetrics

The core data structure containing all metric dimensions.

```python
from hemdov.domain.metrics.dimensions import PromptMetrics

metrics = PromptMetrics(
    prompt_id="unique-id",
    original_idea="Create a data analysis script",
    improved_prompt="# Role: Data Analyst\\n...",
    quality=QualityMetrics(...),
    performance=PerformanceMetrics(...),
    impact=ImpactMetrics(...),
    measured_at=datetime.utcnow(),
    framework="chain-of-thought",
    provider="anthropic",
    model="claude-haiku-4-5-20251001",
    backend="zero-shot",
)
```

**Properties:**
- `overall_score`: Weighted average (quality 50%, performance 25%, impact 25%)
- `grade`: Letter grade (A+, A, B, C, D, F)
- `is_acceptable`: Boolean indicating if minimum thresholds met

### QualityMetrics

Evaluates prompt structure and content quality.

**Dimensions:**
- `coherence_score` (0-1): Logical flow and structure
- `relevance_score` (0-1): Alignment with original intent
- `completeness_score` (0-1): Presence of required sections
- `clarity_score` (0-1): Absence of ambiguity
- `composite_score`: Average of all dimensions (+bonuses)

**Bonuses:**
- Guardrails bonus: +15% max (for safety guardrails)
- Structure bonus: +10% (for well-structured prompts)

### PerformanceMetrics

Evaluates efficiency metrics.

**Dimensions:**
- `latency_ms`: Time to generate improved prompt
- `token_count`: Total tokens consumed
- `estimated_cost_usd`: Estimated API cost
- `performance_score`: Normalized score (0-1)

### ImpactMetrics

Evaluates user-facing impact.

**Dimensions:**
- `copy_count`: Number of times prompt was copied to clipboard
- `regeneration_count`: Number of times prompt was regenerated
- `feedback_score`: User feedback rating (1-5)
- `reuse_count`: Number of times prompt was reused
- `success_rate`: First-attempt acceptance rate (0-1, calculated)
- `impact_score`: Weighted average (0-1, calculated)

## Grade Calculation

| Grade | Range | Description |
|-------|-------|-------------|
| A+ | ≥0.90 | Excellent |
| A | ≥0.85 | Very good |
| A- | ≥0.80 | Great |
| B+ | ≥0.75 | Good plus |
| B | ≥0.70 | Good |
| B- | ≥0.65 | Satisfactory plus |
| C+ | ≥0.60 | Satisfactory |
| C | ≥0.50 | Acceptable |
| D | <0.50 | Below average |

Grades are calculated separately for each dimension based on threshold configuration in `MetricsRegistry`.

## Threshold Configuration

Default thresholds can be customized in `hemdov/domain/metrics/registry.py`:

```python
DEFAULT_THRESHOLDS = {
    "quality": MetricThreshold(
        min_acceptable=0.60,  # C grade
        target=0.80,          # B grade
        excellent=0.90,       # A grade
    ),
    "performance": MetricThreshold(
        min_acceptable=0.40,
        target=0.70,
        excellent=0.85,
    ),
    # ...
}
```

## Programmatic Usage

### Calculating Metrics

```python
from hemdov.domain.metrics.evaluators import PromptMetricsCalculator, ImpactData

calculator = PromptMetricsCalculator()

metrics = calculator.calculate(
    original_idea="Create a data analysis script",
    result={
        "improved_prompt": "# Role: Data Analyst\\n...",
        "role": "Data Analyst",
        "framework": "chain-of-thought",
        "latency_ms": 3000,
        # ...
    },
    impact_data=ImpactData(),
)

print(f"Overall score: {metrics.overall_score:.2f}")
print(f"Grade: {metrics.grade}")
```

### Querying Metrics from Database

```python
from hemdov.infrastructure.persistence.metrics_repository import SQLiteMetricsRepository

repo = SQLiteMetricsRepository("data/prompts.db")
await repo.initialize()

# Get all metrics
all_metrics = await repo.get_all(limit=100)

# Get by ID
specific = await repo.get_by_id("prompt-id")

# Get by date range
from datetime import datetime, timedelta
end = datetime.utcnow()
start = end - timedelta(days=7)
metrics = await repo.get_by_date_range(start, end, limit=100)
```

### Trend Analysis

```python
from hemdov.domain.metrics.analyzers import MetricsAnalyzer

analyzer = MetricsAnalyzer()

# Analyze trends
trends = analyzer.analyze_trends(metrics)
print(f"Quality trend: {trends.quality_trend.trend}")
print(f"Change: {trends.quality_delta:+.2%}")

# Get recommendations
for rec in trends.recommendations:
    print(f"- {rec}")
```

### A/B Testing

```python
from hemdov.domain.metrics.analyzers import MetricsAnalyzer

analyzer = MetricsAnalyzer()

# Compare two groups
comparison = analyzer.compare_versions(
    baseline=group_a_metrics,
    treatment=group_b_metrics,
    baseline_name="Haiku 4.5",
    treatment_name="Sonnet 4.5"
)

print(f"Winner: {comparison.winner}")
print(f"Improvement: {comparison.quality_delta:+.2%}")
print(f"Significance: {comparison.statistical_significance}")
```

## Testing

Run the test suite:

```bash
# All metrics tests
pytest tests/test_metrics*.py -v

# With coverage
pytest tests/test_metrics*.py --cov=hemdov/domain/metrics --cov-report=html

# Specific module
pytest tests/test_metrics_analyzers.py -v
```

## Troubleshooting

### Metrics not being calculated

Check that metrics calculation is enabled in the API:

```python
# In api/prompt_improver_api.py
metrics = _metrics_calculator.calculate_from_history(...)
```

### Empty metrics in database

Verify that:
1. SQLite is enabled (`SQLITE_ENABLED=true` in `.env`)
2. Database path is correct (`SQLITE_DB_PATH` in `.env`)
3. No errors in backend logs

### Low scores

Review the scoring thresholds in `hemdov/domain/metrics/registry.py` and adjust if needed.

## References

- **Domain Layer**: `hemdov/domain/metrics/`
- **Repository**: `hemdov/infrastructure/persistence/metrics_repository.py`
- **API Endpoints**: `api/metrics_api.py`
- **Tests**: `tests/test_metrics_*.py`
