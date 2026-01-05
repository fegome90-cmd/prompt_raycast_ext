# hemdov/domain/metrics/analyzers.py
"""
Metrics Analyzers - Analyze metrics for insights and trends.

Provides tools for:
- Trend analysis over time
- A/B testing comparison
- Performance regression detection
- Improvement recommendations
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from collections import defaultdict
import statistics

from .dimensions import (
    PromptMetrics,
    QualityMetrics,
    PerformanceMetrics,
    ImpactMetrics,
    ImprovementMetrics,
)


logger = logging.getLogger(__name__)


# ============================================================================
# TREND ANALYSIS
# ============================================================================

@dataclass
class TrendPoint:
    """Single data point in a trend."""
    timestamp: datetime
    value: float
    count: int = 1


@dataclass
class TrendMetrics:
    """Statistical summary of a trend."""
    mean: float
    median: float
    std_dev: float
    min_value: float
    max_value: float
    trend: str  # "improving", "stable", "declining"
    change_rate: float  # Change per time period


@dataclass
class TrendAnalysis:
    """
    Analysis of metrics over time.

    Identifies patterns, trends, and anomalies in metric data.
    """

    # Time period analyzed
    start_time: datetime
    end_time: datetime

    # Number of data points
    sample_size: int

    # Quality trends
    quality_trend: TrendMetrics

    # Performance trends
    performance_trend: TrendMetrics

    # Impact trends
    impact_trend: TrendMetrics

    # Overall trend
    overall_trend: TrendMetrics

    # Recommendations
    recommendations: List[str] = field(default_factory=list)

    # Anomalies detected
    anomalies: List[str] = field(default_factory=list)


class TrendAnalyzer:
    """
    Analyzes metric trends over time.

    Detects:
    - Improving/stable/declining trends
    - Statistical anomalies
    - Performance regression
    """

    def __init__(self, window_size: int = 10):
        """
        Initialize analyzer.

        Args:
            window_size: Number of data points for moving average
        """
        self.window_size = window_size

    def analyze(
        self,
        metrics: List[PromptMetrics],
    ) -> TrendAnalysis:
        """
        Analyze trends in metrics data.

        Args:
            metrics: List of prompt metrics sorted by time

        Returns:
            TrendAnalysis with insights
        """
        if not metrics:
            raise ValueError("Cannot analyze empty metrics list")

        # Extract time series
        times = [m.measured_at for m in metrics]
        start_time = min(times)
        end_time = max(times)

        # Extract values
        quality_values = [m.quality.composite_score for m in metrics]
        performance_values = [m.performance.performance_score for m in metrics]
        impact_values = [m.impact.impact_score for m in metrics]
        overall_values = [m.overall_score for m in metrics]

        # Calculate trend metrics
        quality_trend = self._calculate_trend_metrics(quality_values)
        performance_trend = self._calculate_trend_metrics(performance_values)
        impact_trend = self._calculate_trend_metrics(impact_values)
        overall_trend = self._calculate_trend_metrics(overall_values)

        # Generate recommendations
        recommendations = self._generate_recommendations(
            quality_trend, performance_trend, impact_trend, overall_trend
        )

        # Detect anomalies
        anomalies = self._detect_anomalies(metrics)

        return TrendAnalysis(
            start_time=start_time,
            end_time=end_time,
            sample_size=len(metrics),
            quality_trend=quality_trend,
            performance_trend=performance_trend,
            impact_trend=impact_trend,
            overall_trend=overall_trend,
            recommendations=recommendations,
            anomalies=anomalies,
        )

    def _calculate_trend_metrics(self, values: List[float]) -> TrendMetrics:
        """Calculate statistical summary and trend direction."""
        if not values:
            return TrendMetrics(0, 0, 0, 0, 0, "stable", 0)

        mean = statistics.mean(values)
        median = statistics.median(values)
        std_dev = statistics.stdev(values) if len(values) > 1 else 0
        min_value = min(values)
        max_value = max(values)

        # Calculate trend direction using linear regression on last N points
        if len(values) >= 3:
            recent = values[-min(len(values), self.window_size):]
            # Simple slope: (last - first) / (n - 1)
            change_rate = (recent[-1] - recent[0]) / (len(recent) - 1) if len(recent) > 1 else 0

            # Determine trend
            if change_rate > 0.01:
                trend = "improving"
            elif change_rate < -0.01:
                trend = "declining"
            else:
                trend = "stable"
        else:
            change_rate = 0
            trend = "stable"

        return TrendMetrics(
            mean=mean,
            median=median,
            std_dev=std_dev,
            min_value=min_value,
            max_value=max_value,
            trend=trend,
            change_rate=change_rate,
        )

    def _generate_recommendations(
        self,
        quality_trend: TrendMetrics,
        performance_trend: TrendMetrics,
        impact_trend: TrendMetrics,
        overall_trend: TrendMetrics,
    ) -> List[str]:
        """Generate actionable recommendations from trend analysis."""
        recommendations = []

        # Quality recommendations
        if quality_trend.trend == "declining":
            recommendations.append(
                "⚠️ Quality declining: Review prompt templates andFewShot examples"
            )
        elif quality_trend.mean < 0.70:
            recommendations.append(
                "📉 Quality below target (C grade): Consider improving prompt structure"
            )

        # Performance recommendations
        if performance_trend.trend == "declining":
            recommendations.append(
                "⚠️ Performance declining: Check API latency and token usage"
            )
        elif performance_trend.mean < 0.50:
            recommendations.append(
                "📉 Performance below target: Consider faster model or optimization"
            )

        # Impact recommendations
        if impact_trend.trend == "declining":
            recommendations.append(
                "⚠️ User impact declining: Gather user feedback to identify issues"
            )
        elif impact_trend.mean < 0.50:
            recommendations.append(
                "📉 User satisfaction low: Review prompt quality and relevance"
            )

        # Overall recommendations
        if overall_trend.trend == "improving" and overall_trend.change_rate > 0.05:
            recommendations.append(
                "✅ Strong improvement: Document successful changes for replication"
            )

        return recommendations

    def _detect_anomalies(self, metrics: List[PromptMetrics]) -> List[str]:
        """Detect statistical anomalies in metrics."""
        anomalies = []

        if len(metrics) < 10:
            return anomalies  # Need sufficient data

        # Check for outliers in overall score
        overall_scores = [m.overall_score for m in metrics]
        mean = statistics.mean(overall_scores)
        std_dev = statistics.stdev(overall_scores)

        # Flag anything beyond 2 standard deviations
        for i, m in enumerate(metrics):
            if abs(m.overall_score - mean) > 2 * std_dev:
                direction = "high" if m.overall_score > mean else "low"
                anomalies.append(
                    f"Anomaly at index {i}: Overall score {direction} "
                    f"({m.overall_score:.2f} vs mean {mean:.2f})"
                )

        # Check for sudden drops
        for i in range(1, len(metrics)):
            prev_score = metrics[i - 1].overall_score
            curr_score = metrics[i].overall_score
            drop = prev_score - curr_score

            if drop > 0.20:  # 20%+ drop
                anomalies.append(
                    f"Sudden drop at index {i}: Score fell {drop:.1%} "
                    f"({prev_score:.2f} → {curr_score:.2f})"
                )

        return anomalies


# ============================================================================
# COMPARISON REPORT
# ============================================================================

@dataclass
class ComparisonResult:
    """Result of comparing two metric sets."""
    metric_name: str
    baseline_value: float
    current_value: float
    delta: float
    delta_percent: float
    is_improvement: bool
    is_significant: bool  # Statistically significant change


@dataclass
class ComparisonReport:
    """
    Report comparing two sets of metrics (A/B testing).

    Compares baseline vs treatment across all dimensions.
    """

    # Comparison metadata
    baseline_name: str
    treatment_name: str
    comparison_date: datetime

    # Sample sizes
    baseline_size: int
    treatment_size: int

    # Comparison results
    quality_comparison: ComparisonResult
    performance_comparison: ComparisonResult
    impact_comparison: ComparisonResult
    overall_comparison: ComparisonResult

    # Statistical significance
    confidence_level: float = 0.95

    # Recommendations
    winner: str = ""  # "baseline", "treatment", or "inconclusive"
    recommendation: str = ""

    # Detailed breakdown
    details: Dict[str, Any] = field(default_factory=dict)


class ComparisonAnalyzer:
    """
    Performs A/B testing analysis between metric sets.

    Determines:
    - Which version performs better
    - Statistical significance of differences
    - Actionable recommendations
    """

    def __init__(self, min_sample_size: int = 5, alpha: float = 0.05):
        """
        Initialize analyzer.

        Args:
            min_sample_size: Minimum samples for comparison
            alpha: Significance level (default 0.05 for 95% confidence)
        """
        self.min_sample_size = min_sample_size
        self.alpha = alpha

    def compare(
        self,
        baseline_metrics: List[PromptMetrics],
        treatment_metrics: List[PromptMetrics],
        baseline_name: str = "Baseline",
        treatment_name: str = "Treatment",
    ) -> ComparisonReport:
        """
        Compare baseline vs treatment metrics.

        Args:
            baseline_metrics: Metrics from baseline version
            treatment_metrics: Metrics from treatment version
            baseline_name: Name for baseline
            treatment_name: Name for treatment

        Returns:
            ComparisonReport with analysis
        """
        if len(baseline_metrics) < self.min_sample_size:
            raise ValueError(f"Baseline has insufficient samples ({len(baseline_metrics)} < {self.min_sample_size})")

        if len(treatment_metrics) < self.min_sample_size:
            raise ValueError(f"Treatment has insufficient samples ({len(treatment_metrics)} < {self.min_sample_size})")

        # Calculate averages
        baseline_quality = statistics.mean([m.quality.composite_score for m in baseline_metrics])
        treatment_quality = statistics.mean([m.quality.composite_score for m in treatment_metrics])

        baseline_performance = statistics.mean([m.performance.performance_score for m in baseline_metrics])
        treatment_performance = statistics.mean([m.performance.performance_score for m in treatment_metrics])

        baseline_impact = statistics.mean([m.impact.impact_score for m in baseline_metrics])
        treatment_impact = statistics.mean([m.impact.impact_score for m in treatment_metrics])

        baseline_overall = statistics.mean([m.overall_score for m in baseline_metrics])
        treatment_overall = statistics.mean([m.overall_score for m in treatment_metrics])

        # Create comparison results
        quality_comparison = self._create_comparison(
            "Quality",
            baseline_quality,
            treatment_quality,
            baseline_metrics,
            treatment_metrics,
        )

        performance_comparison = self._create_comparison(
            "Performance",
            baseline_performance,
            treatment_performance,
            baseline_metrics,
            treatment_metrics,
        )

        impact_comparison = self._create_comparison(
            "Impact",
            baseline_impact,
            treatment_impact,
            baseline_metrics,
            treatment_metrics,
        )

        overall_comparison = self._create_comparison(
            "Overall",
            baseline_overall,
            treatment_overall,
            baseline_metrics,
            treatment_metrics,
        )

        # Determine winner
        winner, recommendation = self._determine_winner(
            quality_comparison,
            performance_comparison,
            impact_comparison,
            overall_comparison,
        )

        # Detailed breakdown
        details = {
            "baseline_distribution": {
                "quality": [m.quality.composite_score for m in baseline_metrics],
                "performance": [m.performance.performance_score for m in baseline_metrics],
                "impact": [m.impact.impact_score for m in baseline_metrics],
                "overall": [m.overall_score for m in baseline_metrics],
            },
            "treatment_distribution": {
                "quality": [m.quality.composite_score for m in treatment_metrics],
                "performance": [m.performance.performance_score for m in treatment_metrics],
                "impact": [m.impact.impact_score for m in treatment_metrics],
                "overall": [m.overall_score for m in treatment_metrics],
            },
        }

        return ComparisonReport(
            baseline_name=baseline_name,
            treatment_name=treatment_name,
            comparison_date=datetime.utcnow(),
            baseline_size=len(baseline_metrics),
            treatment_size=len(treatment_metrics),
            quality_comparison=quality_comparison,
            performance_comparison=performance_comparison,
            impact_comparison=impact_comparison,
            overall_comparison=overall_comparison,
            winner=winner,
            recommendation=recommendation,
            details=details,
        )

    def _create_comparison(
        self,
        metric_name: str,
        baseline_value: float,
        current_value: float,
        baseline_metrics: List[PromptMetrics],
        current_metrics: List[PromptMetrics],
    ) -> ComparisonResult:
        """Create a comparison result."""
        delta = current_value - baseline_value
        delta_percent = (delta / baseline_value) * 100 if baseline_value != 0 else 0

        is_improvement = delta > 0

        # Simple t-test for significance
        baseline_values = self._extract_values(metric_name, baseline_metrics)
        current_values = self._extract_values(metric_name, current_metrics)

        is_significant = self._is_significant(baseline_values, current_values)

        return ComparisonResult(
            metric_name=metric_name,
            baseline_value=baseline_value,
            current_value=current_value,
            delta=delta,
            delta_percent=delta_percent,
            is_improvement=is_improvement,
            is_significant=is_significant,
        )

    def _extract_values(self, metric_name: str, metrics: List[PromptMetrics]) -> List[float]:
        """Extract values for a specific metric."""
        mapping = {
            "Quality": lambda m: m.quality.composite_score,
            "Performance": lambda m: m.performance.performance_score,
            "Impact": lambda m: m.impact.impact_score,
            "Overall": lambda m: m.overall_score,
        }

        extractor = mapping.get(metric_name)
        if extractor:
            return [extractor(m) for m in metrics]
        return []

    def _is_significant(self, baseline: List[float], treatment: List[float]) -> bool:
        """
        Perform simple t-test for significance.

        Uses simplified Welch's t-test assumption.
        """
        if len(baseline) < 3 or len(treatment) < 3:
            return False

        # Calculate means
        mean_b = statistics.mean(baseline)
        mean_t = statistics.mean(treatment)

        # Calculate standard deviations
        std_b = statistics.stdev(baseline) if len(baseline) > 1 else 0
        std_t = statistics.stdev(treatment) if len(treatment) > 1 else 0

        # If either has no variation, can't determine significance
        if std_b == 0 and std_t == 0:
            return False

        # Calculate standard error
        n_b, n_t = len(baseline), len(treatment)
        se = ((std_b ** 2) / n_b + (std_t ** 2) / n_t) ** 0.5

        if se == 0:
            return False

        # Calculate t-statistic
        t_stat = abs(mean_t - mean_b) / se

        # Critical value for 95% confidence (approximate)
        # For simplicity, use threshold of 2.0 (approx for typical sample sizes)
        return t_stat > 2.0

    def _determine_winner(
        self,
        quality: ComparisonResult,
        performance: ComparisonResult,
        impact: ComparisonResult,
        overall: ComparisonResult,
    ) -> Tuple[str, str]:
        """Determine winner and generate recommendation."""
        # Weighted scoring: quality (40%) + performance (30%) + impact (30%)
        score = 0

        if overall.is_improvement and overall.is_significant:
            score += 1
        elif not overall.is_improvement and overall.is_significant:
            score -= 1

        # Quality is most important
        if quality.is_improvement and quality.is_significant:
            score += 0.4
        elif not quality.is_improvement and quality.is_significant:
            score -= 0.4

        # Performance matters
        if performance.is_improvement and performance.is_significant:
            score += 0.3
        elif not performance.is_improvement and performance.is_significant:
            score -= 0.3

        # Impact matters
        if impact.is_improvement and impact.is_significant:
            score += 0.3
        elif not impact.is_improvement and impact.is_significant:
            score -= 0.3

        # Determine winner
        if score > 0.3:
            winner = "treatment"
            recommendation = (
                f"✅ Treatment wins: {overall.delta_percent:+.1f}% overall improvement "
                f"(Quality: {quality.delta_percent:+.1f}%, "
                f"Performance: {performance.delta_percent:+.1f}%, "
                f"Impact: {impact.delta_percent:+.1f}%)"
            )
        elif score < -0.3:
            winner = "baseline"
            recommendation = (
                f"❌ Treatment underperforms: {overall.delta_percent:+.1f}% overall change "
                f"(Quality: {quality.delta_percent:+.1f}%, "
                f"Performance: {performance.delta_percent:+.1f}%, "
                f"Impact: {impact.delta_percent:+.1f}%)"
            )
        else:
            winner = "inconclusive"
            recommendation = (
                "⚖️ Results inconclusive: Insufficient evidence to declare winner. "
                "Consider increasing sample size or refining the treatment."
            )

        return winner, recommendation


# ============================================================================
# MAIN ANALYZER
# ============================================================================

class MetricsAnalyzer:
    """
    Main analyzer providing high-level analysis interface.

    Combines trend analysis and comparison for comprehensive insights.
    """

    def __init__(self):
        """Initialize analyzer."""
        self.trend_analyzer = TrendAnalyzer()
        self.comparison_analyzer = ComparisonAnalyzer()

    def analyze_trends(self, metrics: List[PromptMetrics]) -> TrendAnalysis:
        """Analyze trends over time."""
        return self.trend_analyzer.analyze(metrics)

    def compare_versions(
        self,
        baseline: List[PromptMetrics],
        treatment: List[PromptMetrics],
        baseline_name: str = "Baseline",
        treatment_name: str = "Treatment",
    ) -> ComparisonReport:
        """Compare two versions (A/B test)."""
        return self.comparison_analyzer.compare(
            baseline_metrics=baseline,
            treatment_metrics=treatment,
            baseline_name=baseline_name,
            treatment_name=treatment_name,
        )

    def summarize(self, metrics: List[PromptMetrics]) -> Dict[str, Any]:
        """
        Generate summary statistics for a metrics collection.

        Args:
            metrics: List of prompt metrics

        Returns:
            Dictionary with summary statistics
        """
        if not metrics:
            return {
                "count": 0,
                "message": "No metrics to summarize",
            }

        overall_scores = [m.overall_score for m in metrics]
        quality_scores = [m.quality.composite_score for m in metrics]
        performance_scores = [m.performance.performance_score for m in metrics]
        impact_scores = [m.impact.impact_score for m in metrics]

        return {
            "count": len(metrics),
            "time_range": {
                "start": min(m.measured_at for m in metrics).isoformat(),
                "end": max(m.measured_at for m in metrics).isoformat(),
            },
            "overall": {
                "mean": statistics.mean(overall_scores),
                "median": statistics.median(overall_scores),
                "std_dev": statistics.stdev(overall_scores) if len(overall_scores) > 1 else 0,
                "min": min(overall_scores),
                "max": max(overall_scores),
            },
            "quality": {
                "mean": statistics.mean(quality_scores),
                "median": statistics.median(quality_scores),
                "std_dev": statistics.stdev(quality_scores) if len(quality_scores) > 1 else 0,
            },
            "performance": {
                "mean": statistics.mean(performance_scores),
                "median": statistics.median(performance_scores),
                "std_dev": statistics.stdev(performance_scores) if len(performance_scores) > 1 else 0,
            },
            "impact": {
                "mean": statistics.mean(impact_scores),
                "median": statistics.median(impact_scores),
                "std_dev": statistics.stdev(impact_scores) if len(impact_scores) > 1 else 0,
            },
            "grade_distribution": self._grade_distribution(metrics),
        }

    def _grade_distribution(self, metrics: List[PromptMetrics]) -> Dict[str, int]:
        """Calculate distribution of grades."""
        distribution = defaultdict(int)

        for m in metrics:
            distribution[m.grade] += 1

        return dict(sorted(distribution.items()))
