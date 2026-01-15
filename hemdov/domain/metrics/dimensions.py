# hemdov/domain/metrics/dimensions.py
"""
Metrics Dimensions - Data structures for multidimensional prompt metrics.

Each dimension captures specific aspects of prompt quality:
- QualityMetrics: Structural and semantic quality
- PerformanceMetrics: Resource utilization and efficiency
- ImpactMetrics: User-facing outcomes
- ImprovementMetrics: Progress over time
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class FrameworkType(Enum):
    """Allowed framework types."""
    CHAIN_OF_THOUGHT = "chain-of-thought"
    TREE_OF_THOUGHTS = "tree-of-thoughts"
    DECOMPOSITION = "decomposition"
    ROLE_PLAYING = "role-playing"


# ============================================================================
# QUALITY DIMENSIONS
# ============================================================================

@dataclass(frozen=True)
class QualityMetrics:
    """
    Quality metrics capture structural and semantic aspects of prompts.

    All scores are normalized 0-1 where higher is better.
    """

    # Coherence: How well the prompt flows logically
    coherence_score: float

    # Relevance: How well the prompt addresses the original intent
    relevance_score: float

    # Completeness: How comprehensive the prompt is
    completeness_score: float

    # Clarity: How unambiguous the prompt is
    clarity_score: float

    # Guardrails count: Number of safety constraints (more is better)
    guardrails_count: int

    # Has all required sections (role, directive, framework)
    has_required_structure: bool

    # Composite quality score (weighted average)
    composite_score: float = field(init=False)

    def __post_init__(self):
        """Calculate composite score."""
        # Weighted average: coherence (30%) + relevance (30%) + completeness (20%) + clarity (20%)
        composite = (
            self.coherence_score * 0.30 +
            self.relevance_score * 0.30 +
            self.completeness_score * 0.20 +
            self.clarity_score * 0.20
        )

        # Bonus for having guardrails (+5% per guardrail, max +15%)
        guardrails_bonus = min(self.guardrails_count * 0.05, 0.15)

        # Bonus for complete structure (+10%)
        structure_bonus = 0.10 if self.has_required_structure else 0.0

        final_score = min(1.0, composite + guardrails_bonus + structure_bonus)
        object.__setattr__(self, 'composite_score', final_score)

    @property
    def grade(self) -> str:
        """Letter grade for quality score."""
        if self.composite_score >= 0.90:
            return "A"
        elif self.composite_score >= 0.80:
            return "B"
        elif self.composite_score >= 0.70:
            return "C"
        elif self.composite_score >= 0.60:
            return "D"
        else:
            return "F"


# ============================================================================
# PERFORMANCE DIMENSIONS
# ============================================================================

@dataclass(frozen=True)
class PerformanceMetrics:
    """
    Performance metrics capture resource utilization and efficiency.
    """

    # Latency in milliseconds
    latency_ms: int

    # Estimated token count (input + output)
    total_tokens: int

    # Estimated cost in USD
    cost_usd: float

    # Provider used
    provider: str

    # Model used
    model: str

    # Backend type (zero-shot | few-shot)
    backend: str

    # Performance score (higher is better, max 1.0)
    performance_score: float = field(init=False)

    def __post_init__(self):
        """Calculate performance score based on efficiency."""
        # Latency score: <5s = 1.0, >30s = 0.0, linear between
        latency_score = max(0.0, 1.0 - (self.latency_ms - 5000) / 25000)
        latency_score = max(0.0, min(1.0, latency_score))

        # Cost score: <$0.01 = 1.0, >$0.10 = 0.0, linear between
        cost_score = max(0.0, 1.0 - (self.cost_usd - 0.01) / 0.09)
        cost_score = max(0.0, min(1.0, cost_score))

        # Token efficiency: <1000 tokens = 1.0, >5000 = 0.0
        token_score = max(0.0, 1.0 - (self.total_tokens - 1000) / 4000)
        token_score = max(0.0, min(1.0, token_score))

        # Composite: latency (50%) + cost (30%) + tokens (20%)
        performance = latency_score * 0.50 + cost_score * 0.30 + token_score * 0.20
        object.__setattr__(self, 'performance_score', performance)

    @property
    def grade(self) -> str:
        """Letter grade for performance."""
        if self.performance_score >= 0.80:
            return "A"
        elif self.performance_score >= 0.60:
            return "B"
        elif self.performance_score >= 0.40:
            return "C"
        elif self.performance_score >= 0.20:
            return "D"
        else:
            return "F"


# ============================================================================
# IMPACT DIMENSIONS
# ============================================================================

@dataclass(frozen=True)
class ImpactMetrics:
    """
    Impact metrics capture user-facing outcomes and behaviors.

    These require user interaction data (feedback, reuse, etc.).
    """

    # Number of times the prompt was copied to clipboard
    copy_count: int = 0

    # Number of times the prompt was regenerated (user was unsatisfied)
    regeneration_count: int = 0

    # User feedback score (1-5, if provided)
    feedback_score: int | None = None

    # Number of times the prompt was used in session
    reuse_count: int = 0

    # Success rate (0-1): prompt was accepted without regeneration
    success_rate: float = field(init=False)

    # Impact score (higher is better, max 1.0)
    impact_score: float = field(init=False)

    def __post_init__(self):
        """Calculate impact score."""
        # Success rate: first attempt success
        total_attempts = self.copy_count + self.regeneration_count
        success_rate = (self.copy_count / total_attempts) if total_attempts > 0 else 0.0
        object.__setattr__(self, 'success_rate', success_rate)

        # Impact components
        copy_score = min(1.0, self.copy_count / 3)  # 3+ copies = max
        success_score = self.success_rate  # Direct success rate
        feedback_score = (self.feedback_score or 3) / 5  # Normalize to 0-1
        reuse_score = min(1.0, self.reuse_count / 2)  # 2+ reuses = max

        # Composite: copy (30%) + success (30%) + feedback (25%) + reuse (15%)
        impact = (
            copy_score * 0.30 +
            success_score * 0.30 +
            feedback_score * 0.25 +
            reuse_score * 0.15
        )
        object.__setattr__(self, 'impact_score', impact)

    @property
    def grade(self) -> str:
        """Letter grade for impact."""
        if self.impact_score >= 0.80:
            return "A"
        elif self.impact_score >= 0.60:
            return "B"
        elif self.impact_score >= 0.40:
            return "C"
        elif self.impact_score >= 0.20:
            return "D"
        else:
            return "F"


# ============================================================================
# IMPROVEMENT DIMENSIONS
# ============================================================================

@dataclass(frozen=True)
class ImprovementMetrics:
    """
    Improvement metrics capture progress over time through A/B testing.

    These compare current performance against baseline or previous versions.
    """

    # Version identifier
    version: str

    # Baseline metrics (for comparison)
    baseline_quality: float
    baseline_performance: float
    baseline_impact: float

    # Current metrics
    current_quality: float
    current_performance: float
    current_impact: float

    # Timestamp of measurement
    measured_at: datetime

    # Delta scores (positive = improvement)
    quality_delta: float = field(init=False)
    performance_delta: float = field(init=False)
    impact_delta: float = field(init=False)

    # Overall improvement score (weighted delta)
    improvement_score: float = field(init=False)

    def __post_init__(self):
        """Calculate improvement deltas."""
        quality_delta = self.current_quality - self.baseline_quality
        performance_delta = self.current_performance - self.baseline_performance
        impact_delta = self.current_impact - self.baseline_impact

        object.__setattr__(self, 'quality_delta', quality_delta)
        object.__setattr__(self, 'performance_delta', performance_delta)
        object.__setattr__(self, 'impact_delta', impact_delta)

        # Composite improvement: quality (40%) + performance (30%) + impact (30%)
        improvement = (
            (quality_delta if quality_delta > 0 else quality_delta * 0.5) * 0.40 +
            (performance_delta if performance_delta > 0 else performance_delta * 0.5) * 0.30 +
            (impact_delta if impact_delta > 0 else impact_delta * 0.5) * 0.30
        )
        object.__setattr__(self, 'improvement_score', improvement)

    @property
    def trend(self) -> str:
        """Trend direction."""
        if self.improvement_score > 0.10:
            return "↗️ Strongly Improving"
        elif self.improvement_score > 0.02:
            return "→ Improving"
        elif self.improvement_score > -0.02:
            return "→ Stable"
        elif self.improvement_score > -0.10:
            return "↘ Declining"
        else:
            return "⬇️ Strongly Declining"


# ============================================================================
# COMPOSITE METRICS
# ============================================================================

@dataclass(frozen=True)
class PromptMetrics:
    """
    Complete metrics for a single prompt improvement event.

    Aggregates all dimensions into a single comprehensive score.
    """

    # Input/output identifiers
    prompt_id: str
    original_idea: str
    improved_prompt: str

    # Dimension scores
    quality: QualityMetrics
    performance: PerformanceMetrics
    impact: ImpactMetrics

    # Metadata
    measured_at: datetime
    framework: FrameworkType
    provider: str
    model: str
    backend: str

    # Overall score (weighted across dimensions)
    overall_score: float = field(init=False)

    def __post_init__(self):
        """Calculate overall score."""
        # Weighted: quality (50%) + performance (25%) + impact (25%)
        # Quality gets highest weight as it's the primary value
        overall = (
            self.quality.composite_score * 0.50 +
            self.performance.performance_score * 0.25 +
            self.impact.impact_score * 0.25
        )
        object.__setattr__(self, 'overall_score', overall)

    @property
    def grade(self) -> str:
        """Overall letter grade."""
        if self.overall_score >= 0.90:
            return "A+"
        elif self.overall_score >= 0.85:
            return "A"
        elif self.overall_score >= 0.80:
            return "A-"
        elif self.overall_score >= 0.75:
            return "B+"
        elif self.overall_score >= 0.70:
            return "B"
        elif self.overall_score >= 0.65:
            return "B-"
        elif self.overall_score >= 0.60:
            return "C+"
        elif self.overall_score >= 0.50:
            return "C"
        else:
            return "D"

    @property
    def is_acceptable(self) -> bool:
        """Check if metrics meet minimum quality threshold."""
        return (
            self.quality.composite_score >= 0.60 and  # C or better
            self.performance.performance_score >= 0.40 and  # C or better
            self.impact.success_rate >= 0.50  # 50% success rate
        )

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "prompt_id": self.prompt_id,
            "overall_score": self.overall_score,
            "grade": self.grade,
            "is_acceptable": self.is_acceptable,
            "quality": {
                "composite_score": self.quality.composite_score,
                "grade": self.quality.grade,
                "coherence": self.quality.coherence_score,
                "relevance": self.quality.relevance_score,
                "completeness": self.quality.completeness_score,
                "clarity": self.quality.clarity_score,
                "guardrails_count": self.quality.guardrails_count,
                "has_structure": self.quality.has_required_structure,
            },
            "performance": {
                "performance_score": self.performance.performance_score,
                "grade": self.performance.grade,
                "latency_ms": self.performance.latency_ms,
                "total_tokens": self.performance.total_tokens,
                "cost_usd": self.performance.cost_usd,
                "provider": self.performance.provider,
                "model": self.performance.model,
                "backend": self.performance.backend,
            },
            "impact": {
                "impact_score": self.impact.impact_score,
                "grade": self.impact.grade,
                "success_rate": self.impact.success_rate,
                "copy_count": self.impact.copy_count,
                "regeneration_count": self.impact.regeneration_count,
                "feedback_score": self.impact.feedback_score,
                "reuse_count": self.impact.reuse_count,
            },
            "metadata": {
                "measured_at": self.measured_at.isoformat(),
                "framework": self.framework.value,
                "provider": self.provider,
                "model": self.model,
                "backend": self.backend,
            }
        }
