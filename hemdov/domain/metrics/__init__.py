# hemdov/domain/metrics/__init__.py
"""
Prompt Metrics Framework

Multidimensional metrics system for evaluating prompt quality, performance,
impact, and improvement over time.

Core Dimensions:
- Quality: Coherence, Relevance, Completeness, Clarity
- Performance: Latency, Tokens, Cost
- Impact: Success Rate, Satisfaction, Reuse
- Improvement: Delta between versions, Convergence speed
"""

from .analyzers import (
    ComparisonReport,
    MetricsAnalyzer,
    TrendAnalysis,
)
from .dimensions import (
    ImpactMetrics,
    ImprovementMetrics,
    PerformanceMetrics,
    PromptMetrics,
    QualityMetrics,
)
from .evaluators import (
    PromptMetricsCalculator,
    get_calculator,
)
from .registry import (
    MetricDefinition,
    MetricGrade,
    MetricsRegistry,
    MetricThreshold,
    get_registry,
)

__all__ = [
    # Evaluators
    "PromptMetricsCalculator",
    "get_calculator",
    # Dimensions
    "QualityMetrics",
    "PerformanceMetrics",
    "ImpactMetrics",
    "ImprovementMetrics",
    "PromptMetrics",
    # Analyzers
    "MetricsAnalyzer",
    "TrendAnalysis",
    "ComparisonReport",
    # Registry
    "MetricsRegistry",
    "MetricDefinition",
    "MetricThreshold",
    "get_registry",
    "MetricGrade",
]
