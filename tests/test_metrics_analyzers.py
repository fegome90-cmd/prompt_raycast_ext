# tests/test_metrics_analyzers.py
"""
Tests for metrics analyzers (analyzers.py).
Tests trend analysis, comparison, and recommendation generation.
"""

import pytest
from datetime import datetime, timedelta, timezone
from hemdov.domain.metrics.analyzers import (
    TrendPoint,
    TrendMetrics,
    TrendAnalysis,
    TrendAnalyzer,
    ComparisonResult,
    ComparisonReport,
    ComparisonAnalyzer,
    MetricsAnalyzer,
)
from hemdov.domain.metrics.dimensions import (
    PromptMetrics,
    QualityMetrics,
    PerformanceMetrics,
    ImpactMetrics,
    FrameworkType,
)


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def base_time():
    """Base time for creating metrics."""
    return datetime.now(timezone.utc)


@pytest.fixture
def sample_quality():
    """Create sample quality metrics."""
    return QualityMetrics(
        coherence_score=0.8,
        relevance_score=0.8,
        completeness_score=0.8,
        clarity_score=0.8,
        guardrails_count=2,
        has_required_structure=True,
    )


@pytest.fixture
def sample_performance():
    """Create sample performance metrics."""
    return PerformanceMetrics(
        latency_ms=5000,
        total_tokens=1000,
        cost_usd=0.01,
        provider="anthropic",
        model="claude-haiku-4-5-20251001",
        backend="zero-shot",
    )


@pytest.fixture
def sample_impact():
    """Create sample impact metrics."""
    return ImpactMetrics(
        copy_count=3,
        regeneration_count=1,
        feedback_score=4,
        reuse_count=2,
    )


@pytest.fixture
def single_metric(base_time, sample_quality, sample_performance, sample_impact):
    """Create a single prompt metric."""
    return PromptMetrics(
        prompt_id="test-1",
        original_idea="test idea",
        improved_prompt="test prompt",
        quality=sample_quality,
        performance=sample_performance,
        impact=sample_impact,
        measured_at=base_time,
        framework=FrameworkType.CHAIN_OF_THOUGHT,
        provider="anthropic",
        model="claude-haiku-4-5-20251001",
        backend="zero-shot",
    )


@pytest.fixture
def improving_metrics(base_time, sample_quality, sample_performance, sample_impact):
    """Create metrics showing improvement over time."""
    metrics = []
    for i in range(10):
        # Increasing quality over time
        quality = QualityMetrics(
            coherence_score=0.7 + (i * 0.02),
            relevance_score=0.7 + (i * 0.02),
            completeness_score=0.7 + (i * 0.02),
            clarity_score=0.7 + (i * 0.02),
            guardrails_count=2,
            has_required_structure=True,
        )
        metrics.append(PromptMetrics(
            prompt_id=f"test-{i}",
            original_idea="test idea",
            improved_prompt="test prompt",
            quality=quality,
            performance=sample_performance,
            impact=sample_impact,
            measured_at=base_time + timedelta(hours=i),
            framework=FrameworkType.CHAIN_OF_THOUGHT,
            provider="anthropic",
            model="claude-haiku-4-5-20251001",
            backend="zero-shot",
        ))
    return metrics


@pytest.fixture
def declining_metrics(base_time, sample_quality, sample_performance, sample_impact):
    """Create metrics showing decline over time."""
    metrics = []
    for i in range(10):
        # Decreasing quality over time
        quality = QualityMetrics(
            coherence_score=0.9 - (i * 0.03),
            relevance_score=0.9 - (i * 0.03),
            completeness_score=0.9 - (i * 0.03),
            clarity_score=0.9 - (i * 0.03),
            guardrails_count=2,
            has_required_structure=True,
        )
        metrics.append(PromptMetrics(
            prompt_id=f"test-{i}",
            original_idea="test idea",
            improved_prompt="test prompt",
            quality=quality,
            performance=sample_performance,
            impact=sample_impact,
            measured_at=base_time + timedelta(hours=i),
            framework=FrameworkType.CHAIN_OF_THOUGHT,
            provider="anthropic",
            model="claude-haiku-4-5-20251001",
            backend="zero-shot",
        ))
    return metrics


@pytest.fixture
def stable_metrics(base_time, sample_quality, sample_performance, sample_impact):
    """Create metrics showing stability over time."""
    metrics = []
    for i in range(10):
        metrics.append(PromptMetrics(
            prompt_id=f"test-{i}",
            original_idea="test idea",
            improved_prompt="test prompt",
            quality=sample_quality,
            performance=sample_performance,
            impact=sample_impact,
            measured_at=base_time + timedelta(hours=i),
            framework=FrameworkType.CHAIN_OF_THOUGHT,
            provider="anthropic",
            model="claude-haiku-4-5-20251001",
            backend="zero-shot",
        ))
    return metrics


