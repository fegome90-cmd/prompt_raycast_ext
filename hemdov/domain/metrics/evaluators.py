# hemdov/domain/metrics/evaluators.py
"""
Metrics Evaluators - Calculate metrics from prompt data.

This module provides the core evaluation logic that transforms raw prompt
data into structured, actionable metrics across all dimensions.

Key Principles:
- Automatic: No manual intervention required
- Fast: <10ms per evaluation
- Deterministic: Same input = same output
- Actionable: Each metric drives a specific improvement
"""

import logging
import re
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime

from .dimensions import (
    FrameworkType,
    ImpactMetrics,
    PerformanceMetrics,
    PromptMetrics,
    QualityMetrics,
)

logger = logging.getLogger(__name__)


# ============================================================================
# COST CALCULATION
# ============================================================================

PRICING_TABLE = {
    "anthropic": {
        "claude-haiku-4-5-20251001": {"input": 0.00008, "output": 0.00024},  # per 1K tokens
        "claude-sonnet-4-5-20250929": {"input": 0.003, "output": 0.015},
        "claude-opus-4-20250514": {"input": 0.015, "output": 0.075},
    },
    "deepseek": {
        "deepseek-chat": {"input": 0.00014, "output": 0.00028},
        "deepseek-reasoner": {"input": 0.00055, "output": 0.00219},
    },
    "openai": {
        "gpt-4o-mini": {"input": 0.00015, "output": 0.00060},
        "gpt-4o": {"input": 0.0025, "output": 0.01},
    },
    "gemini": {
        "gemini-2.0-flash-exp": {"input": 0.00001, "output": 0.00001},  # Approx
        "gemini-2.5-pro": {"input": 0.00125, "output": 0.005},
    },
    "ollama": {
        "default": {"input": 0.0, "output": 0.0},  # Free
    },
}


def calculate_cost(
    provider: str,
    model: str,
    input_tokens: int,
    output_tokens: int,
) -> float:
    """
    Calculate cost in USD for a given API call.

    Args:
        provider: LLM provider (anthropic, deepseek, openai, etc.)
        model: Model name
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens

    Returns:
        Cost in USD
    """
    provider_key = provider.lower()

    # Default to free if unknown
    if provider_key not in PRICING_TABLE:
        return 0.0

    pricing = PRICING_TABLE[provider_key]

    # Exact model match
    if model in pricing:
        rates = pricing[model]
    else:
        # Use default or free
        rates = pricing.get("default", {"input": 0.0, "output": 0.0})

    input_cost = (input_tokens / 1000) * rates["input"]
    output_cost = (output_tokens / 1000) * rates["output"]

    return input_cost + output_cost


def estimate_tokens(text: str) -> int:
    """
    Estimate token count from text.

    Uses a simple heuristic: ~4 characters per token for English text.
    This is approximate but sufficient for cost estimation.

    Args:
        text: Input text

    Returns:
        Estimated token count
    """
    return len(text) // 4


# ============================================================================
# QUALITY EVALUATORS
# ============================================================================

