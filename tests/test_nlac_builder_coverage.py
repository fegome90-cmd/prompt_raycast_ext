"""
Coverage tests for NLaCBuilder.

This file provides comprehensive coverage tests for the domain service
located at hemdov/domain/services/nlac_builder.py.

Tests cover:
- Full prompt flow (end-to-end build pipeline)
- RaR template for complex inputs
- Simple template for basic inputs
- Constraint builder
- Strategy metadata builder
"""

import pytest

# Component not exposed - kept for future use (see PLAN-2026-0001)
pytestmark = pytest.mark.skip(
    reason="Component not exposed - kept for future use (see PLAN-2026-0001)"
)
from hemdov.domain.dto.nlac_models import NLaCRequest, IntentType, NLaCInputs
from hemdov.domain.services.nlac_builder import NLaCBuilder
from hemdov.domain.services.complexity_analyzer import ComplexityLevel


class TestNLaCBuilderCoverage:
    """Comprehensive coverage tests for NLaCBuilder domain service."""

    @pytest.fixture
    def builder(self):
        """Create builder instance without KNN provider."""
        return NLaCBuilder(knn_provider=None)

    # ========================================================================
    # FULL PROMPT FLOW (End-to-End)
    # ========================================================================

    def test_build_full_prompt_flow(self, builder):
        """
        Test the complete build pipeline from request to PromptObject.

        Verifies the 8-step pipeline:
        1. Classify intent
        2. Analyze complexity
        3. Select strategy
        4. Inject role
        5. Fetch KNN examples (skipped in this test)
        6. Build template (simple or RaR)
        7. Compile metadata
        8. Build constraints
        """
        # Simple request - should use simple template
        simple_request = NLaCRequest(
            idea="Create a hello world function",
            context="In Python",
            mode="nlac"
        )

        result = builder.build(simple_request)

        # Verify PromptObject structure
        assert result.id is not None
        assert result.version == "1.0.0"
        assert result.intent_type == IntentType.GENERATE
        assert result.template is not None
        assert len(result.template) > 0
        assert result.strategy_meta is not None
        assert result.constraints is not None
        assert result.created_at is not None
        assert result.updated_at is not None

        # Verify strategy metadata
        assert "strategy" in result.strategy_meta
        assert "complexity" in result.strategy_meta
        assert "intent" in result.strategy_meta
        assert "role" in result.strategy_meta
        assert "rar_used" in result.strategy_meta
        assert result.strategy_meta["rar_used"] is False  # Simple = no RaR

        # Verify constraints
        assert "max_tokens" in result.constraints

    # ========================================================================
    # RAR TEMPLATE FOR COMPLEX INPUTS
    # ========================================================================

    def test_rar_template_for_complex(self, builder):
        """
        Test RaR (Rephrase and Respond) template structure for complex inputs.

        RaR template should include:
        - Role injection
        - Original request
        - Rephrased understanding
        - Task section
        - Requirements section
        """
        # Complex request - should trigger RaR template
        complex_request = NLaCRequest(
            idea="Design a microservices architecture with components, repositories, "
                  "adapters, integration pipeline, API, using framework patterns",
            context="For scalable e-commerce platform with quality metrics",
            mode="nlac"
        )

        result = builder.build(complex_request)

        # Verify RaR was used
        assert result.strategy_meta["rar_used"] is True
        assert result.strategy_meta["complexity"] == "complex"

        # Verify RaR template structure
        template = result.template
        assert "# Role" in template
        assert "You are a" in template
        assert "# Understanding the Request" in template
        assert "First, let me rephrase" in template
        assert "**Original Request:**" in template
        assert "**Rephrased Understanding:**" in template
        assert "# Task" in template
        assert "## Requirements" in template

        # Verify context is included
        assert "Additional Context" in template or "Context" in template

    # ========================================================================
    # SIMPLE TEMPLATE FOR BASIC INPUTS
    # ========================================================================

    def test_simple_template_for_basic(self, builder):
        """
        Test simple template structure for basic inputs.

        Simple template should include:
        - Role injection
        - Task section with idea
        - Context (if provided)
        - No RaR section
        """
        # Simple request - should use simple template
        simple_request = NLaCRequest(
            idea="Create a hello world function",
            context="In Python",
            mode="nlac"
        )

        result = builder.build(simple_request)

        # Verify simple template was used
        assert result.strategy_meta["rar_used"] is False
        assert result.strategy_meta["complexity"] == "simple"

        # Verify simple template structure
        template = result.template
        assert "# Role" in template
        assert "You are a" in template
        assert "# Task" in template
        assert simple_request.idea in template

        # Verify context is included
        assert "# Context" in template
        assert simple_request.context in template

        # Verify NO RaR elements
        assert "Understanding the Request" not in template
        assert "Rephrased Understanding" not in template

    # ========================================================================
    # CONSTRAINT BUILDER
    # ========================================================================

    def test_constraint_builder(self, builder):
        """
        Test that constraints are built correctly based on complexity.

        Constraints should include:
        - max_tokens (varies by complexity)
        - format (if target_language specified)
        - include_examples (false for simple, true otherwise)
        - include_explanation (true only for complex)
        """
        # Test SIMPLE constraints
        simple_request = NLaCRequest(
            idea="Simple task",
            context="",
            mode="nlac"
        )
        simple_result = builder.build(simple_request)

        assert simple_result.constraints["max_tokens"] == 500
        assert simple_result.constraints["include_examples"] is False
        assert simple_result.constraints["include_explanation"] is False

        # Test MODERATE constraints
        moderate_request = NLaCRequest(
            idea="Create a moderately complex function with validation " * 3,
            context="",
            mode="nlac"
        )
        moderate_result = builder.build(moderate_request)

        assert moderate_result.constraints["max_tokens"] == 1000
        assert moderate_result.constraints["include_examples"] is True
        assert moderate_result.constraints["include_explanation"] is False

        # Test COMPLEX constraints
        complex_request = NLaCRequest(
            idea="Design a system architecture " * 20,
            context="",
            mode="nlac"
        )
        complex_result = builder.build(complex_request)

        assert complex_result.constraints["max_tokens"] == 2000
        assert complex_result.constraints["include_examples"] is True
        assert complex_result.constraints["include_explanation"] is True

        # Test format constraint with target_language
        request_with_language = NLaCRequest(
            idea="Create a function",
            context="",
            mode="nlac",
            inputs=NLaCInputs(target_language="Python")
        )
        result_with_language = builder.build(request_with_language)

        assert "format" in result_with_language.constraints
        assert "Python" in result_with_language.constraints["format"]

    # ========================================================================
    # STRATEGY METADATA BUILDER
    # ========================================================================

    def test_strategy_metadata_builder(self, builder):
        """
        Test that strategy metadata is built correctly.

        Strategy metadata should include:
        - strategy (selected strategy name)
        - complexity (complexity level)
        - intent (intent string)
        - role (injected role)
        - rar_used (boolean)
        - fewshot_count (number of examples)
        - knn_enabled (boolean)
        - knn_failed (boolean)
        - knn_error (error details if any)
        """
        request = NLaCRequest(
            idea="Fix this bug",
            context="",
            mode="nlac"
        )

        result = builder.build(request)
        meta = result.strategy_meta

        # Verify all required fields
        assert "strategy" in meta
        assert "complexity" in meta
        assert "intent" in meta
        assert "role" in meta
        assert "rar_used" in meta
        assert "fewshot_count" in meta
        assert "knn_enabled" in meta
        assert "knn_failed" in meta
        assert "knn_error" in meta

        # Verify values are correct
        assert meta["strategy"] is not None
        assert meta["complexity"] in ["simple", "moderate", "complex"]
        assert meta["intent"] in ["generate", "debug", "refactor", "explain"]
        assert meta["role"] is not None
        assert isinstance(meta["rar_used"], bool)
        assert isinstance(meta["fewshot_count"], int)
        assert isinstance(meta["knn_enabled"], bool)
        assert isinstance(meta["knn_failed"], bool)

        # With no KNN provider
        assert meta["knn_enabled"] is False
        assert meta["fewshot_count"] == 0

    # ========================================================================
    # ROLE INJECTION BY INTENT AND COMPLEXITY
    # ========================================================================

    def test_role_injection_by_intent_and_complexity(self, builder):
        """
        Test that roles are injected correctly based on intent + complexity.

        Roles should escalate with complexity:
        - DEBUG: Code Debugger → Senior Debugging Specialist → Expert Systems Diagnostics Engineer
        - REFACTOR: Code Reviewer → Software Architect
        - EXPLAIN: Technical Educator (constant)
        - GENERATE: Developer → Senior Developer → Software Engineer
        """
        # Simple debug → Code Debugger
        simple_debug = NLaCRequest(idea="Fix bug", context="", mode="nlac")
        assert builder.build(simple_debug).strategy_meta["role"] == "Code Debugger"

        # Moderate debug → Senior Debugging Specialist
        moderate_debug = NLaCRequest(
            idea="Fix this bug, add validation, handle errors, and resolve the issues",
            context="",
            mode="nlac"
        )
        assert builder.build(moderate_debug).strategy_meta["role"] == "Senior Debugging Specialist"

        # Complex debug → Expert Systems Diagnostics Engineer
        complex_debug = NLaCRequest(
            idea="Fix bug " * 100,
            context="",
            mode="nlac"
        )
        assert builder.build(complex_debug).strategy_meta["role"] == "Expert Systems Diagnostics Engineer"

        # Simple refactor → Code Reviewer
        simple_refactor = NLaCRequest(idea="Optimize code", context="", mode="nlac")
        assert builder.build(simple_refactor).strategy_meta["role"] == "Code Reviewer"

        # Complex refactor → Software Architect
        complex_refactor = NLaCRequest(
            idea="Optimize " * 100,
            context="",
            mode="nlac"
        )
        assert builder.build(complex_refactor).strategy_meta["role"] == "Software Architect"

        # Explain → Technical Educator (all complexities)
        explain = NLaCRequest(idea="Explain how it works", context="", mode="nlac")
        assert builder.build(explain).strategy_meta["role"] == "Technical Educator"

        # Simple generate → Developer
        simple_generate = NLaCRequest(idea="Create function", context="", mode="nlac")
        assert builder.build(simple_generate).strategy_meta["role"] == "Developer"

        # Moderate generate → Senior Developer
        moderate_generate = NLaCRequest(
            idea="Create a function with validation, add input checks, include tests, and provide documentation",
            context="",
            mode="nlac"
        )
        assert builder.build(moderate_generate).strategy_meta["role"] == "Senior Developer"

        # Complex generate → Software Engineer
        complex_generate = NLaCRequest(
            idea="Create function " * 100,
            context="",
            mode="nlac"
        )
        assert builder.build(complex_generate).strategy_meta["role"] == "Software Engineer"

    # ========================================================================
    # STRATEGY SELECTION BY INTENT AND COMPLEXITY
    # ========================================================================

    def test_strategy_selection_by_intent_and_complexity(self, builder):
        """
        Test that strategies are selected correctly based on intent + complexity.

        Strategy mapping:
        - DEBUG: simple_debug → moderate_debug → complex_debug
        - REFACTOR: simple_refactor → complex_refactor
        - EXPLAIN: explain (constant)
        - GENERATE: simple → moderate → complex
        """
        # Simple debug → simple_debug
        simple_debug = NLaCRequest(idea="Fix bug", context="", mode="nlac")
        assert builder.build(simple_debug).strategy_meta["strategy"] == "simple_debug"

        # Moderate debug → moderate_debug
        moderate_debug = NLaCRequest(
            idea="Fix this bug, add validation, handle errors, and resolve the issues",
            context="",
            mode="nlac"
        )
        assert builder.build(moderate_debug).strategy_meta["strategy"] == "moderate_debug"

        # Complex debug → complex_debug
        complex_debug = NLaCRequest(
            idea="Fix bug " * 100,
            context="",
            mode="nlac"
        )
        assert builder.build(complex_debug).strategy_meta["strategy"] == "complex_debug"

        # Simple refactor → simple_refactor
        simple_refactor = NLaCRequest(idea="Optimize", context="", mode="nlac")
        assert builder.build(simple_refactor).strategy_meta["strategy"] == "simple_refactor"

        # Complex refactor → complex_refactor
        complex_refactor = NLaCRequest(
            idea="Optimize " * 100,
            context="",
            mode="nlac"
        )
        assert builder.build(complex_refactor).strategy_meta["strategy"] == "complex_refactor"

        # Explain → explain
        explain = NLaCRequest(idea="Explain", context="", mode="nlac")
        assert builder.build(explain).strategy_meta["strategy"] == "explain"

        # Generate → complexity value
        simple_generate = NLaCRequest(idea="Create", context="", mode="nlac")
        assert builder.build(simple_generate).strategy_meta["strategy"] == "simple"

        moderate_generate = NLaCRequest(
            idea="Create a function with validation, add input checks, include tests, and provide documentation",
            context="",
            mode="nlac"
        )
        assert builder.build(moderate_generate).strategy_meta["strategy"] == "moderate"

        complex_generate = NLaCRequest(
            idea="Create " * 100,
            context="",
            mode="nlac"
        )
        assert builder.build(complex_generate).strategy_meta["strategy"] == "complex"

    # ========================================================================
    # STRUCTURED INPUTS HANDLING
    # ========================================================================

    def test_structured_inputs_handling(self, builder):
        """
        Test that structured inputs (code_snippet, error_log, target_language)
        are correctly included in the template.
        """
        # Request with all structured inputs
        request = NLaCRequest(
            idea="Fix this error",
            context="In production",
            mode="nlac",
            inputs=NLaCInputs(
                code_snippet="def foo():\n    return 1/0",
                error_log="ZeroDivisionError: division by zero",
                target_language="Python",
                target_framework="FastAPI"
            )
        )

        result = builder.build(request)

        # Verify structured inputs are in template
        template = result.template
        assert "def foo():" in template
        assert "ZeroDivisionError" in template
        assert "Python" in template
        assert "# Code" in template or "Code to Work With" in template
        assert "# Error" in template or "Error Information" in template