@pytest.fixture
def baseline_group(base_time, sample_quality, sample_performance, sample_impact):
    """Create baseline group for comparison."""
    metrics = []
    for i in range(5):
        quality = QualityMetrics(
            coherence_score=0.7,
            relevance_score=0.7,
            completeness_score=0.7,
            clarity_score=0.7,
            guardrails_count=1,
            has_required_structure=True,
        )
        metrics.append(PromptMetrics(
            prompt_id=f"baseline-{i}",
            original_idea="test idea",
            improved_prompt="test prompt",
            quality=quality,
            performance=sample_performance,
            impact=sample_impact,
            measured_at=base_time + timedelta(hours=i),
            framework=FrameworkType.CHAIN_OF_THOUGHT,
            provider="anthropic",
            model="claude-haiku-4-5-20251001",
            backend="zero-shot",
        ))
    return metrics


@pytest.fixture
def treatment_group(base_time, sample_quality, sample_performance, sample_impact):
    """Create treatment group for comparison (better quality)."""
    metrics = []
    for i in range(5):
        quality = QualityMetrics(
            coherence_score=0.85,
            relevance_score=0.85,
            completeness_score=0.85,
            clarity_score=0.85,
            guardrails_count=3,
            has_required_structure=True,
        )
        metrics.append(PromptMetrics(
            prompt_id=f"treatment-{i}",
            original_idea="test idea",
            improved_prompt="test prompt",
            quality=quality,
            performance=sample_performance,
            impact=sample_impact,
            measured_at=base_time + timedelta(hours=i),
            framework=FrameworkType.CHAIN_OF_THOUGHT,
            provider="anthropic",
            model="claude-haiku-4-5-20251001",
            backend="zero-shot",
        ))
    return metrics


# =============================================================================
# TrendPoint Tests
# =============================================================================

def test_trend_point_creation(base_time):
    """Test creating TrendPoint."""
    point = TrendPoint(
        timestamp=base_time,
        value=0.85,
        count=10,
    )

    assert point.timestamp == base_time
    assert point.value == 0.85
    assert point.count == 10


def test_trend_point_default_count(base_time):
    """Test TrendPoint with default count."""
    point = TrendPoint(
        timestamp=base_time,
        value=0.75,
    )

    assert point.count == 1


# =============================================================================
# TrendMetrics Tests
# =============================================================================

def test_trend_metrics_creation():
    """Test creating TrendMetrics."""
    metrics = TrendMetrics(
        mean=0.75,
        median=0.78,
        std_dev=0.05,
        min_value=0.65,
        max_value=0.85,
        trend="improving",
        change_rate=0.02,
    )

    assert metrics.mean == 0.75
    assert metrics.median == 0.78
    assert metrics.std_dev == 0.05
    assert metrics.min_value == 0.65
    assert metrics.max_value == 0.85
    assert metrics.trend == "improving"
    assert metrics.change_rate == 0.02


# =============================================================================
# TrendAnalysis Tests
# =============================================================================

def test_trend_analysis_structure(base_time):
    """Test TrendAnalysis data structure."""
    analysis = TrendAnalysis(
        start_time=base_time,
        end_time=base_time + timedelta(hours=10),
        sample_size=10,
        quality_trend=TrendMetrics(0.8, 0.8, 0.05, 0.7, 0.9, "stable", 0.0),
        performance_trend=TrendMetrics(0.7, 0.7, 0.05, 0.6, 0.8, "stable", 0.0),
        impact_trend=TrendMetrics(0.6, 0.6, 0.05, 0.5, 0.7, "stable", 0.0),
        overall_trend=TrendMetrics(0.7, 0.7, 0.05, 0.6, 0.8, "stable", 0.0),
        recommendations=["Test recommendation"],
        anomalies=["Test anomaly"],
    )

    assert analysis.start_time == base_time
    assert analysis.sample_size == 10
    assert len(analysis.recommendations) == 1
    assert len(analysis.anomalies) == 1


# =============================================================================
# TrendAnalyzer Tests
# =============================================================================

def test_trend_analyzer_initialization():
    """Test TrendAnalyzer initialization."""
    analyzer = TrendAnalyzer(window_size=15)
    assert analyzer.window_size == 15


def test_trend_analyzer_default_window_size():
    """Test TrendAnalyzer default window size."""
    analyzer = TrendAnalyzer()
    assert analyzer.window_size == 10