class QualityEvaluator:
    """
    Evaluates quality metrics from improved prompt.

    Uses heuristics and pattern matching to assess:
    - Coherence: Logical flow and structure
    - Relevance: Alignment with original intent
    - Completeness: Presence of required sections
    - Clarity: Absence of ambiguity
    """

    # Patterns for required sections
    ROLE_PATTERNS = [
        r"role\s*[:=]\s*\w+",
        r"you are a\s+\w+",
        r"act as\s+a\s+\w+",
        r"#\s*role",
    ]

    DIRECTIVE_PATTERNS = [
        r"task\s*[:=]",
        r"your\s+(task|job|mission)",
        r"#\s*task",
        r"requirements?",
    ]

    FRAMEWORK_PATTERNS = [
        r"framework\s*[:=]\s*\w+",
        r"approach\s*[:=]\s*\w+",
        r"method\s*[:=]\s*\w+",
    ]

    GUARDRAIL_PATTERNS = [
        r"guardrails?",
        r"constraints?",
        r"avoid\s+\w+",
        r"do\s+not\s+\w+",
        r"ensure\s+that",
    ]

    @classmethod
    def evaluate(
        cls,
        original_idea: str,
        improved_prompt: str,
        framework: str,
        guardrails: list[str],
    ) -> QualityMetrics:
        """
        Calculate quality metrics from prompt data.

        Args:
            original_idea: Original user input
            improved_prompt: Improved prompt text
            framework: Framework used (chain-of-thought, etc.)
            guardrails: List of guardrails

        Returns:
            QualityMetrics instance
        """
        # Coherence: Check for logical structure
        coherence_score = cls._calculate_coherence(improved_prompt)

        # Relevance: How well it addresses original intent
        relevance_score = cls._calculate_relevance(original_idea, improved_prompt)

        # Completeness: Presence of all required sections
        completeness_score = cls._calculate_completeness(improved_prompt, framework, guardrails)

        # Clarity: Absence of ambiguity indicators
        clarity_score = cls._calculate_clarity(improved_prompt)

        # Guardrails count
        guardrails_count = len(guardrails)

        # Required structure check
        has_role = any(re.search(p, improved_prompt, re.IGNORECASE) for p in cls.ROLE_PATTERNS)
        has_directive = any(re.search(p, improved_prompt, re.IGNORECASE) for p in cls.DIRECTIVE_PATTERNS)
        has_required_structure = has_role and has_directive

        return QualityMetrics(
            coherence_score=coherence_score,
            relevance_score=relevance_score,
            completeness_score=completeness_score,
            clarity_score=clarity_score,
            guardrails_count=guardrails_count,
            has_required_structure=has_required_structure,
        )

    @classmethod
    def _calculate_coherence(cls, prompt: str) -> float:
        """Assess logical flow and structure."""
        score = 0.5  # Base score

        # Bonus for clear sections
        if re.search(r"^#+\s*\w+", prompt, re.MULTILINE):
            score += 0.15  # Has headers

        if re.search(r"\n\n+", prompt):
            score += 0.10  # Has paragraph breaks

        # Bonus for numbered or bulleted lists
        if re.search(r"^\s*[-*]\s+", prompt, re.MULTILINE):
            score += 0.10  # Has bullets

        if re.search(r"^\s*\d+\.\s+", prompt, re.MULTILINE):
            score += 0.10  # Has numbered list

        # Penalty for very short prompts
        if len(prompt) < 100:
            score -= 0.20

        # Penalty for very long single paragraphs
        if len(prompt) > 500 and "\n" not in prompt[:200]:
            score -= 0.15

        return max(0.0, min(1.0, score))

    @classmethod
    def _calculate_relevance(cls, original: str, improved: str) -> float:
        """Assess alignment with original intent."""
        # Extract key terms from original
        original_words = set(re.findall(r"\b\w{3,}\b", original.lower()))

        if not original_words:
            return 0.5  # Neutral if no key terms

        # Check how many appear in improved prompt
        improved_lower = improved.lower()
        matched = sum(1 for word in original_words if word in improved_lower)

        relevance = matched / len(original_words)

        # Bonus for capturing action verbs
        action_verbs = {"write", "create", "generate", "build", "implement", "design", "develop"}
        if any(verb in original.lower() for verb in action_verbs):
            if any(verb in improved_lower for verb in action_verbs):
                relevance += 0.10

        return min(1.0, relevance)

    @classmethod
    def _calculate_completeness(cls, prompt: str, framework: str, guardrails: list[str]) -> float:
        """Assess presence of required sections."""
        score = 0.0

        # Has role section
        if any(re.search(p, prompt, re.IGNORECASE) for p in cls.ROLE_PATTERNS):
            score += 0.25

        # Has directive/task section
        if any(re.search(p, prompt, re.IGNORECASE) for p in cls.DIRECTIVE_PATTERNS):
            score += 0.25

        # Has framework (if not default)
        if framework != "chain-of-thought":
            if framework.lower() in prompt.lower():
                score += 0.15

        # Has guardrails section
        if any(re.search(p, prompt, re.IGNORECASE) for p in cls.GUARDRAIL_PATTERNS):
            score += 0.15

        # Has actual guardrails
        if guardrails:
            score += 0.10

        # Bonus for context/background
        if re.search(r"context|background|overview", prompt, re.IGNORECASE):
            score += 0.10

        return min(1.0, score)

    @classmethod
    def _calculate_clarity(cls, prompt: str) -> float:
        """Assess absence of ambiguity."""
        score = 1.0  # Start perfect, deduct for issues

        # Penalty for vague terms
        vague_terms = [
            "etc", "etcetera", "and so on", "things like that",
            "stuff", "whatever", "something", "somehow",
        ]
        for term in vague_terms:
            if re.search(r"\b" + term + r"\b", prompt, re.IGNORECASE):
                score -= 0.05

        # Penalty for ambiguity markers
        ambiguous = ["maybe", "possibly", "might", "could be", "sort of", "kind of"]
        for marker in ambiguous:
            if re.search(r"\b" + marker + r"\b", prompt, re.IGNORECASE):
                score -= 0.03

        # Penalty for excessive hedging
        if len(re.findall(r"\b(just|only|simply|barely)\b", prompt, re.IGNORECASE)) > 3:
            score -= 0.10

        # Bonus for specific requirements
        if re.search(r"\d+\s*(words?|lines?|items?|points?)", prompt, re.IGNORECASE):
            score += 0.05

        # Bonus for examples
        if re.search(r"for example|e\.g\.|such as|like:", prompt, re.IGNORECASE):
            score += 0.05

        return max(0.0, min(1.0, score))


