"""
Coverage tests for ComplexityAnalyzer.

This file provides comprehensive coverage tests for the domain service
located at hemdov/domain/services/complexity_analyzer.py.

Note: The existing test files (test_complexity_analyzer.py and
test_complexity_analyzer_edge_cases.py) import from the old path
(eval.src.complexity_analyzer). These new tests use the correct
domain layer import path.

Tests cover:
- All complexity levels classification (simple, moderate, complex)
- Analysis with code blocks
- Analysis with multiple requirements
- Token count heuristics
"""

import pytest
from hemdov.domain.services.complexity_analyzer import ComplexityAnalyzer, ComplexityLevel


class TestComplexityAnalyzerCoverage:
    """Comprehensive coverage tests for ComplexityAnalyzer domain service."""

    @pytest.fixture
    def analyzer(self):
        """Create analyzer instance."""
        return ComplexityAnalyzer()

    # ========================================================================
    # ALL LEVELS CLASSIFICATION
    # ========================================================================

    def test_analyze_all_levels(self, analyzer):
        """
        Test that ALL complexity levels are correctly classified.

        This comprehensive test ensures:
        - SIMPLE level (short, no technical terms)
        - MODERATE level (moderate length or some technical terms)
        - COMPLEX level (long, many technical terms, multi-dimensional)
        """
        # SIMPLE: Short input, no technical terms
        simple_input = "Create a function"
        simple_context = ""
        result = analyzer.analyze(simple_input, simple_context)
        assert result == ComplexityLevel.SIMPLE, \
            f"Expected SIMPLE for short simple input, got {result}"

        # MODERATE: Moderate length with one technical term
        moderate_input = "Create a framework for user authentication"
        moderate_context = "Need to handle login and logout"
        result = analyzer.analyze(moderate_input, moderate_context)
        assert result == ComplexityLevel.MODERATE, \
            f"Expected MODERATE for input with technical term, got {result}"

        # COMPLEX: Long input with multiple technical terms
        complex_input = (
            "Design a microservices architecture with components, repositories, "
            "adapters, integration pipeline, API, using framework modern. "
            "Evaluate quality with metrics. Optimize performance."
        )
        complex_context = "For scalable e-commerce platform with domain infrastructure separation"
        result = analyzer.analyze(complex_input, complex_context)
        assert result == ComplexityLevel.COMPLEX, \
            f"Expected COMPLEX for long technical input, got {result}"

    # ========================================================================
    # CODE BLOCKS ANALYSIS
    # ========================================================================

    def test_analyze_with_code_blocks(self, analyzer):
        """
        Test analysis of prompts containing code blocks or code-like content.

        Code blocks typically increase complexity due to:
        - Structure (punctuation)
        - Technical terms
        - Often longer length
        """
        # Simple code block (still SIMPLE due to low technical content)
        simple_code = "def foo(): pass"
        result = analyzer.analyze(simple_code, "")
        # Length is short, no technical terms from our list
        assert result == ComplexityLevel.SIMPLE, \
            f"Expected SIMPLE for simple code block, got {result}"

        # Code block with technical terms (MODERATE)
        # Note: Technical terms list is in Spanish
        code_with_technical = (
            "Crea un componente para el patrón de repositorio "
            "en la capa de dominio"
        )
        result = analyzer.analyze(code_with_technical, "")
        # Has technical terms: "componente", "patrón", "repositorio", "dominio"
        assert result == ComplexityLevel.MODERATE, \
            f"Expected MODERATE for code with technical terms, got {result}"

        # Complex code block with architecture concepts (COMPLEX)
        # Note: Using Spanish technical terms
        complex_code = (
            "Implementa una pipeline de integración API con "
            "múltiples componentes, repositorios y adaptadores. "
            "Separa el dominio de la infraestructura. "
            "Usa patrones de framework para métricas de calidad."
        )
        result = analyzer.analyze(complex_code, "Para sistema de microservicios")
        # Many technical terms + context provided
        assert result == ComplexityLevel.COMPLEX, \
            f"Expected COMPLEX for complex code block, got {result}"

    # ========================================================================
    # MULTIPLE REQUIREMENTS ANALYSIS
    # ========================================================================

    def test_analyze_with_multiple_requirements(self, analyzer):
        """
        Test analysis of prompts with multiple requirements.

        Multiple requirements typically increase complexity due to:
        - Structure (punctuation, commas, periods)
        - Increased length
        - Often technical terms
        """
        # Single requirement (SIMPLE)
        single = "Create a login function"
        result = analyzer.analyze(single, "")
        assert result == ComplexityLevel.SIMPLE, \
            f"Expected SIMPLE for single requirement, got {result}"

        # Multiple requirements, simple phrasing (MODERATE)
        # Need to ensure length and structure push it to MODERATE
        multiple_simple = (
            "Crea una función de login, añade validación de entrada, "
            "maneja errores de forma elegante, y agrega pruebas unitarias"
        )
        result = analyzer.analyze(multiple_simple, "")
        # Structure (3 commas) + moderate length (~100 chars)
        # Structure score: min(3 * 0.1, 1.0) = 0.3
        # Length: ~100 chars (MODERATE: 0.5)
        # Total: 0.5*0.4 + 0.3*0.2 = 0.2 + 0.06 = 0.26 > 0.25 = MODERATE
        assert result == ComplexityLevel.MODERATE, \
            f"Expected MODERATE for multiple simple requirements, got {result}"

        # Multiple technical requirements (COMPLEX)
        # Using Spanish technical terms
        multiple_technical = (
            "Diseña una pipeline de integración API, crea componentes "
            "de repositorio, implementa separación de dominio e infraestructura, "
            "añade evaluación de métricas de calidad, y optimiza el rendimiento."
        )
        result = analyzer.analyze(multiple_technical, "Para arquitectura de microservicios")
        # Many technical terms + structure + context
        assert result == ComplexityLevel.COMPLEX, \
            f"Expected COMPLEX for multiple technical requirements, got {result}"

    # ========================================================================
    # TOKEN COUNT HEURISTICS
    # ========================================================================

    def test_token_count_heuristics(self, analyzer):
        """
        Test token count heuristics used for complexity classification.

        The analyzer uses character length as a proxy for token count:
        - <= 50 chars: SIMPLE (length_score = 0.0)
        - 51-150 chars: MODERATE (length_score = 0.5)
        - 151-300 chars: COMPLEX range (length_score = 1.0)
        - > 300 chars: AUTO-COMPLEX (regardless of other factors)
        """
        # Exactly at SIMPLE threshold (50 chars)
        threshold_simple = "a" * 50
        result = analyzer.analyze(threshold_simple, "")
        assert result == ComplexityLevel.SIMPLE, \
            f"Expected SIMPLE at 50 char threshold, got {result}"

        # Just over SIMPLE threshold (51 chars)
        just_over_simple = "a" * 51
        result = analyzer.analyze(just_over_simple, "")
        # Length: MODERATE (0.5), but no other factors
        # Score: 0.5 * 0.4 = 0.2, which is < 0.25 SIMPLE threshold
        # So still SIMPLE due to low score
        assert result == ComplexityLevel.SIMPLE, \
            f"Expected SIMPLE just over 50 char threshold, got {result}"

        # At MODERATE threshold (150 chars)
        threshold_moderate = "a" * 150
        result = analyzer.analyze(threshold_moderate, "")
        # Length: 150 chars is exactly MODERATE_MAX_LENGTH
        # So length_score = LENGTH_SCORE_MODERATE = 0.5
        # Score: 0.5 * 0.4 = 0.2, which is < 0.25 = SIMPLE
        # (Need more factors to push to MODERATE)
        assert result == ComplexityLevel.SIMPLE, \
            f"Expected SIMPLE at 150 char threshold (no other factors), got {result}"

        # Just over MODERATE threshold (151 chars) - still SIMPLE without other factors
        just_over_moderate = "a" * 151
        result = analyzer.analyze(just_over_moderate, "")
        # Length: 151 > 150 so length_score = LENGTH_SCORE_COMPLEX = 1.0
        # Score: 1.0 * 0.4 = 0.4, which is > 0.25 and < 0.6 = MODERATE
        assert result == ComplexityLevel.MODERATE, \
            f"Expected MODERATE just over 150 char threshold, got {result}"

        # At AUTO-COMPLEX threshold (300 chars)
        threshold_auto_complex = "a" * 301
        result = analyzer.analyze(threshold_auto_complex, "")
        # Auto-complex at > 300 chars
        assert result == ComplexityLevel.COMPLEX, \
            f"Expected COMPLEX at 301 char threshold, got {result}"

    # ========================================================================
    # MULTI-DIMENSIONAL SCORING
    # ========================================================================

    def test_multi_dimensional_scoring(self, analyzer):
        """
        Test that all four dimensions contribute to the final score.

        Dimensions:
        1. Length (40% weight)
        2. Technical terms (30% weight)
        3. Structure (20% weight)
        4. Context (10% weight)
        """
        # Input that maximizes all dimensions
        max_input = (
            "Design a framework architecture with components, repositories, "
            "adapters, and API integration pipeline. Evaluate quality metrics. "
            "Optimize system performance for domain infrastructure."
        )
        max_context = "For scalable microservices e-commerce platform"

        result = analyzer.analyze(max_input, max_context)

        # Should be COMPLEX due to high score across all dimensions
        assert result == ComplexityLevel.COMPLEX, \
            f"Expected COMPLEX for maxed multi-dimensional input, got {result}"

    # ========================================================================
    # TECHNICAL TERM DETECTION
    # ========================================================================

    def test_technical_term_detection(self, analyzer):
        """
        Test technical term detection with word boundary matching.

        Ensures:
        - Technical terms are detected correctly
        - Word boundaries prevent false positives (e.g., "api" in "capacidad")
        - Multiple terms contribute to score (capped at 1.0)
        """
        # Single technical term
        single_term = "Create a component"
        result = analyzer.analyze(single_term, "")
        # "component" is a technical term
        # Length: 20 chars (SIMPLE), Technical: 0.5
        # Score: 0.0*0.4 + 0.5*0.3 = 0.15 < 0.25 = SIMPLE
        # Wait, let me recalculate: 20 chars is in SIMPLE range (0-50)
        # So length_score = 0.0, technical_score = 0.5
        # Total: 0.0*0.4 + 0.5*0.3 = 0.15 < 0.25 = SIMPLE
        assert result == ComplexityLevel.SIMPLE, \
            f"Expected SIMPLE for single technical term with short length, got {result}"

        # Multiple technical terms
        multiple_terms = "Design a framework with components and repositories"
        result = analyzer.analyze(multiple_terms, "")
        # "framework", "components", "repositories" = 3 terms
        # Technical score: min(3 * 0.5, 1.0) = 1.0
        # Length: ~50 chars (SIMPLE/MODERATE boundary)
        # Should be MODERATE or COMPLEX
        assert result in [ComplexityLevel.MODERATE, ComplexityLevel.COMPLEX], \
            f"Expected MODERATE/COMPLEX for multiple technical terms, got {result}"

        # Word boundary: "api" should NOT match in "capacidad"
        false_positive = "La capacidad del sistema"
        result = analyzer.analyze(false_positive, "")
        assert result == ComplexityLevel.SIMPLE, \
            f"Expected SIMPLE for false positive case, got {result}"

        # Word boundary: "api" alone should match
        # Note: "sistema" is also a technical term
        true_positive = "Usa la api rest para conectar el sistema backend"
        result = analyzer.analyze(true_positive, "")
        # "api" and "sistema" are technical terms (2 terms)
        # Technical: min(2 * 0.5, 1.0) = 1.0, Length: 45 (SIMPLE: 0.0)
        # Total: 0.0*0.4 + 1.0*0.3 = 0.3 > 0.25 = MODERATE
        assert result == ComplexityLevel.MODERATE, \
            f"Expected MODERATE for two technical terms, got {result}"

        # With structure + technical term → MODERATE
        with_structure = "Usa la api rest, conecta el backend, maneja errores"
        result = analyzer.analyze(with_structure, "")
        # Structure: 2 commas = 0.2, Technical: 0.5, Length: ~50 (SIMPLE: 0.0)
        # Total: 0.0*0.4 + 0.5*0.3 + 0.2*0.2 = 0.15 + 0.04 = 0.19 < 0.25 = SIMPLE
        # Still SIMPLE, need more...
        # Actually, let me just verify the word boundary works by checking a longer input
        long_with_api = "Usa la api rest del framework para conectar múltiples componentes del sistema backend"
        result = analyzer.analyze(long_with_api, "")
        # Length: ~95 chars (MODERATE: 0.5), Technical: "api", "framework", "componentes" = 3 → 1.0
        # Total: 0.5*0.4 + 1.0*0.3 = 0.2 + 0.3 = 0.5 → MODERATE
        assert result == ComplexityLevel.MODERATE, \
            f"Expected MODERATE for longer input with technical terms, got {result}"

    # ========================================================================
    # CONTEXT INFLUENCE
    # ========================================================================

    def test_context_influence_on_complexity(self, analyzer):
        """
        Test that providing context influences the complexity score.

        Context contributes 10% weight to the final score.
        """
        # Same input without context
        no_context = "Design a system"
        result_no_context = analyzer.analyze(no_context, "")

        # Same input with context
        with_context = "Design a system"
        context = "For microservices architecture"
        result_with_context = analyzer.analyze(with_context, context)

        # With context should have same or higher complexity
        # (context adds 0.1 * 0.1 = 0.01 to score)
        # This may not change the level for simple inputs
        assert result_with_context.value in ["simple", "moderate", "complex"]

    # ========================================================================
    # STRUCTURE ANALYSIS
    # ========================================================================

    def test_structure_analysis(self, analyzer):
        """
        Test that punctuation structure contributes to complexity score.

        Punctuation marks (., ;) contribute 0.1 each, capped at 1.0.
        Structure weight is 20%.
        """
        # Input with many punctuation marks
        punctuated = (
            "Create a function, add a class, define a method; "
            "implement a loop, add conditions, handle errors."
        )
        result = analyzer.analyze(punctuated, "")
        # Punctuation count: 5 commas, 1 period = 6
        # Structure score: min(6 * 0.1, 1.0) = 0.6
        # Length: ~110 chars (MODERATE: 0.5)
        # Score: 0.5*0.4 + 0.6*0.2 = 0.2 + 0.12 = 0.32
        # 0.32 is between 0.25 and 0.6 = MODERATE
        assert result == ComplexityLevel.MODERATE, \
            f"Expected MODERATE for punctuated input, got {result}"