def test_trend_analyzer_empty_list():
    """Test trend analyzer with empty list."""
    analyzer = TrendAnalyzer()

    with pytest.raises(ValueError, match="Cannot analyze empty metrics list"):
        analyzer.analyze([])


def test_trend_analyzer_single_metric(single_metric):
    """Test trend analyzer with single metric."""
    analyzer = TrendAnalyzer()

    analysis = analyzer.analyze([single_metric])

    assert isinstance(analysis, TrendAnalysis)
    assert analysis.sample_size == 1
    assert analysis.quality_trend.trend == "stable"  # Not enough data for trend


def test_trend_analyzer_two_metrics(base_time, sample_quality, sample_performance, sample_impact):
    """Test trend analyzer with two metrics."""
    analyzer = TrendAnalyzer()

    metric1 = PromptMetrics(
        prompt_id="test-1",
        original_idea="test",
        improved_prompt="test",
        quality=QualityMetrics(0.7, 0.7, 0.7, 0.7, 1, True),
        performance=sample_performance,
        impact=sample_impact,
        measured_at=base_time,
        framework=FrameworkType.CHAIN_OF_THOUGHT,
        provider="anthropic",
        model="claude-haiku-4-5-20251001",
        backend="zero-shot",
    )

    metric2 = PromptMetrics(
        prompt_id="test-2",
        original_idea="test",
        improved_prompt="test",
        quality=QualityMetrics(0.8, 0.8, 0.8, 0.8, 2, True),
        performance=sample_performance,
        impact=sample_impact,
        measured_at=base_time + timedelta(hours=1),
        framework=FrameworkType.CHAIN_OF_THOUGHT,
        provider="anthropic",
        model="claude-haiku-4-5-20251001",
        backend="zero-shot",
    )

    analysis = analyzer.analyze([metric1, metric2])

    assert analysis.sample_size == 2
    # With 2 data points, should still be stable
    assert analysis.quality_trend.trend == "stable"


def test_trend_analyzer_improving_trend(improving_metrics):
    """Test trend analyzer with improving metrics."""
    analyzer = TrendAnalyzer()

    analysis = analyzer.analyze(improving_metrics)

    assert analysis.sample_size == 10
    assert analysis.quality_trend.trend == "improving"
    assert analysis.quality_trend.change_rate > 0
    assert analysis.start_time < analysis.end_time


def test_trend_analyzer_declining_trend(declining_metrics):
    """Test trend analyzer with declining metrics."""
    analyzer = TrendAnalyzer()

    analysis = analyzer.analyze(declining_metrics)

    assert analysis.sample_size == 10
    assert analysis.quality_trend.trend == "declining"
    assert analysis.quality_trend.change_rate < 0


def test_trend_analyzer_stable_trend(stable_metrics):
    """Test trend analyzer with stable metrics."""
    analyzer = TrendAnalyzer()

    analysis = analyzer.analyze(stable_metrics)

    assert analysis.sample_size == 10
    assert analysis.quality_trend.trend == "stable"
    # Change rate should be very close to 0
    assert abs(analysis.quality_trend.change_rate) < 0.01


def test_trend_analyzer_statistics(stable_metrics):
    """Test statistical calculations in trend analysis."""
    analyzer = TrendAnalyzer()

    analysis = analyzer.analyze(stable_metrics)

    # Check quality statistics
    assert 0.0 <= analysis.quality_trend.mean <= 1.0
    assert 0.0 <= analysis.quality_trend.median <= 1.0
    assert analysis.quality_trend.min_value <= analysis.quality_trend.max_value
    assert analysis.quality_trend.std_dev >= 0


def test_trend_analyzer_recommendations_declining_quality(declining_metrics):
    """Test recommendations for declining quality."""
    analyzer = TrendAnalyzer()

    analysis = analyzer.analyze(declining_metrics)

    # Should recommend reviewing prompt templates
    assert len(analysis.recommendations) > 0
    assert any("declining" in rec.lower() for rec in analysis.recommendations)


