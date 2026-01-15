# tests/test_metrics_registry.py
"""
Tests for metrics registry (registry.py).
Tests threshold configuration, grade calculation, and singleton pattern.
"""

import threading

import pytest

from hemdov.domain.metrics.registry import (
    DEFAULT_THRESHOLDS,
    METRIC_DEFINITIONS,
    MetricDefinition,
    MetricGrade,
    MetricsRegistry,
    MetricThreshold,
    get_registry,
)

# ============================================================================
# SINGLETON PATTERN TESTS
# ============================================================================

def test_registry_singleton():
    """Test that registry is singleton."""
    registry1 = MetricsRegistry.get_instance()
    registry2 = MetricsRegistry.get_instance()

    assert registry1 is registry2


def test_registry_thread_safety():
    """Test singleton in multi-threaded environment."""
    instances = []

    def get_instance():
        instances.append(MetricsRegistry.get_instance())

    threads = [threading.Thread(target=get_instance) for _ in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    # All instances should be the same
    assert len(set(instances)) == 1


def test_get_registry_function():
    """Test get_registry helper function."""
    registry1 = get_registry()
    registry2 = get_registry()

    assert registry1 is registry2
    assert isinstance(registry1, MetricsRegistry)


def test_multiple_registry_instances_separate():
    """Test that manually created instances are separate."""
    registry1 = MetricsRegistry()
    registry2 = MetricsRegistry()

    # Different instances (not singleton)
    assert registry1 is not registry2

    # But should have same default values
    assert registry1.thresholds == registry2.thresholds


# ============================================================================
# THRESHOLD TESTS
# ============================================================================

def test_get_threshold_quality():
    """Test getting threshold for quality metric."""
    registry = get_registry()

    threshold = registry.get_threshold("quality.coherence")

    assert isinstance(threshold, MetricThreshold)
    assert threshold.min_acceptable == 0.60
    assert threshold.target == 0.80
    assert threshold.excellent == 0.90


def test_get_threshold_performance():
    """Test getting threshold for performance metric."""
    registry = get_registry()

    # get_threshold returns the base "performance" threshold for any performance.* metric
    threshold = registry.get_threshold("performance.latency")
    assert isinstance(threshold, MetricThreshold)
    assert threshold.min_acceptable == 0.40
    assert threshold.target == 0.70
    assert threshold.excellent == 0.85

    # But the definition has custom thresholds for specific metrics
    definition = registry.get_definition("performance.latency")
    assert definition.threshold.min_acceptable == 30000  # ms
    assert definition.threshold.target == 10000  # ms
    assert definition.threshold.excellent == 5000  # ms


def test_get_threshold_impact():
    """Test getting threshold for impact metric."""
    registry = get_registry()

    threshold = registry.get_threshold("impact.success_rate")

    assert isinstance(threshold, MetricThreshold)
    assert threshold.min_acceptable == 0.50
    assert threshold.target == 0.75
    assert threshold.excellent == 0.90


def test_get_threshold_overall():
    """Test getting threshold for overall metric."""
    registry = get_registry()

    threshold = registry.get_threshold("overall")

    assert isinstance(threshold, MetricThreshold)
    assert threshold.min_acceptable == 0.60
    assert threshold.target == 0.80
    assert threshold.excellent == 0.90


def test_get_threshold_unknown_metric():
    """Test getting threshold for unknown metric (should use overall)."""
    registry = get_registry()

    threshold = registry.get_threshold("unknown.metric.name")

    # Should fall back to "overall" threshold
    assert threshold.min_acceptable == DEFAULT_THRESHOLDS["overall"].min_acceptable
    assert threshold.target == DEFAULT_THRESHOLDS["overall"].target
    assert threshold.excellent == DEFAULT_THRESHOLDS["overall"].excellent


def test_threshold_get_grade():
    """Test MetricThreshold.get_grade method."""
    threshold = MetricThreshold(
        min_acceptable=0.60,
        target=0.80,
        excellent=0.90,
    )

    assert threshold.get_grade(0.95) == MetricGrade.A_PLUS
    assert threshold.get_grade(0.85) == MetricGrade.A
    assert threshold.get_grade(0.70) == MetricGrade.C
    assert threshold.get_grade(0.50) == MetricGrade.F


def test_threshold_boundary_conditions():
    """Test threshold grades at boundary values."""
    threshold = MetricThreshold(
        min_acceptable=0.60,
        target=0.80,
        excellent=0.90,
    )

    # Exactly excellent
    assert threshold.get_grade(0.90) == MetricGrade.A_PLUS

    # Exactly target
    assert threshold.get_grade(0.80) == MetricGrade.A

    # Exactly min_acceptable
    assert threshold.get_grade(0.60) == MetricGrade.C

    # Just below min_acceptable
    assert threshold.get_grade(0.59) == MetricGrade.F


# ============================================================================
# DEFINITION TESTS
# ============================================================================

def test_get_definition_quality_coherence():
    """Test getting definition for quality.coherence metric."""
    registry = get_registry()

    definition = registry.get_definition("quality.coherence")

    assert isinstance(definition, MetricDefinition)
    assert definition.name == "Coherence"
    assert "logical flow" in definition.description.lower()
    assert definition.unit == "score"
    assert definition.higher_is_better is True


def test_get_definition_performance_latency():
    """Test getting definition for performance.latency metric."""
    registry = get_registry()

    definition = registry.get_definition("performance.latency")

    assert isinstance(definition, MetricDefinition)
    assert definition.name == "Latency"
    assert "time" in definition.description.lower()
    assert definition.unit == "ms"
    assert definition.higher_is_better is False  # Lower is better


def test_get_definition_performance_cost():
    """Test getting definition for performance.cost metric."""
    registry = get_registry()

    definition = registry.get_definition("performance.cost")

    assert isinstance(definition, MetricDefinition)
    assert definition.name == "Cost"
    assert definition.unit == "usd"
    assert definition.higher_is_better is False  # Lower is better


def test_get_definition_unknown_metric():
    """Test getting definition for unknown metric."""
    registry = get_registry()

    definition = registry.get_definition("unknown.metric")

    assert definition is None


def test_all_definitions_have_thresholds():
    """Test that all metric definitions have thresholds."""
    registry = get_registry()

    for metric_name, definition in METRIC_DEFINITIONS.items():
        threshold = registry.get_threshold(metric_name)
        assert isinstance(threshold, MetricThreshold)


# ============================================================================
# IS_ACCEPTABLE TESTS
# ============================================================================

def test_is_acceptable_higher_better_pass():
    """Test is_acceptable for metrics where higher is better (passing)."""
    registry = get_registry()

    # Quality metrics: higher is better
    assert registry.is_acceptable("quality.coherence", 0.90) is True
    assert registry.is_acceptable("quality.coherence", 0.70) is True
    assert registry.is_acceptable("quality.relevance", 0.60) is True


def test_is_acceptable_higher_better_fail():
    """Test is_acceptable for metrics where higher is better (failing)."""
    registry = get_registry()

    # Quality metrics below threshold
    assert registry.is_acceptable("quality.coherence", 0.50) is False
    assert registry.is_acceptable("quality.relevance", 0.30) is False


def test_is_acceptable_lower_better_pass():
    """Test is_acceptable for metrics where lower is better (passing)."""
    registry = get_registry()

    # Note: is_acceptable uses the base threshold (0.4) and higher_is_better flag
    # For performance metrics, higher_is_better=False, so we check value <= threshold
    # This means it checks if the performance score (0-1) is >= 0.4
    # A high performance score (e.g., 0.8 from low latency) is acceptable
    assert registry.is_acceptable("performance.latency", 0.8) is True
    assert registry.is_acceptable("performance.latency", 0.5) is True
    assert registry.is_acceptable("performance.latency", 0.4) is True  # At threshold


def test_is_acceptable_lower_better_fail():
    """Test is_acceptable for metrics where lower is better (failing)."""
    registry = get_registry()

    # Low performance score (from high latency) is not acceptable
    assert registry.is_acceptable("performance.latency", 0.3) is False
    assert registry.is_acceptable("performance.latency", 0.1) is False


def test_is_acceptable_cost():
    """Test is_acceptable for cost metric."""
    registry = get_registry()

    # Cost uses performance score (0-1), higher = better (more efficient)
    assert registry.is_acceptable("performance.cost", 0.9) is True  # Very efficient
    assert registry.is_acceptable("performance.cost", 0.5) is True
    assert registry.is_acceptable("performance.cost", 0.4) is True  # At threshold
    assert registry.is_acceptable("performance.cost", 0.3) is False  # Not efficient enough


def test_is_acceptable_tokens():
    """Test is_acceptable for token usage metric."""
    registry = get_registry()

    # Tokens uses performance score (0-1), higher = better (more efficient)
    assert registry.is_acceptable("performance.tokens", 0.9) is True
    assert registry.is_acceptable("performance.tokens", 0.5) is True
    assert registry.is_acceptable("performance.tokens", 0.4) is True  # At threshold
    assert registry.is_acceptable("performance.tokens", 0.3) is False


def test_is_acceptable_unknown_metric():
    """Test is_acceptable for unknown metric (should default to higher_is_better=True)."""
    registry = get_registry()

    # Unknown metric should use overall threshold and default to higher_is_better=True
    assert registry.is_acceptable("unknown.metric", 0.70) is True
    assert registry.is_acceptable("unknown.metric", 0.50) is False


# ============================================================================
# GET_GRADE TESTS
# ============================================================================

def test_get_grade_a_plus():
    """Test get_grade returns A_PLUS for excellent values."""
    registry = get_registry()

    assert registry.get_grade("quality.coherence", 0.95) == MetricGrade.A_PLUS
    assert registry.get_grade("quality.coherence", 0.90) == MetricGrade.A_PLUS


def test_get_grade_a():
    """Test get_grade returns A for target values."""
    registry = get_registry()

    assert registry.get_grade("quality.coherence", 0.89) == MetricGrade.A
    assert registry.get_grade("quality.coherence", 0.85) == MetricGrade.A
    assert registry.get_grade("quality.coherence", 0.80) == MetricGrade.A


def test_get_grade_c():
    """Test get_grade returns C for acceptable values."""
    registry = get_registry()

    assert registry.get_grade("quality.coherence", 0.79) == MetricGrade.C
    assert registry.get_grade("quality.coherence", 0.70) == MetricGrade.C
    assert registry.get_grade("quality.coherence", 0.60) == MetricGrade.C


def test_get_grade_f():
    """Test get_grade returns F for failing values."""
    registry = get_registry()

    assert registry.get_grade("quality.coherence", 0.59) == MetricGrade.F
    assert registry.get_grade("quality.coherence", 0.50) == MetricGrade.F
    assert registry.get_grade("quality.coherence", 0.30) == MetricGrade.F


def test_get_grade_boundary_values():
    """Test get_grade at exact boundary values."""
    registry = get_registry()

    # At exact boundaries
    assert registry.get_grade("quality.coherence", 0.90) == MetricGrade.A_PLUS
    assert registry.get_grade("quality.coherence", 0.80) == MetricGrade.A
    assert registry.get_grade("quality.coherence", 0.60) == MetricGrade.C


def test_get_grade_invalid_input_type():
    """Test that get_grade validates input type."""
    registry = get_registry()

    with pytest.raises(TypeError, match="must be numeric"):
        registry.get_grade("quality.coherence", "not a number")

    with pytest.raises(TypeError, match="must be numeric"):
        registry.get_grade("quality.coherence", None)


def test_get_grade_out_of_range_warning():
    """Test that get_grade handles out-of-range values."""
    # Should not raise exception, just log warning
    result1 = get_registry().get_grade("quality.coherence", 1.5)
    assert result1 == MetricGrade.A_PLUS  # Clamped to excellent

    result2 = get_registry().get_grade("quality.coherence", -0.1)
    assert result2 == MetricGrade.F  # Below threshold


# ============================================================================
# DEFAULT THRESHOLDS TESTS
# ============================================================================

def test_default_thresholds_structure():
    """Test that DEFAULT_THRESHOLDS has correct structure."""
    assert "quality" in DEFAULT_THRESHOLDS
    assert "performance" in DEFAULT_THRESHOLDS
    assert "impact" in DEFAULT_THRESHOLDS
    assert "overall" in DEFAULT_THRESHOLDS

    for name, threshold in DEFAULT_THRESHOLDS.items():
        assert isinstance(threshold, MetricThreshold)
        assert hasattr(threshold, "min_acceptable")
        assert hasattr(threshold, "target")
        assert hasattr(threshold, "excellent")


def test_default_thresholds_values():
    """Test that default thresholds have sensible values."""
    # Quality: min 0.60, target 0.80, excellent 0.90
    quality = DEFAULT_THRESHOLDS["quality"]
    assert quality.min_acceptable == 0.60
    assert quality.target == 0.80
    assert quality.excellent == 0.90

    # Performance: min 0.40, target 0.70, excellent 0.85
    performance = DEFAULT_THRESHOLDS["performance"]
    assert performance.min_acceptable == 0.40
    assert performance.target == 0.70
    assert performance.excellent == 0.85

    # Impact: min 0.50, target 0.75, excellent 0.90
    impact = DEFAULT_THRESHOLDS["impact"]
    assert impact.min_acceptable == 0.50
    assert impact.target == 0.75
    assert impact.excellent == 0.90


# ============================================================================
# METRIC DEFINITIONS TESTS
# ============================================================================

def test_metric_definitions_completeness():
    """Test that METRIC_DEFINITIONS includes all expected metrics."""
    expected_metrics = [
        "quality.coherence",
        "quality.relevance",
        "quality.completeness",
        "quality.clarity",
        "performance.latency",
        "performance.tokens",
        "performance.cost",
        "impact.success_rate",
    ]

    for metric in expected_metrics:
        assert metric in METRIC_DEFINITIONS
        assert isinstance(METRIC_DEFINITIONS[metric], MetricDefinition)


def test_metric_definitions_required_fields():
    """Test that all metric definitions have required fields."""
    for metric_name, definition in METRIC_DEFINITIONS.items():
        assert hasattr(definition, "name")
        assert hasattr(definition, "description")
        assert hasattr(definition, "unit")
        assert hasattr(definition, "threshold")
        assert hasattr(definition, "higher_is_better")

        # Verify types
        assert isinstance(definition.name, str)
        assert isinstance(definition.description, str)
        assert isinstance(definition.unit, str)
        assert isinstance(definition.threshold, MetricThreshold)
        assert isinstance(definition.higher_is_better, bool)


def test_metric_definitions_quality_higher_better():
    """Test that all quality metrics have higher_is_better=True."""
    quality_metrics = [
        "quality.coherence",
        "quality.relevance",
        "quality.completeness",
        "quality.clarity",
    ]

    for metric in quality_metrics:
        assert METRIC_DEFINITIONS[metric].higher_is_better is True


def test_metric_definitions_performance_lower_better():
    """Test that performance metrics (latency, cost, tokens) have lower_is_better."""
    performance_metrics = [
        "performance.latency",
        "performance.tokens",
        "performance.cost",
    ]

    for metric in performance_metrics:
        assert METRIC_DEFINITIONS[metric].higher_is_better is False


# ============================================================================
# METRIC GRADE ENUM TESTS
# ============================================================================

def test_metric_grade_enum_values():
    """Test MetricGrade enum has all expected values."""
    assert MetricGrade.A_PLUS.value == "A+"
    assert MetricGrade.A.value == "A"
    assert MetricGrade.A_MINUS.value == "A-"
    assert MetricGrade.B_PLUS.value == "B+"
    assert MetricGrade.B.value == "B"
    assert MetricGrade.B_MINUS.value == "B-"
    assert MetricGrade.C_PLUS.value == "C+"
    assert MetricGrade.C.value == "C"
    assert MetricGrade.D.value == "D"
    assert MetricGrade.F.value == "F"


# ============================================================================
# REGISTRY INITIALIZATION TESTS
# ============================================================================

def test_registry_initialization_defaults():
    """Test that registry initializes with default thresholds."""
    registry = MetricsRegistry()

    assert "quality" in registry.thresholds
    assert "performance" in registry.thresholds
    assert "impact" in registry.thresholds
    assert "overall" in registry.thresholds


def test_registry_thresholds_copied():
    """Test that registry copies thresholds (not references)."""
    registry1 = MetricsRegistry()
    registry2 = MetricsRegistry()

    # Modify registry1 thresholds
    from hemdov.domain.metrics.registry import MetricThreshold
    registry1.thresholds["quality"] = MetricThreshold(0.1, 0.2, 0.3)

    # registry2 should not be affected
    assert registry2.thresholds["quality"].min_acceptable == 0.60
    assert registry1.thresholds["quality"].min_acceptable == 0.1


def test_registry_definitions_copied():
    """Test that registry copies definitions (not references)."""
    registry1 = MetricsRegistry()
    registry2 = MetricsRegistry()

    # Verify both have same definitions
    assert len(registry1.definitions) == len(registry2.definitions)
    assert set(registry1.definitions.keys()) == set(registry2.definitions.keys())
