# tests/test_metrics_evaluators.py
"""
Tests for metrics calculation logic (evaluators.py).
Tests quality, performance, and impact evaluators.
"""

from hemdov.domain.metrics.dimensions import (
    FrameworkType,
    ImpactMetrics,
    PerformanceMetrics,
    PromptMetrics,
    QualityMetrics,
)
from hemdov.domain.metrics.evaluators import (
    ImpactData,
    ImpactEvaluator,
    PerformanceEvaluator,
    PromptImprovementResult,
    PromptMetricsCalculator,
    QualityEvaluator,
    calculate_cost,
    estimate_tokens,
)

# ============================================================================
# COST AND TOKEN ESTIMATION TESTS
# ============================================================================

def test_calculate_cost_anthropic_haiku():
    """Test cost calculation for Anthropic Claude Haiku."""
    cost = calculate_cost(
        provider="anthropic",
        model="claude-haiku-4-5-20251001",
        input_tokens=1000,
        output_tokens=500,
    )

    # Haiku: $0.00008 input, $0.00024 output per 1K tokens
    # Expected: (1000/1000 * 0.00008) + (500/1000 * 0.00024) = 0.00008 + 0.00012 = 0.0002
    assert cost > 0
    assert cost < 0.01  # Should be very cheap


def test_calculate_cost_anthropic_sonnet():
    """Test cost calculation for Anthropic Claude Sonnet."""
    cost = calculate_cost(
        provider="anthropic",
        model="claude-sonnet-4-5-20250929",
        input_tokens=1000,
        output_tokens=500,
    )

    # Sonnet is more expensive than Haiku
    haiku_cost = calculate_cost(
        provider="anthropic",
        model="claude-haiku-4-5-20251001",
        input_tokens=1000,
        output_tokens=500,
    )

    assert cost > haiku_cost


def test_calculate_cost_deepseek():
    """Test cost calculation for DeepSeek."""
    cost = calculate_cost(
        provider="deepseek",
        model="deepseek-chat",
        input_tokens=1000,
        output_tokens=500,
    )

    # DeepSeek is very affordable
    assert cost > 0
    assert cost < 0.001


def test_calculate_cost_unknown_provider():
    """Test cost calculation returns 0 for unknown provider."""
    cost = calculate_cost(
        provider="unknown_provider",
        model="unknown_model",
        input_tokens=1000,
        output_tokens=500,
    )

    assert cost == 0.0


def test_estimate_tokens():
    """Test token estimation from text."""
    # Simple heuristic: ~4 characters per token
    text = "This is a test prompt with some text."
    estimated = estimate_tokens(text)

    assert estimated > 0
    assert estimated == len(text) // 4


def test_estimate_tokens_empty():
    """Test token estimation with empty string."""
    assert estimate_tokens("") == 0


# ============================================================================
# QUALITY EVALUATOR TESTS
# ============================================================================

def test_quality_evaluator_coherence_high():
    """Test coherence evaluation for well-structured prompt."""
    evaluator = QualityEvaluator()

    # High coherence prompt with clear structure
    prompt = """# Role: Expert Data Analyst

## Task
Analyze the sales data and provide insights.

## Steps
1. Load the CSV file
2. Clean the data
3. Generate visualizations
4. Write summary report

## Output Format
Provide results in markdown format.
"""

    score = evaluator._calculate_coherence(prompt)

    # Should score high for structured prompt with headers and lists
    assert score >= 0.7


def test_quality_evaluator_coherence_low():
    """Test coherence evaluation for poorly structured prompt."""
    evaluator = QualityEvaluator()

    # Low coherence: very short, no structure
    prompt = "analyze data"

    score = evaluator._calculate_coherence(prompt)

    # Should score low
    assert score < 0.6


def test_quality_evaluator_relevance_high():
    """Test relevance evaluation when prompt maintains intent."""
    evaluator = QualityEvaluator()

    original = "Create a data analysis script in Python"
    improved = """# Role: Python Data Analyst

Create a Python script that analyzes CSV data, generates plots using matplotlib,
and exports the results to a PDF report.
"""

    score = evaluator._calculate_relevance(original, improved)

    # Should maintain relevance
    assert score >= 0.6