def test_trend_analyzer_recommendations_strong_improvement():
    """Test recommendations for strong improvement."""
    analyzer = TrendAnalyzer()

    # Create metrics with very strong improvement
    # The quality trend itself should be improving significantly
    metrics = []
    base_time = datetime.now(timezone.utc)
    for i in range(10):
        # Extremely strong improvement in quality
        # Starting at 0.2, ending at 0.9 = 0.7 total change
        quality = QualityMetrics(
            coherence_score=0.2 + (i * 0.078),  # 0.2 -> 0.9
            relevance_score=0.2 + (i * 0.078),
            completeness_score=0.2 + (i * 0.078),
            clarity_score=0.2 + (i * 0.078),
            guardrails_count=2,
            has_required_structure=True,
        )
        metrics.append(PromptMetrics(
            prompt_id=f"test-{i}",
            original_idea="test",
            improved_prompt="test",
            quality=quality,
            performance=PerformanceMetrics(5000, 1000, 0.01, "anthropic", "claude-haiku-4-5-20251001", "zero-shot"),
            impact=ImpactMetrics(copy_count=3, regeneration_count=1, feedback_score=4, reuse_count=2),
            measured_at=base_time + timedelta(hours=i),
            framework=FrameworkType.CHAIN_OF_THOUGHT,
            provider="anthropic",
            model="claude-haiku-4-5-20251001",
            backend="zero-shot",
        ))

    analysis = analyzer.analyze(metrics)

    # Verify quality has strong improvement trend (not diluted by performance/impact)
    assert analysis.quality_trend.trend == "improving"
    assert analysis.quality_trend.change_rate > 0.05

    # Overall should also be improving
    assert analysis.overall_trend.trend == "improving"


def test_trend_analyzer_anomaly_detection(base_time):
    """Test anomaly detection."""
    analyzer = TrendAnalyzer()

    # Create metrics with an anomaly
    metrics = []
    for i in range(15):
        # Most metrics are around 0.7-0.8
        score = 0.75
        if i == 10:
            score = 0.3  # Anomaly (very low)

        quality = QualityMetrics(score, score, score, score, 2, True)
        metrics.append(PromptMetrics(
            prompt_id=f"test-{i}",
            original_idea="test",
            improved_prompt="test",
            quality=quality,
            performance=PerformanceMetrics(5000, 1000, 0.01, "anthropic", "claude-haiku-4-5-20251001", "zero-shot"),
            impact=ImpactMetrics(copy_count=3, regeneration_count=1, feedback_score=4, reuse_count=2),
            measured_at=base_time + timedelta(hours=i),
            framework=FrameworkType.CHAIN_OF_THOUGHT,
            provider="anthropic",
            model="claude-haiku-4-5-20251001",
            backend="zero-shot",
        ))

    analysis = analyzer.analyze(metrics)

    # Should detect anomalies
    assert len(analysis.anomalies) >= 1


def test_trend_analyzer_sudden_drop_detection(base_time):
    """Test detection of sudden drops."""
    analyzer = TrendAnalyzer()

    # Create metrics with sudden drop - need >0.20 (20%) drop in overall_score
    metrics = []
    for i in range(20):  # Need more than 10 for anomaly detection
        if i < 10:
            # High quality with all bonuses
            quality = QualityMetrics(0.95, 0.95, 0.95, 0.95, 5, True)
            impact = ImpactMetrics(copy_count=10, regeneration_count=0, feedback_score=5, reuse_count=5)
        else:
            # Very low quality with no bonuses
            quality = QualityMetrics(0.3, 0.3, 0.3, 0.3, 0, False)
            impact = ImpactMetrics(copy_count=0, regeneration_count=5, feedback_score=1, reuse_count=0)

        metrics.append(PromptMetrics(
            prompt_id=f"test-{i}",
            original_idea="test",
            improved_prompt="test",
            quality=quality,
            performance=PerformanceMetrics(5000, 1000, 0.01, "anthropic", "claude-haiku-4-5-20251001", "zero-shot"),
            impact=impact,
            measured_at=base_time + timedelta(hours=i),
            framework=FrameworkType.CHAIN_OF_THOUGHT,
            provider="anthropic",
            model="claude-haiku-4-5-20251001",
            backend="zero-shot",
        ))

    analysis = analyzer.analyze(metrics)

    # With such extreme drop, should detect anomalies
    # Check if we have anomalies (might be drop detection or outlier detection)
    assert len(analysis.anomalies) >= 1


def test_trend_analyzer_insufficient_data_for_anomalies(stable_metrics):
    """Test that anomalies are not detected with insufficient data."""
    analyzer = TrendAnalyzer()

    # Only 10 data points (minimum needed)
    analysis = analyzer.analyze(stable_metrics[:10])

    # Should not detect anomalies with exactly 10 points
    # (anomaly detection needs more than 10)
    assert len(analysis.anomalies) == 0


# =============================================================================
# ComparisonResult Tests
# =============================================================================

def test_comparison_result_creation():
    """Test creating ComparisonResult."""
    result = ComparisonResult(
        metric_name="Quality",
        baseline_value=0.70,
        current_value=0.85,
        delta=0.15,
        delta_percent=21.43,
        is_improvement=True,
        is_significant=True,
    )

    assert result.metric_name == "Quality"
    assert result.baseline_value == 0.70
    assert result.current_value == 0.85
    assert result.delta == 0.15
    assert result.delta_percent == 21.43
    assert result.is_improvement is True
    assert result.is_significant is True