# ============================================================================
# PERFORMANCE EVALUATORS
# ============================================================================

@dataclass
class PromptImprovementResult:
    """Result of a prompt improvement operation."""
    improved_prompt: str
    role: str
    directive: str
    framework: str
    guardrails: list[str]
    reasoning: str | None = None
    confidence: float | None = None
    latency_ms: int | None = None
    backend: str | None = None
    provider: str | None = None
    model: str | None = None


class PerformanceEvaluator:
    """
    Evaluates performance metrics from API call data.

    Captures resource utilization: latency, tokens, cost.
    """

    @classmethod
    def evaluate(
        cls,
        latency_ms: int,
        provider: str,
        model: str,
        backend: str,
        original_idea: str,
        improved_prompt: str,
    ) -> PerformanceMetrics:
        """
        Calculate performance metrics.

        Args:
            latency_ms: Request latency in milliseconds
            provider: LLM provider
            model: Model name
            backend: Backend type (zero-shot | few-shot)
            original_idea: Original input text
            improved_prompt: Improved output text

        Returns:
            PerformanceMetrics instance
        """
        # Estimate tokens
        input_tokens = estimate_tokens(original_idea)
        output_tokens = estimate_tokens(improved_prompt)
        total_tokens = input_tokens + output_tokens

        # Calculate cost
        cost_usd = calculate_cost(provider, model, input_tokens, output_tokens)

        return PerformanceMetrics(
            latency_ms=latency_ms,
            total_tokens=total_tokens,
            cost_usd=cost_usd,
            provider=provider,
            model=model,
            backend=backend,
        )


# ============================================================================
# IMPACT EVALUATORS
# ============================================================================

@dataclass
class ImpactData:
    """User interaction data for impact evaluation."""
    copy_count: int = 0
    regeneration_count: int = 0
    feedback_score: int | None = None
    reuse_count: int = 0


class ImpactEvaluator:
    """
    Evaluates impact metrics from user interaction data.

    Requires tracking user behavior: copies, regenerations, feedback.
    """

    @classmethod
    def evaluate(cls, data: ImpactData) -> ImpactMetrics:
        """
        Calculate impact metrics.

        Args:
            data: User interaction data

        Returns:
            ImpactMetrics instance
        """
        return ImpactMetrics(
            copy_count=data.copy_count,
            regeneration_count=data.regeneration_count,
            feedback_score=data.feedback_score,
            reuse_count=data.reuse_count,
        )


# ============================================================================
# MAIN CALCULATOR
# ============================================================================

