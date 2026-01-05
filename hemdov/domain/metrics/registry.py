# hemdov/domain/metrics/registry.py
"""
Metrics Registry - Configuration for metric thresholds and definitions.

Provides centralized configuration for metric evaluation thresholds,
alerting rules, and metric metadata.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional
from enum import Enum


class MetricGrade(Enum):
    """Letter grades for metric scores."""
    A_PLUS = "A+"
    A = "A"
    A_MINUS = "A-"
    B_PLUS = "B+"
    B = "B"
    B_MINUS = "B-"
    C_PLUS = "C+"
    C = "C"
    D = "D"
    F = "F"


@dataclass(frozen=True)
class MetricThreshold:
    """Threshold configuration for a metric."""
    min_acceptable: float
    target: float
    excellent: float

    def get_grade(self, value: float) -> MetricGrade:
        """Get letter grade for a metric value."""
        if value >= self.excellent:
            return MetricGrade.A_PLUS
        elif value >= self.target:
            return MetricGrade.A
        elif value >= self.min_acceptable:
            return MetricGrade.C
        else:
            return MetricGrade.F


# Default thresholds for each metric dimension
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
    "impact": MetricThreshold(
        min_acceptable=0.50,
        target=0.75,
        excellent=0.90,
    ),
    "overall": MetricThreshold(
        min_acceptable=0.60,
        target=0.80,
        excellent=0.90,
    ),
}


@dataclass(frozen=True)
class MetricDefinition:
    """Metadata about a metric."""
    name: str
    description: str
    unit: str  # "score", "ms", "tokens", "usd", etc.
    threshold: MetricThreshold
    higher_is_better: bool = True


METRIC_DEFINITIONS: Dict[str, MetricDefinition] = {
    "quality.coherence": MetricDefinition(
        name="Coherence",
        description="Logical flow and structure of the prompt",
        unit="score",
        threshold=DEFAULT_THRESHOLDS["quality"],
    ),
    "quality.relevance": MetricDefinition(
        name="Relevance",
        description="Alignment with original intent",
        unit="score",
        threshold=DEFAULT_THRESHOLDS["quality"],
    ),
    "quality.completeness": MetricDefinition(
        name="Completeness",
        description="Presence of required sections",
        unit="score",
        threshold=DEFAULT_THRESHOLDS["quality"],
    ),
    "quality.clarity": MetricDefinition(
        name="Clarity",
        description="Absence of ambiguity",
        unit="score",
        threshold=DEFAULT_THRESHOLDS["quality"],
    ),
    "performance.latency": MetricDefinition(
        name="Latency",
        description="Time to generate improved prompt",
        unit="ms",
        threshold=MetricThreshold(min_acceptable=30000, target=10000, excellent=5000),
        higher_is_better=False,  # Lower is better
    ),
    "performance.tokens": MetricDefinition(
        name="Token Usage",
        description="Total tokens consumed",
        unit="tokens",
        threshold=MetricThreshold(min_acceptable=5000, target=2000, excellent=1000),
        higher_is_better=False,
    ),
    "performance.cost": MetricDefinition(
        name="Cost",
        description="Estimated API cost in USD",
        unit="usd",
        threshold=MetricThreshold(min_acceptable=0.10, target=0.03, excellent=0.01),
        higher_is_better=False,
    ),
    "impact.success_rate": MetricDefinition(
        name="Success Rate",
        description="First-attempt acceptance rate",
        unit="score",
        threshold=DEFAULT_THRESHOLDS["impact"],
    ),
}


class MetricsRegistry:
    """
    Registry for metric configuration and metadata.

    Provides centralized access to thresholds, definitions, and
    evaluation rules for all metrics.
    """

    _instance: Optional["MetricsRegistry"] = None

    def __init__(self):
        """Initialize registry with defaults."""
        self.thresholds = DEFAULT_THRESHOLDS.copy()
        self.definitions = METRIC_DEFINITIONS.copy()

    @classmethod
    def get_instance(cls) -> "MetricsRegistry":
        """Get singleton instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def get_threshold(self, metric_name: str) -> MetricThreshold:
        """Get threshold configuration for a metric."""
        # Handle nested names like "quality.coherence"
        base_metric = metric_name.split(".")[0]
        return self.thresholds.get(base_metric, DEFAULT_THRESHOLDS["overall"])

    def get_definition(self, metric_name: str) -> Optional[MetricDefinition]:
        """Get metadata for a metric."""
        return self.definitions.get(metric_name)

    def is_acceptable(self, metric_name: str, value: float) -> bool:
        """Check if metric value meets minimum threshold."""
        threshold = self.get_threshold(metric_name)
        if self.get_definition(metric_name):
            higher_is_better = self.get_definition(metric_name).higher_is_better
        else:
            higher_is_better = True

        if higher_is_better:
            return value >= threshold.min_acceptable
        else:
            return value <= threshold.min_acceptable

    def get_grade(self, metric_name: str, value: float) -> MetricGrade:
        """Get letter grade for a metric value."""
        threshold = self.get_threshold(metric_name)
        return threshold.get_grade(value)


# Singleton accessor
def get_registry() -> MetricsRegistry:
    """Get the metrics registry singleton."""
    return MetricsRegistry.get_instance()