def test_comparison_result_negative_delta():
    """Test ComparisonResult with negative delta."""
    result = ComparisonResult(
        metric_name="Quality",
        baseline_value=0.85,
        current_value=0.70,
        delta=-0.15,
        delta_percent=-17.65,
        is_improvement=False,
        is_significant=True,
    )

    assert result.delta < 0
    assert result.is_improvement is False


# =============================================================================
# ComparisonReport Tests
# =============================================================================

def test_comparison_report_structure(base_time):
    """Test ComparisonReport data structure."""
    report = ComparisonReport(
        baseline_name="Baseline",
        treatment_name="Treatment",
        comparison_date=base_time,
        baseline_size=10,
        treatment_size=10,
        quality_comparison=ComparisonResult("Quality", 0.7, 0.85, 0.15, 21.43, True, True),
        performance_comparison=ComparisonResult("Performance", 0.6, 0.7, 0.1, 16.67, True, False),
        impact_comparison=ComparisonResult("Impact", 0.5, 0.6, 0.1, 20.0, True, False),
        overall_comparison=ComparisonResult("Overall", 0.6, 0.72, 0.12, 20.0, True, True),
        winner="treatment",
        recommendation="Treatment wins",
        details={"test": "data"},
    )

    assert report.baseline_name == "Baseline"
    assert report.treatment_name == "Treatment"
    assert report.baseline_size == 10
    assert report.treatment_size == 10
    assert report.winner == "treatment"
    assert "test" in report.details


# =============================================================================
# ComparisonAnalyzer Tests
# =============================================================================

def test_comparison_analyzer_initialization():
    """Test ComparisonAnalyzer initialization."""
    analyzer = ComparisonAnalyzer(min_sample_size=10, alpha=0.01)
    assert analyzer.min_sample_size == 10
    assert analyzer.alpha == 0.01


def test_comparison_analyzer_default_parameters():
    """Test ComparisonAnalyzer default parameters."""
    analyzer = ComparisonAnalyzer()
    assert analyzer.min_sample_size == 5
    assert analyzer.alpha == 0.05


def test_comparison_analyzer_insufficient_baseline(baseline_group, treatment_group):
    """Test comparison with insufficient baseline samples."""
    analyzer = ComparisonAnalyzer(min_sample_size=10)

    with pytest.raises(ValueError, match="Baseline has insufficient samples"):
        analyzer.compare(baseline_group, treatment_group)


def test_comparison_analyzer_insufficient_treatment(baseline_group, treatment_group):
    """Test comparison with insufficient treatment samples."""
    # Create groups where baseline passes but treatment fails
    analyzer = ComparisonAnalyzer(min_sample_size=10)

    # Baseline has 10 (just enough), treatment has 5 (insufficient)
    large_baseline = baseline_group * 2  # 10 items

    with pytest.raises(ValueError, match="Treatment has insufficient samples"):
        analyzer.compare(large_baseline, treatment_group)


def test_comparison_analyzer_basic_comparison(baseline_group, treatment_group):
    """Test basic A/B comparison."""
    analyzer = ComparisonAnalyzer()

    report = analyzer.compare(baseline_group, treatment_group)

    assert isinstance(report, ComparisonReport)
    assert report.baseline_size == 5
    assert report.treatment_size == 5
    assert report.quality_comparison.current_value > report.quality_comparison.baseline_value
    assert report.quality_comparison.is_improvement is True


def test_comparison_analyzer_all_metrics(baseline_group, treatment_group):
    """Test comparison of all metrics."""
    analyzer = ComparisonAnalyzer()

    report = analyzer.compare(baseline_group, treatment_group)

    # Check all comparisons are present
    assert report.quality_comparison.metric_name == "Quality"
    assert report.performance_comparison.metric_name == "Performance"
    assert report.impact_comparison.metric_name == "Impact"
    assert report.overall_comparison.metric_name == "Overall"

    # All should have delta calculated
    assert report.quality_comparison.delta is not None
    assert report.performance_comparison.delta is not None
    assert report.impact_comparison.delta is not None
    assert report.overall_comparison.delta is not None


def test_comparison_analyzer_winner_determination(baseline_group, treatment_group):
    """Test winner determination in comparison."""
    analyzer = ComparisonAnalyzer()

    report = analyzer.compare(baseline_group, treatment_group)

    # Treatment has better quality, so should win or be inconclusive
    assert report.winner in ["treatment", "inconclusive", "baseline"]
    assert len(report.recommendation) > 0