class PromptMetricsCalculator:
    """
    Main calculator that aggregates all metric dimensions.

    This is the primary interface for calculating comprehensive prompt metrics.
    """

    def __init__(self):
        """Initialize calculator."""
        self.quality_evaluator = QualityEvaluator()
        self.performance_evaluator = PerformanceEvaluator()
        self.impact_evaluator = ImpactEvaluator()

    def calculate(
        self,
        original_idea: str,
        result: PromptImprovementResult,
        impact_data: ImpactData | None = None,
        prompt_id: str | None = None,
    ) -> PromptMetrics:
        """
        Calculate comprehensive metrics for a prompt improvement.

        Args:
            original_idea: Original user input
            result: Improvement result with all outputs
            impact_data: Optional user interaction data
            prompt_id: Optional unique identifier (generated if not provided)

        Returns:
            Complete PromptMetrics instance
        """
        # Generate ID if not provided
        if prompt_id is None:
            prompt_id = str(uuid.uuid4())

        # Get latency (default to 0 if not provided)
        latency_ms = result.latency_ms or 0

        # Parse framework
        try:
            framework = FrameworkType(result.framework)
        except ValueError:
            framework = FrameworkType.CHAIN_OF_THOUGHT

        # Calculate quality metrics
        quality = self.quality_evaluator.evaluate(
            original_idea=original_idea,
            improved_prompt=result.improved_prompt,
            framework=result.framework,
            guardrails=result.guardrails,
        )

        # Calculate performance metrics
        performance = self.performance_evaluator.evaluate(
            latency_ms=latency_ms,
            provider=result.provider or result.model or "unknown",  # Use provider if available
            model=result.model or "unknown",
            backend=result.backend or "zero-shot",  # Use backend from result, default to zero-shot
            original_idea=original_idea,
            improved_prompt=result.improved_prompt,
        )

        # Calculate impact metrics (default to zeros if not provided)
        if impact_data is None:
            impact_data = ImpactData()
        impact = self.impact_evaluator.evaluate(impact_data)

        # Create composite metrics
        return PromptMetrics(
            prompt_id=prompt_id,
            original_idea=original_idea,
            improved_prompt=result.improved_prompt,
            quality=quality,
            performance=performance,
            impact=impact,
            measured_at=datetime.now(UTC),
            framework=framework,
            provider=performance.provider,
            model=performance.model,
            backend=performance.backend,
        )

    def calculate_from_history(
        self,
        original_idea: str,
        context: str,
        improved_prompt: str,
        role: str,
        directive: str,
        framework: str,
        guardrails: list[str],
        backend: str,
        model: str,
        provider: str,
        latency_ms: int | None = None,
        confidence: float | None = None,
        impact_data: ImpactData | None = None,
    ) -> PromptMetrics:
        """
        Calculate metrics from PromptHistory entity fields.

        This bridges the legacy entity format with the new metrics framework.

        Args:
            original_idea: Original user input
            context: Additional context
            improved_prompt: Improved prompt text
            role: Role assigned
            directive: Directive/task
            framework: Framework used
            guardrails: List of guardrails
            backend: Backend type
            model: Model name
            provider: Provider name
            latency_ms: Request latency
            confidence: Confidence score
            impact_data: Optional user interaction data

        Returns:
            Complete PromptMetrics instance
        """
        # Create PromptImprovementResult
        result = PromptImprovementResult(
            improved_prompt=improved_prompt,
            role=role,
            directive=directive,
            framework=framework,
            guardrails=guardrails,
            reasoning=None,
            confidence=confidence,
            latency_ms=latency_ms,
            backend=backend,
        )

        # Override model/provider in result for performance evaluation
        result.model = model
        result.provider = provider

        return self.calculate(
            original_idea=original_idea,
            result=result,
            impact_data=impact_data,
        )


# Singleton instance for easy access
_calculator_instance: PromptMetricsCalculator | None = None


def get_calculator() -> PromptMetricsCalculator:
    """Get singleton calculator instance."""
    global _calculator_instance
    if _calculator_instance is None:
        _calculator_instance = PromptMetricsCalculator()
    return _calculator_instance