def test_quality_evaluator_relevance_low():
    """Test relevance evaluation when prompt drifts from intent."""
    evaluator = QualityEvaluator()

    original = "Create a data analysis script"
    improved = """# Role: Web Developer

Build a responsive HTML website with CSS styling and JavaScript interactivity.
"""

    score = evaluator._calculate_relevance(original, improved)

    # Should have lower relevance due to topic drift
    assert score < 0.5


def test_quality_evaluator_completeness_high():
    """Test completeness evaluation for comprehensive prompt."""
    evaluator = QualityEvaluator()

    prompt = """# Role: Expert Data Analyst

## Task
Analyze the data.

## Context
We have monthly sales data for the past year.

## Steps
1. Load data
2. Process data
3. Generate insights

## Constraints
- Use Python pandas
- Ensure data privacy
- Handle missing values appropriately
"""

    score = evaluator._calculate_completeness(
        prompt,
        framework="chain-of-thought",
        guardrails=["Use Python pandas", "Ensure data privacy", "Handle missing values"]
    )

    # Should score high for complete structure
    assert score >= 0.7


def test_quality_evaluator_completeness_minimal():
    """Test completeness evaluation for minimal prompt."""
    evaluator = QualityEvaluator()

    prompt = "Analyze the data."

    score = evaluator._calculate_completeness(
        prompt,
        framework="chain-of-thought",
        guardrails=[]
    )

    # Should score low for minimal prompt
    assert score < 0.5


def test_quality_evaluator_clarity_high():
    """Test clarity evaluation for clear, specific prompt."""
    evaluator = QualityEvaluator()

    clear_prompt = """# Role: Data Analyst

Write a Python function that:
- Takes a CSV file path as input
- Loads the data using pandas
- Calculates summary statistics (mean, median, std)
- Returns results as a dictionary
- Handles missing values by dropping rows

For example: analyze_data('sales.csv') should return {'mean': 1500, 'median': 1200, 'std': 300}
"""

    score = evaluator._calculate_clarity(clear_prompt)

    # Should score high for specific, unambiguous prompt
    assert score >= 0.7


def test_quality_evaluator_clarity_low():
    """Test clarity evaluation for vague, ambiguous prompt."""
    evaluator = QualityEvaluator()

    vague_prompt = """Do some stuff with the data and maybe handle things
    and perhaps do something else if needed and stuff like that etc."""

    score = evaluator._calculate_clarity(vague_prompt)

    # Should score low for vague prompt with hedge words
    # Penalties: stuff(-0.05), etc(-0.05), something(-0.05), maybe(-0.03) = 0.18 total
    # Score: 1.0 - 0.18 = 0.82
    assert score < 0.9
    assert score > 0.7


def test_quality_evaluator_full_evaluation():
    """Test full quality evaluation with all dimensions."""
    evaluator = QualityEvaluator()

    quality = evaluator.evaluate(
        original_idea="Create a data analysis script",
        improved_prompt="""# Role: Data Analyst

## Task
Write a Python script to analyze CSV data and generate visualizations.

## Steps
1. Load data using pandas
2. Clean missing values
3. Create plots with matplotlib

## Constraints
- Handle edge cases
- Provide clear comments
""",
        framework="chain-of-thought",
        guardrails=["Handle edge cases", "Provide clear comments"],
    )

    assert isinstance(quality, QualityMetrics)
    assert 0.0 <= quality.coherence_score <= 1.0
    assert 0.0 <= quality.relevance_score <= 1.0
    assert 0.0 <= quality.completeness_score <= 1.0
    assert 0.0 <= quality.clarity_score <= 1.0
    assert quality.guardrails_count == 2
    assert quality.has_required_structure is True


# ============================================================================
# PERFORMANCE EVALUATOR TESTS
# ============================================================================

def test_performance_evaluator_fast():
    """Test performance evaluation for fast response."""
    evaluator = PerformanceEvaluator()

    performance = evaluator.evaluate(
        latency_ms=3000,
        provider="anthropic",
        model="claude-haiku-4-5-20251001",
        backend="zero-shot",
        original_idea="Create a data analysis script",
        improved_prompt="# Role: Data Analyst\nWrite a Python script.",
    )

    assert isinstance(performance, PerformanceMetrics)
    assert performance.latency_ms == 3000
    assert performance.performance_score > 0.7  # Fast = high score