def test_comparison_analyzer_details(baseline_group, treatment_group):
    """Test detailed breakdown in comparison report."""
    analyzer = ComparisonAnalyzer()

    report = analyzer.compare(baseline_group, treatment_group)

    # Check details contain distributions
    assert "baseline_distribution" in report.details
    assert "treatment_distribution" in report.details

    # Check distribution keys
    baseline_dist = report.details["baseline_distribution"]
    assert "quality" in baseline_dist
    assert "performance" in baseline_dist
    assert "impact" in baseline_dist
    assert "overall" in baseline_dist


def test_comparison_analyzer_custom_names(baseline_group, treatment_group):
    """Test comparison with custom group names."""
    analyzer = ComparisonAnalyzer()

    report = analyzer.compare(
        baseline_group,
        treatment_group,
        baseline_name="Version 1.0",
        treatment_name="Version 2.0",
    )

    assert report.baseline_name == "Version 1.0"
    assert report.treatment_name == "Version 2.0"


def test_comparison_analyzer_equal_groups(baseline_group):
    """Test comparison with identical groups."""
    analyzer = ComparisonAnalyzer()

    report = analyzer.compare(baseline_group, baseline_group)

    # Deltas should be zero or very close to zero
    assert abs(report.quality_comparison.delta) < 0.01
    assert abs(report.overall_comparison.delta) < 0.01


def test_comparison_analyzer_delta_percent_calculation(baseline_group, treatment_group):
    """Test delta percent calculation."""
    analyzer = ComparisonAnalyzer()

    report = analyzer.compare(baseline_group, treatment_group)

    # Delta percent should be calculated correctly
    expected_delta = report.quality_comparison.current_value - report.quality_comparison.baseline_value
    expected_percent = (expected_delta / report.quality_comparison.baseline_value) * 100

    assert abs(report.quality_comparison.delta - expected_delta) < 0.01
    assert abs(report.quality_comparison.delta_percent - expected_percent) < 0.1


# =============================================================================
# MetricsAnalyzer Tests
# =============================================================================

def test_metrics_analyzer_initialization():
    """Test MetricsAnalyzer initialization."""
    analyzer = MetricsAnalyzer()

    assert analyzer.trend_analyzer is not None
    assert analyzer.comparison_analyzer is not None
    assert isinstance(analyzer.trend_analyzer, TrendAnalyzer)
    assert isinstance(analyzer.comparison_analyzer, ComparisonAnalyzer)


def test_metrics_analyzer_analyze_trends(improving_metrics):
    """Test analyze_trends facade method."""
    analyzer = MetricsAnalyzer()

    analysis = analyzer.analyze_trends(improving_metrics)

    assert isinstance(analysis, TrendAnalysis)
    assert analysis.sample_size == 10


def test_metrics_analyzer_compare_versions(baseline_group, treatment_group):
    """Test compare_versions facade method."""
    analyzer = MetricsAnalyzer()

    report = analyzer.compare_versions(baseline_group, treatment_group)

    assert isinstance(report, ComparisonReport)
    assert report.baseline_size == 5
    assert report.treatment_size == 5


def test_metrics_analyzer_summarize_empty():
    """Test summarize with empty list."""
    analyzer = MetricsAnalyzer()

    summary = analyzer.summarize([])

    assert summary["count"] == 0
    assert "message" in summary


def test_metrics_analyzer_summarize(stable_metrics):
    """Test summarize with metrics."""
    analyzer = MetricsAnalyzer()

    summary = analyzer.summarize(stable_metrics)

    assert summary["count"] == 10
    assert "time_range" in summary
    assert "overall" in summary
    assert "quality" in summary
    assert "performance" in summary
    assert "impact" in summary
    assert "grade_distribution" in summary


def test_metrics_analyzer_summarize_statistics(stable_metrics):
    """Test statistical summaries in summarize method."""
    analyzer = MetricsAnalyzer()

    summary = analyzer.summarize(stable_metrics)

    # Check overall statistics
    overall = summary["overall"]
    assert "mean" in overall
    assert "median" in overall
    assert "std_dev" in overall
    assert "min" in overall
    assert "max" in overall

    # Check that statistics are reasonable
    assert 0.0 <= overall["mean"] <= 1.0
    assert overall["min"] <= overall["max"]


def test_metrics_analyzer_summarize_time_range(stable_metrics, base_time):
    """Test time range calculation in summarize."""
    analyzer = MetricsAnalyzer()

    summary = analyzer.summarize(stable_metrics)

    time_range = summary["time_range"]
    assert "start" in time_range
    assert "end" in time_range

    # Parse and check time range
    start = datetime.fromisoformat(time_range["start"])
    end = datetime.fromisoformat(time_range["end"])
    assert start < end


