"""Tests for ExampleGenerator."""

from scripts.legacy_curation.models import Component, Domain
from scripts.synthetic_examples.generators.example_generator import ExampleGenerator


def test_generate_example_missing_required_fields():
    """Should handle component missing required fields"""
    generator = ExampleGenerator()

    incomplete_component = Component(
        source_file="test.md",
        domain=Domain.SOFTDEV,
        role="",  # Missing
        directive="Build system",
        framework="Chain-of-Thought",
        guardrails=[],
        confidence=0.8,
    )

    result = generator.generate_single_example(incomplete_component)
    assert "{role}" not in result["example"]
    assert "{directive}" not in result["example"]
    assert result["metadata"]["source_component_id"] == "test.md:Domain.SOFTDEV"


def test_generate_example_with_seed():
    """Should produce consistent results with same seed"""
    import random as r

    # Reset global random state before test
    r.seed(0)

    generator1 = ExampleGenerator(seed=42)
    result1 = generator1.generate_single_example(
        Component(
            source_file="test.md",
            domain=Domain.SOFTDEV,
            role="Software Engineer",
            directive="Build scalable systems",
            framework="Chain-of-Thought",
            guardrails=[],
            confidence=0.9,
        )
    )

    r.seed(0)
    generator2 = ExampleGenerator(seed=42)
    result2 = generator2.generate_single_example(
        Component(
            source_file="test.md",
            domain=Domain.SOFTDEV,
            role="Software Engineer",
            directive="Build scalable systems",
            framework="Chain-of-Thought",
            guardrails=[],
            confidence=0.9,
        )
    )

    assert result1["example"] == result2["example"]


def test_generate_batch():
    """Should generate multiple examples per component"""
    generator = ExampleGenerator(seed=42)

    component = Component(
        source_file="test.md",
        domain=Domain.SOFTDEV,
        role="Architect",
        directive="Design systems",
        framework="Chain-of-Thought",
        guardrails=[],
        confidence=0.8,
    )

    results = generator.generate_batch([component], examples_per_component=2)

    assert len(results) == 2
    assert all("{role}" not in r["example"] for r in results)


def test_apply_variations():
    """Should apply variations correctly"""
    generator = ExampleGenerator()

    component = Component(
        source_file="test.md",
        domain=Domain.SOFTDEV,
        role="Developer",
        directive="Write clean code",
        framework="TDD",
        guardrails=[],
        confidence=0.8,
    )

    base = "You are a Developer."
    expanded = generator._apply_variation(base, "expand", component)
    simplified = generator._apply_variation(base, "simplify", component)
    with_context = generator._apply_variation(base, "add_context", component)

    assert "highly experienced" in expanded
    assert simplified == "You are a Developer."
    # Should include context text with explanations
    assert "Provide detailed explanations" in with_context


def test_different_domains():
    """Should handle different domains"""
    generator = ExampleGenerator()

    for domain in [Domain.SOFTDEV, Domain.PRODUCTIVITY, Domain.AIML, Domain.SECURITY]:
        component = Component(
            source_file="test.md",
            domain=domain,
            role="Expert",
            directive="Test directive",
            framework="Test framework",
            guardrails=[],
            confidence=0.8,
        )

        result = generator.generate_single_example(component)
        assert result is not None
        assert "example" in result
        assert "metadata" in result