def test_performance_evaluator_slow():
    """Test performance evaluation for slow response."""
    evaluator = PerformanceEvaluator()

    performance = evaluator.evaluate(
        latency_ms=30000,
        provider="anthropic",
        model="claude-sonnet-4-5-20250929",
        backend="few-shot",
        original_idea="Create a data analysis script",
        improved_prompt="# Role: Data Analyst\nWrite a Python script." * 10,  # Longer text
    )

    assert isinstance(performance, PerformanceMetrics)
    assert performance.latency_ms == 30000
    assert performance.performance_score < 0.7  # Slow = lower score (latency_score = 0.0, but cost/token can add up to 0.5 max)


def test_performance_evaluator_cost_calculation():
    """Test that performance evaluation includes cost calculation."""
    evaluator = PerformanceEvaluator()

    performance = evaluator.evaluate(
        latency_ms=5000,
        provider="anthropic",
        model="claude-haiku-4-5-20251001",
        backend="zero-shot",
        original_idea="test idea",
        improved_prompt="test prompt",
    )

    assert performance.cost_usd >= 0
    assert performance.total_tokens > 0


# ============================================================================
# IMPACT EVALUATOR TESTS
# ============================================================================

def test_impact_evaluator_high_impact():
    """Test impact evaluation for high user engagement."""
    evaluator = ImpactEvaluator()

    impact = evaluator.evaluate(
        ImpactData(
            copy_count=10,
            regeneration_count=0,
            feedback_score=5,
            reuse_count=5,
        )
    )

    assert isinstance(impact, ImpactMetrics)
    assert impact.copy_count == 10
    assert impact.regeneration_count == 0
    assert impact.feedback_score == 5
    assert impact.reuse_count == 5
    assert impact.success_rate >= 0.9  # High success rate
    assert impact.impact_score >= 0.7  # High impact


def test_impact_evaluator_low_impact():
    """Test impact evaluation for low user engagement."""
    evaluator = ImpactEvaluator()

    impact = evaluator.evaluate(
        ImpactData(
            copy_count=1,
            regeneration_count=5,
            feedback_score=2,
            reuse_count=0,
        )
    )

    assert isinstance(impact, ImpactMetrics)
    assert impact.copy_count == 1
    assert impact.regeneration_count == 5
    assert impact.success_rate <= 0.3  # Low success rate
    assert impact.impact_score < 0.5  # Low impact


def test_impact_evaluator_no_feedback():
    """Test impact evaluation when no feedback provided."""
    evaluator = ImpactEvaluator()

    impact = evaluator.evaluate(
        ImpactData(
            copy_count=3,
            regeneration_count=1,
            feedback_score=None,  # No feedback
            reuse_count=2,
        )
    )

    # Should still calculate score (defaults to neutral feedback)
    assert impact.impact_score >= 0


# ============================================================================
# PROMPT METRICS CALCULATOR TESTS
# ============================================================================

def test_metrics_calculator_basic():
    """Test basic metrics calculation."""
    calculator = PromptMetricsCalculator()

    result = PromptImprovementResult(
        improved_prompt="# Role: Data Analyst\nWrite a Python script.",
        role="Data Analyst",
        directive="Write a Python script",
        framework="chain-of-thought",
        guardrails=["Handle edge cases"],
        reasoning=None,
        confidence=None,
        latency_ms=5000,
    )

    # Add model/provider attributes (normally done elsewhere)
    result.model = "claude-haiku-4-5-20251001"
    result.provider = "anthropic"

    metrics = calculator.calculate(
        original_idea="Create a data analysis script",
        result=result,
        impact_data=ImpactData(copy_count=5, regeneration_count=1),
    )

    assert isinstance(metrics, PromptMetrics)
    assert metrics.original_idea == "Create a data analysis script"
    assert metrics.improved_prompt == "# Role: Data Analyst\nWrite a Python script."
    assert metrics.quality.composite_score > 0
    assert metrics.performance.performance_score > 0
    assert metrics.impact.impact_score > 0
    assert metrics.overall_score > 0


def test_metrics_calculator_without_impact():
    """Test metrics calculation without impact data (should default to zeros)."""
    calculator = PromptMetricsCalculator()

    result = PromptImprovementResult(
        improved_prompt="test prompt",
        role="Test",
        directive="test",
        framework="chain-of-thought",
        guardrails=[],
        latency_ms=3000,
    )
    result.model = "claude-haiku-4-5-20251001"
    result.provider = "anthropic"

    metrics = calculator.calculate(
        original_idea="test",
        result=result,
        impact_data=None,  # No impact data
    )

    # Impact metrics should default to zeros
    assert metrics.impact.copy_count == 0
    assert metrics.impact.regeneration_count == 0
    assert metrics.impact.reuse_count == 0