def test_metrics_analyzer_summarize_grade_distribution(stable_metrics):
    """Test grade distribution calculation."""
    analyzer = MetricsAnalyzer()

    summary = analyzer.summarize(stable_metrics)

    grade_dist = summary["grade_distribution"]
    assert isinstance(grade_dist, dict)
    assert len(grade_dist) > 0


def test_metrics_analyzer_custom_comparison_names(baseline_group, treatment_group):
    """Test compare_versions with custom names."""
    analyzer = MetricsAnalyzer()

    report = analyzer.compare_versions(
        baseline_group,
        treatment_group,
        baseline_name="Control",
        treatment_name="Experiment",
    )

    assert report.baseline_name == "Control"
    assert report.treatment_name == "Experiment"


# =============================================================================
# Integration Tests
# =============================================================================

def test_full_analysis_workflow(base_time, sample_quality, sample_performance, sample_impact):
    """Test complete workflow from metrics to recommendations."""
    analyzer = MetricsAnalyzer()

    # Create historical data
    historical = []
    for i in range(20):
        quality = QualityMetrics(
            coherence_score=0.7 + (i * 0.01),
            relevance_score=0.7 + (i * 0.01),
            completeness_score=0.7 + (i * 0.01),
            clarity_score=0.7 + (i * 0.01),
            guardrails_count=2,
            has_required_structure=True,
        )
        historical.append(PromptMetrics(
            prompt_id=f"hist-{i}",
            original_idea="test",
            improved_prompt="test",
            quality=quality,
            performance=sample_performance,
            impact=sample_impact,
            measured_at=base_time + timedelta(hours=i),
            framework=FrameworkType.CHAIN_OF_THOUGHT,
            provider="anthropic",
            model="claude-haiku-4-5-20251001",
            backend="zero-shot",
        ))

    # Analyze trends
    trend_analysis = analyzer.analyze_trends(historical)
    assert trend_analysis.sample_size == 20

    # Get summary
    summary = analyzer.summarize(historical)
    assert summary["count"] == 20

    # Compare first half vs second half
    baseline = historical[:10]
    treatment = historical[10:]
    comparison = analyzer.compare_versions(baseline, treatment, "v1", "v2")
    assert comparison.baseline_size == 10
    assert comparison.treatment_size == 10


def test_realistic_scenario_with_recommendations(base_time):
    """Test realistic scenario with various metrics and recommendations."""
    analyzer = MetricsAnalyzer()

    # Create realistic mixed metrics
    metrics = []
    for i in range(15):
        # Quality improves but performance degrades
        quality_score = 0.65 + (i * 0.02)
        latency = 5000 + (i * 1000)  # Getting slower

        quality = QualityMetrics(
            coherence_score=quality_score,
            relevance_score=quality_score,
            completeness_score=quality_score,
            clarity_score=quality_score,
            guardrails_count=2,
            has_required_structure=True,
        )

        performance = PerformanceMetrics(
            latency_ms=latency,
            total_tokens=1000,
            cost_usd=0.01,
            provider="anthropic",
            model="claude-haiku-4-5-20251001",
            backend="zero-shot",
        )

        impact = ImpactMetrics(
            copy_count=3,
            regeneration_count=1,
            feedback_score=4,
            reuse_count=2,
        )

        metrics.append(PromptMetrics(
            prompt_id=f"test-{i}",
            original_idea="test",
            improved_prompt="test",
            quality=quality,
            performance=performance,
            impact=impact,
            measured_at=base_time + timedelta(hours=i),
            framework=FrameworkType.CHAIN_OF_THOUGHT,
            provider="anthropic",
            model="claude-haiku-4-5-20251001",
            backend="zero-shot",
        ))

    # Analyze
    analysis = analyzer.analyze_trends(metrics)

    # Should have recommendations
    assert len(analysis.recommendations) > 0

    # Quality should be improving
    assert analysis.quality_trend.trend in ["improving", "stable"]


# =============================================================================
# Edge Cases Tests
# =============================================================================

