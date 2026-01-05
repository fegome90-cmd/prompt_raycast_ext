# Metrics Framework Usage Examples

This directory contains practical examples demonstrating how to use the metrics framework.

## Examples

### 1. Basic Usage (`metrics_basic_usage.py`)

Demonstrates how to calculate metrics for a prompt improvement.

**Run:**
```bash
# Using uv (recommended)
uv run examples/metrics_basic_usage.py

# Or with Python directly
PYTHONPATH=. python examples/metrics_basic_usage.py
```

**What you'll learn:**
- How to initialize `PromptMetricsCalculator`
- How to calculate quality, performance, and impact metrics
- How to interpret metric scores and grades
- How impact data affects overall scoring

### 2. Query & Analysis (`metrics_query_analysis.py`)

Demonstrates how to query metrics from the database and analyze trends.

**Run:**
```bash
# Using uv (recommended)
uv run examples/metrics_query_analysis.py

# Or with Python directly
PYTHONPATH=. python examples/metrics_query_analysis.py
```

**What you'll learn:**
- How to query metrics from SQLite database
- How to use `MetricsAnalyzer` for summary statistics
- How to analyze trends over time
- How to generate recommendations from trends

### 3. A/B Testing (`metrics_ab_testing.py`)

Demonstrates how to compare two groups of prompts.

**Run:**
```bash
# Using uv (recommended)
uv run examples/metrics_ab_testing.py

# Or with Python directly
PYTHONPATH=. python examples/metrics_ab_testing.py
```

**What you'll learn:**
- How to split metrics into groups for comparison
- How to run A/B tests with `MetricsAnalyzer`
- How to interpret comparison results
- How to determine statistical significance

## Prerequisites

1. **Database with metrics**: Run the backend and make some prompt improvements first
2. **Python environment**: Install dependencies with `pip install -r requirements.txt`
3. **Database path**: Examples assume database at `data/prompts.db`

## Tips

- Start with `metrics_basic_usage.py` to understand the data model
- Use `metrics_query_analysis.py` to explore your existing metrics
- Run `metrics_ab_testing.py` to compare different models or approaches
- Check `docs/metrics-framework.md` for complete API reference

## Next Steps

- Integrate metrics calculation into your own workflow
- Query metrics to track prompt quality over time
- Run A/B tests to optimize prompts
- Explore the metrics API endpoints for real-time monitoring