def test_metrics_calculator_with_custom_id():
    """Test metrics calculation with custom prompt ID."""
    calculator = PromptMetricsCalculator()

    result = PromptImprovementResult(
        improved_prompt="test",
        role="Test",
        directive="test",
        framework="chain-of-thought",
        guardrails=[],
        latency_ms=3000,
    )
    result.model = "claude-haiku-4-5-20251001"
    result.provider = "anthropic"

    metrics = calculator.calculate(
        original_idea="test",
        result=result,
        prompt_id="custom-id-123",
    )

    assert metrics.prompt_id == "custom-id-123"


def test_metrics_calculator_invalid_framework():
    """Test metrics calculation with invalid framework (should default)."""
    calculator = PromptMetricsCalculator()

    result = PromptImprovementResult(
        improved_prompt="test",
        role="Test",
        directive="test",
        framework="invalid-framework",  # Invalid
        guardrails=[],
        latency_ms=3000,
    )
    result.model = "claude-haiku-4-5-20251001"
    result.provider = "anthropic"

    metrics = calculator.calculate(
        original_idea="test",
        result=result,
    )

    # Should default to CHAIN_OF_THOUGHT
    assert metrics.framework == FrameworkType.CHAIN_OF_THOUGHT


def test_metrics_calculator_from_history():
    """Test calculate_from_history method for legacy format."""
    calculator = PromptMetricsCalculator()

    metrics = calculator.calculate_from_history(
        original_idea="test idea",
        context="test context",
        improved_prompt="# Role: Test\nTest prompt.",
        role="Test",
        directive="Test directive",
        framework="chain-of-thought",
        guardrails=["guard1", "guard2"],
        backend="few-shot",
        model="claude-haiku-4-5-20251001",
        provider="anthropic",
        latency_ms=4000,
        confidence=0.95,
        impact_data=ImpactData(copy_count=3),
    )

    assert isinstance(metrics, PromptMetrics)
    # Note: provider comes from result.model, not the provider parameter
    assert metrics.model == "claude-haiku-4-5-20251001"
    assert metrics.backend == "few-shot"
    assert metrics.performance.latency_ms == 4000


def test_metrics_calculator_singleton():
    """Test that get_calculator returns singleton instance."""
    from hemdov.domain.metrics.evaluators import get_calculator

    calc1 = get_calculator()
    calc2 = get_calculator()

    assert calc1 is calc2


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

def test_end_to_end_calculation():
    """Test complete calculation flow from input to metrics."""
    calculator = PromptMetricsCalculator()

    result = PromptImprovementResult(
        improved_prompt="""# Role: Expert Python Developer

## Task
Create a data analysis script with the following requirements:

## Steps
1. Load CSV file using pandas
2. Calculate summary statistics
3. Generate visualizations with matplotlib
4. Export results to PDF

## Constraints
- Handle missing values
- Use type hints
- Include docstrings
- Maximum 100 lines of code
""",
        role="Expert Python Developer",
        directive="Create a data analysis script",
        framework="chain-of-thought",
        guardrails=["Handle missing values", "Use type hints", "Include docstrings"],
        reasoning="Structured prompt provides clear guidance",
        confidence=0.95,
        latency_ms=7500,
    )
    result.model = "claude-haiku-4-5-20251001"
    result.provider = "anthropic"

    metrics = calculator.calculate(
        original_idea="Create a Python script to analyze data",
        result=result,
        impact_data=ImpactData(
            copy_count=8,
            regeneration_count=0,
            feedback_score=5,
            reuse_count=4,
        ),
    )

    # Verify all dimensions are calculated
    assert metrics.quality.composite_score > 0.7  # High quality
    assert metrics.performance.performance_score > 0.6  # Good performance
    assert metrics.impact.impact_score > 0.7  # High impact
    assert metrics.overall_score > 0.6  # Acceptable overall
    assert metrics.is_acceptable is True

    # Verify quality breakdown
    assert metrics.quality.guardrails_count == 3
    assert metrics.quality.has_required_structure is True

    # Verify performance
    assert metrics.performance.latency_ms == 7500
    assert metrics.performance.cost_usd > 0

    # Verify impact
    assert metrics.impact.success_rate >= 0.9
    assert metrics.impact.feedback_score == 5