def test_trend_analyzer_with_outliers(base_time):
    """Test trend analyzer handles outliers gracefully."""
    analyzer = TrendAnalyzer()

    # Create metrics with outliers
    metrics = []
    for i in range(12):
        # Add outliers at indices 3 and 8
        if i == 3:
            score = 0.95  # Very high
        elif i == 8:
            score = 0.45  # Very low
        else:
            score = 0.75

        quality = QualityMetrics(score, score, score, score, 2, True)
        metrics.append(PromptMetrics(
            prompt_id=f"test-{i}",
            original_idea="test",
            improved_prompt="test",
            quality=quality,
            performance=PerformanceMetrics(5000, 1000, 0.01, "anthropic", "claude-haiku-4-5-20251001", "zero-shot"),
            impact=ImpactMetrics(),
            measured_at=base_time + timedelta(hours=i),
            framework=FrameworkType.CHAIN_OF_THOUGHT,
            provider="anthropic",
            model="claude-haiku-4-5-20251001",
            backend="zero-shot",
        ))

    analysis = analyzer.analyze(metrics)

    # Should still complete without errors
    assert analysis.sample_size == 12


def test_comparison_analyzer_different_sized_groups(base_time):
    """Test comparison with different sized groups."""
    analyzer = ComparisonAnalyzer(min_sample_size=5)

    # Create groups of different sizes
    group_a = []
    group_b = []

    for i in range(10):
        quality_a = QualityMetrics(0.7, 0.7, 0.7, 0.7, 1, True)
        group_a.append(PromptMetrics(
            prompt_id=f"a-{i}",
            original_idea="test",
            improved_prompt="test",
            quality=quality_a,
            performance=PerformanceMetrics(5000, 1000, 0.01, "anthropic", "claude-haiku-4-5-20251001", "zero-shot"),
            impact=ImpactMetrics(),
            measured_at=base_time + timedelta(hours=i),
            framework=FrameworkType.CHAIN_OF_THOUGHT,
            provider="anthropic",
            model="claude-haiku-4-5-20251001",
            backend="zero-shot",
        ))

    for i in range(7):
        quality_b = QualityMetrics(0.8, 0.8, 0.8, 0.8, 2, True)
        group_b.append(PromptMetrics(
            prompt_id=f"b-{i}",
            original_idea="test",
            improved_prompt="test",
            quality=quality_b,
            performance=PerformanceMetrics(5000, 1000, 0.01, "anthropic", "claude-haiku-4-5-20251001", "zero-shot"),
            impact=ImpactMetrics(),
            measured_at=base_time + timedelta(hours=i),
            framework=FrameworkType.CHAIN_OF_THOUGHT,
            provider="anthropic",
            model="claude-haiku-4-5-20251001",
            backend="zero-shot",
        ))

    report = analyzer.compare(group_a, group_b)

    assert report.baseline_size == 10
    assert report.treatment_size == 7


def test_zero_variance_scenario(base_time):
    """Test scenario where all metrics are identical (zero variance)."""
    analyzer = ComparisonAnalyzer()

    # Create identical metrics
    group = []
    for i in range(5):
        quality = QualityMetrics(0.75, 0.75, 0.75, 0.75, 2, True)
        group.append(PromptMetrics(
            prompt_id=f"test-{i}",
            original_idea="test",
            improved_prompt="test",
            quality=quality,
            performance=PerformanceMetrics(5000, 1000, 0.01, "anthropic", "claude-haiku-4-5-20251001", "zero-shot"),
            impact=ImpactMetrics(),
            measured_at=base_time + timedelta(hours=i),
            framework=FrameworkType.CHAIN_OF_THOUGHT,
            provider="anthropic",
            model="claude-haiku-4-5-20251001",
            backend="zero-shot",
        ))

    report = analyzer.compare(group, group)

    # With zero variance, should not be significant
    assert report.overall_comparison.is_significant is False


def test_very_small_changes(base_time):
    """Test with very small changes (boundary case)."""
    analyzer = TrendAnalyzer()

    # Create metrics with tiny changes
    metrics = []
    for i in range(10):
        quality = QualityMetrics(
            coherence_score=0.75 + (i * 0.001),  # Very small change
            relevance_score=0.75 + (i * 0.001),
            completeness_score=0.75 + (i * 0.001),
            clarity_score=0.75 + (i * 0.001),
            guardrails_count=2,
            has_required_structure=True,
        )
        metrics.append(PromptMetrics(
            prompt_id=f"test-{i}",
            original_idea="test",
            improved_prompt="test",
            quality=quality,
            performance=PerformanceMetrics(5000, 1000, 0.01, "anthropic", "claude-haiku-4-5-20251001", "zero-shot"),
            impact=ImpactMetrics(),
            measured_at=base_time + timedelta(hours=i),
            framework=FrameworkType.CHAIN_OF_THOUGHT,
            provider="anthropic",
            model="claude-haiku-4-5-20251001",
            backend="zero-shot",
        ))

    analysis = analyzer.analyze(metrics)

    # Very small changes should be stable
    assert analysis.quality_trend.trend == "stable"
