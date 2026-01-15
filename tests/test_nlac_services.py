"""
Tests for NLaC Domain Services.

Covers:
- IntentClassifier
- NLaCBuilder
- OPROOptimizer
- PromptValidator
"""

from datetime import UTC, datetime

import pytest

from hemdov.domain.dto.nlac_models import (
    IntentType,
    NLaCInputs,
    NLaCRequest,
    OPROIteration,
    PromptObject,
)
from hemdov.domain.services.intent_classifier import IntentClassifier
from hemdov.domain.services.nlac_builder import NLaCBuilder
from hemdov.domain.services.oprop_optimizer import OPROOptimizer
from hemdov.domain.services.prompt_validator import PromptValidator


class TestIntentClassifier:
    """Test IntentClassifier service."""

    @pytest.fixture
    def classifier(self):
        return IntentClassifier()

    def test_classify_debug_intent_with_code_and_error(self, classifier):
        """Debug intent when code_snippet + error_log present."""
        request = NLaCRequest(
            idea="Fix this bug",
            context="Something is broken",
            inputs=NLaCInputs(
                code_snippet="def foo():\n    return 1/0",
                error_log="ZeroDivisionError: division by zero"
            )
        )

        result = classifier.classify(request)
        assert result == classifier.INTENT_DEBUG

    def test_classify_explain_intent_keywords(self, classifier):
        """Explain intent detected by keywords."""
        request = NLaCRequest(
            idea="Explain how this works",
            context="Need to understand the logic"
        )

        result = classifier.classify(request)
        assert result == classifier.INTENT_EXPLAIN

    def test_classify_refactor_intent_keywords(self, classifier):
        """Refactor intent detected by keywords."""
        request = NLaCRequest(
            idea="Refactor this code for better maintainability",
            context="Code is messy"
        )

        result = classifier.classify(request)
        assert result.startswith("refactor")

    def test_classify_generate_intent_default(self, classifier):
        """Generate intent as default."""
        request = NLaCRequest(
            idea="Create a new function",
            context="Need to add feature X"
        )

        result = classifier.classify(request)
        assert result == classifier.INTENT_GENERATE

    def test_get_intent_type_mapping(self, classifier):
        """IntentType enum mapping."""
        assert classifier.get_intent_type(classifier.INTENT_GENERATE) == IntentType.GENERATE
        assert classifier.get_intent_type(classifier.INTENT_DEBUG) == IntentType.DEBUG
        assert classifier.get_intent_type(classifier.INTENT_EXPLAIN) == IntentType.EXPLAIN
        assert classifier.get_intent_type("refactor_simple") == IntentType.REFACTOR


class TestNLaCBuilder:
    """Test NLaCBuilder service."""

    @pytest.fixture
    def builder(self):
        return NLaCBuilder()

    def test_build_simple_prompt(self, builder):
        """Build simple PromptObject without RaR."""
        request = NLaCRequest(
            idea="Create a hello world function",
            context="In Python",
            mode="nlac"
        )

        result = builder.build(request)

        assert isinstance(result, PromptObject)
        assert result.template
        assert "hello world" in result.template.lower()
        assert result.strategy_meta["strategy"] in ["simple", "moderate", "complex"]
        assert result.constraints["max_tokens"] > 0
        assert result.intent_type == IntentType.GENERATE

    def test_build_debug_prompt_with_role(self, builder):
        """Debug prompt gets appropriate role."""
        request = NLaCRequest(
            idea="Fix this error",
            context="Not working",
            inputs=NLaCInputs(
                code_snippet="def test(): pass",
                error_log="Error occurred"
            ),
            mode="nlac"
        )

        result = builder.build(request)

        assert result.intent_type == IntentType.DEBUG
        assert "debugg" in result.strategy_meta["role"].lower()

    def test_build_explain_prompt_with_role(self, builder):
        """Explain prompt gets educator role."""
        request = NLaCRequest(
            idea="Explain recursion",
            context="Need to understand",
            mode="nlac"
        )

        result = builder.build(request)

        assert result.intent_type == IntentType.EXPLAIN
        assert "educat" in result.strategy_meta["role"].lower()

    def test_build_with_code_snippet(self, builder):
        """Code snippet is included in template."""
        code = "def factorial(n):\n    return 1 if n <= 1 else n * factorial(n-1)"
        request = NLaCRequest(
            idea="Analyze this function",
            context="Need review",
            inputs=NLaCInputs(code_snippet=code),
            mode="nlac"
        )

        result = builder.build(request)

        assert code in result.template
        assert "```" in result.template

    def test_build_with_error_log(self, builder):
        """Error log is included in template."""
        request = NLaCRequest(
            idea="Debug this",
            context="Production error",
            inputs=NLaCInputs(
                code_snippet="x = 1/0",
                error_log="ZeroDivisionError"
            ),
            mode="nlac"
        )

        result = builder.build(request)

        assert "ZeroDivisionError" in result.template
        assert "# Error" in result.template

    def test_build_constraints_by_complexity(self, builder):
        """Constraints scale with complexity."""
        # Simple request
        simple_request = NLaCRequest(
            idea="Print hello",
            context="Simple task",
            mode="nlac"
        )
        simple_result = builder.build(simple_request)
        assert simple_result.constraints["max_tokens"] <= 500

        # Complex request
        complex_request = NLaCRequest(
            idea="Build a comprehensive authentication system with OAuth2, "
                "JWT tokens, role-based access control, audit logging, "
                "session management, password reset flows, and security monitoring",
            context="Enterprise-grade security",
            mode="nlac"
        )
        complex_result = builder.build(complex_request)
        assert complex_result.constraints["max_tokens"] >= 1000
        assert complex_result.constraints["include_explanation"] is True


class TestOPROOptimizer:
    """Test OPROOptimizer service."""

    @pytest.fixture
    def optimizer(self):
        return OPROOptimizer(llm_client=None)  # Use simple refinement

    @pytest.fixture
    def sample_prompt(self):
        return PromptObject(
            id="test-123",
            version="1.0.0",
            intent_type=IntentType.GENERATE,
            template="Create a function that sorts a list",
            strategy_meta={"strategy": "simple"},
            constraints={"max_tokens": 500, "include_examples": True},
            created_at=datetime.now(UTC).isoformat(),
            updated_at=datetime.now(UTC).isoformat(),
        )

    def test_run_loop_returns_response(self, optimizer, sample_prompt):
        """Optimizer returns OptimizeResponse."""
        result = optimizer.run_loop(sample_prompt)

        assert result.prompt_id == sample_prompt.id
        assert result.final_instruction
        assert 0.0 <= result.final_score <= 1.0
        assert result.iteration_count == optimizer.MAX_ITERATIONS
        assert isinstance(result.trajectory, list)

    def test_run_loop_trajectory_tracking(self, optimizer, sample_prompt):
        """Each iteration is tracked in trajectory."""
        result = optimizer.run_loop(sample_prompt)

        assert len(result.trajectory) == optimizer.MAX_ITERATIONS

        for i, iteration in enumerate(result.trajectory, 1):
            assert isinstance(iteration, OPROIteration)
            assert iteration.iteration_number == i
            assert iteration.meta_prompt_used
            assert iteration.generated_instruction
            assert 0.0 <= iteration.score <= 1.0
            assert iteration.feedback

    def test_evaluate_perfect_score(self, optimizer, sample_prompt):
        """Perfect score when all constraints pass."""
        # Create a prompt that passes all checks
        perfect_prompt = PromptObject(
            id="perfect",
            version="1.0.0",
            intent_type=IntentType.GENERATE,
            template="You are a Developer.\n\n# Task\nCreate a function.\n\nFor example:\ndef example():\n    pass\n\nThis explains the reasoning clearly.",
            strategy_meta={"strategy": "simple"},
            constraints={
                "max_tokens": 500,
                "format": "code",
                "include_examples": True,
                "include_explanation": True
            },
            created_at=datetime.now(UTC).isoformat(),
            updated_at=datetime.now(UTC).isoformat(),
        )

        score, feedback = optimizer._evaluate(perfect_prompt)
        assert score == 1.0
        assert "All constraints passed" in feedback

    def test_evaluate_low_score(self, optimizer, sample_prompt):
        """Low score when constraints fail."""
        poor_prompt = PromptObject(
            id="poor",
            version="1.0.0",
            intent_type=IntentType.GENERATE,
            template="Hi",  # Too short
            strategy_meta={"strategy": "simple"},
            constraints={
                "max_tokens": 10,  # Will fail: template > 10 chars
                "include_examples": True,  # Will fail: no examples
            },
            created_at=datetime.now(UTC).isoformat(),
            updated_at=datetime.now(UTC).isoformat(),
        )

        score, feedback = optimizer._evaluate(poor_prompt)
        assert score < 1.0
        assert "Issues:" in feedback

    def test_build_meta_prompt_with_history(self, optimizer, sample_prompt):
        """Meta-prompt includes trajectory history."""
        trajectory = [
            OPROIteration(
                iteration_number=1,
                meta_prompt_used="Improve this",
                generated_instruction="Version 1",
                score=0.5,
                feedback="Needs more detail"
            ),
            OPROIteration(
                iteration_number=2,
                meta_prompt_used="Improve this again",
                generated_instruction="Version 2",
                score=0.7,
                feedback="Better but unclear"
            )
        ]

        meta_prompt = optimizer._build_meta_prompt(sample_prompt, trajectory)

        assert "Iteration 1" in meta_prompt
        assert "Iteration 2" in meta_prompt
        assert "0.50" in meta_prompt
        assert "0.70" in meta_prompt


class TestPromptValidator:
    """Test PromptValidator service."""

    @pytest.fixture
    def validator(self):
        return PromptValidator(llm_client=None)  # Use simple autocorrect

    @pytest.fixture
    def valid_prompt(self):
        return PromptObject(
            id="valid",
            version="1.0.0",
            intent_type=IntentType.GENERATE,
            template="You are a Developer.\n\n# Task\nCreate a function.\n\nFor example:\ndef test():\n    pass",
            strategy_meta={"strategy": "simple"},
            constraints={
                "max_tokens": 200,
                "include_examples": True
            },
            created_at=datetime.now(UTC).isoformat(),
            updated_at=datetime.now(UTC).isoformat(),
        )

    def test_validate_passed_no_warnings(self, validator, valid_prompt):
        """Valid prompt passes with no warnings."""
        passed, warnings = validator.validate(valid_prompt)

        assert passed is True
        assert warnings == []

    def test_validate_max_tokens_violation(self, validator):
        """Detects max_tokens constraint violation."""
        short_prompt = PromptObject(
            id="token-test",
            version="1.0.0",
            intent_type=IntentType.GENERATE,
            template="A" * 1000,  # 1000 characters
            strategy_meta={"strategy": "simple"},
            constraints={"max_tokens": 100},  # Only allows 100
            created_at=datetime.now(UTC).isoformat(),
            updated_at=datetime.now(UTC).isoformat(),
        )

        passed, warnings = validator.validate(short_prompt)

        assert passed is False
        assert any("max_tokens" in w for w in warnings)

    def test_validate_missing_examples(self, validator):
        """Detects missing examples when required."""
        no_examples_prompt = PromptObject(
            id="no-examples",
            version="1.0.0",
            intent_type=IntentType.GENERATE,
            template="You are a Developer.\n\nCreate a function.",
            strategy_meta={"strategy": "simple"},
            constraints={"include_examples": True},
            created_at=datetime.now(UTC).isoformat(),
            updated_at=datetime.now(UTC).isoformat(),
        )

        passed, warnings = validator.validate(no_examples_prompt)

        assert passed is False
        assert any("examples" in w.lower() for w in warnings)

    def test_validate_missing_explanation(self, validator):
        """Detects missing explanation when required."""
        no_explanation_prompt = PromptObject(
            id="no-explanation",
            version="1.0.0",
            intent_type=IntentType.GENERATE,
            template="You are a Developer.\n\nCreate the function.\n\ndef test():\n    pass",
            strategy_meta={"strategy": "simple"},
            constraints={"include_explanation": True},
            created_at=datetime.now(UTC).isoformat(),
            updated_at=datetime.now(UTC).isoformat(),
        )

        passed, warnings = validator.validate(no_explanation_prompt)

        assert passed is False
        assert any("explanation" in w.lower() for w in warnings)

    def test_validate_too_short(self, validator):
        """Detects templates that are too short before autocorrect."""
        # Note: The validator will autocorrect to add role, making it longer
        # So we check the raw constraint check directly
        short_prompt = PromptObject(
            id="short",
            version="1.0.0",
            intent_type=IntentType.GENERATE,
            template="Short",  # Only 5 chars (< 20)
            strategy_meta={"strategy": "simple"},
            constraints={},
            created_at=datetime.now(UTC).isoformat(),
            updated_at=datetime.now(UTC).isoformat(),
        )

        # Check raw constraint check
        warnings = validator._check_constraints(short_prompt)
        assert any("too short" in w.lower() for w in warnings)

    def test_validate_missing_role(self, validator):
        """Detects missing role/task definition."""
        # Note: "Just do it" contains "do" which is a keyword, so use different text
        no_role_prompt = PromptObject(
            id="no-role",
            version="1.0.0",
            intent_type=IntentType.GENERATE,
            template="Execute the function immediately",
            strategy_meta={"strategy": "simple"},
            constraints={},
            created_at=datetime.now(UTC).isoformat(),
            updated_at=datetime.now(UTC).isoformat(),
        )

        # Check raw constraint check (before autocorrect)
        warnings = validator._check_constraints(no_role_prompt)
        assert any("role" in w.lower() or "task" in w.lower() for w in warnings)

    def test_validate_no_markdown_constraint(self, validator):
        """Detects markdown when no_markdown format required."""
        # Note: Check raw constraint before autocorrect removes the markdown
        markdown_prompt = PromptObject(
            id="markdown",
            version="1.0.0",
            intent_type=IntentType.GENERATE,
            template="```python\ndef test():\n    pass\n```",
            strategy_meta={"strategy": "simple"},
            constraints={"format": "no_markdown"},
            created_at=datetime.now(UTC).isoformat(),
            updated_at=datetime.now(UTC).isoformat(),
        )

        # Check raw constraint (before autocorrect)
        warnings = validator._check_constraints(markdown_prompt)
        assert any("markdown" in w.lower() and "prohibited" in w.lower() for w in warnings)

    def test_autocorrect_adds_missing_role(self, validator):
        """Autocorrect adds missing role to template."""
        no_role_prompt = PromptObject(
            id="no-role",
            version="1.0.0",
            intent_type=IntentType.GENERATE,
            template="Create a function",
            strategy_meta={"strategy": "simple"},
            constraints={},
            created_at=datetime.now(UTC).isoformat(),
            updated_at=datetime.now(UTC).isoformat(),
        )

        warnings = ["Template missing role or task definition"]

        # First pass: autocorrect
        result = validator._simple_autocorrect(no_role_prompt, warnings)

        assert result is True
        assert "# Role" in no_role_prompt.template
        assert "expert assistant" in no_role_prompt.template.lower()

    def test_autocorrect_removes_markdown(self, validator):
        """Autocorrect removes markdown when no_markdown required."""
        markdown_prompt = PromptObject(
            id="markdown",
            version="1.0.0",
            intent_type=IntentType.GENERATE,
            template="```python\ndef test():\n    pass\n```",
            strategy_meta={"strategy": "simple"},
            constraints={"format": "no_markdown"},
            created_at=datetime.now(UTC).isoformat(),
            updated_at=datetime.now(UTC).isoformat(),
        )

        warnings = ["Template contains markdown code blocks (prohibited)"]

        result = validator._simple_autocorrect(markdown_prompt, warnings)

        assert result is True
        assert "```" not in markdown_prompt.template

    def test_reflexion_loop_retries(self, validator):
        """Validation retries after autocorrection."""
        # First version fails
        failing_prompt = PromptObject(
            id="retry-test",
            version="1.0.0",
            intent_type=IntentType.GENERATE,
            template="Create",  # Too short, no role
            strategy_meta={"strategy": "simple"},
            constraints={"include_examples": True},
            created_at=datetime.now(UTC).isoformat(),
            updated_at=datetime.now(UTC).isoformat(),
        )

        # Validate will trigger autocorrect and re-validate
        passed, warnings = validator.validate(failing_prompt)

        # After autocorrect, it should have role added
        assert "# Role" in failing_prompt.template

    def test_has_examples_detection(self, validator):
        """Example detection works correctly."""
        assert validator._has_examples("For example, do X") is True
        assert validator._has_examples("Such as Y") is True
        assert validator._has_examples("e.g., Z") is True
        assert validator._has_examples("Por ejemplo: A") is True
        # Note: "examples" contains "example" as substring, so it matches
        # Use text that truly has no example indicators
        assert validator._has_examples("Just do the task") is False
        assert validator._has_examples("Execute the code") is False

    def test_has_explanation_detection(self, validator):
        """Explanation detection works correctly."""
        assert validator._has_explanation("Explain why this works") is True
        assert validator._has_explanation("The reason is") is True
        assert validator._has_explanation("How it functions") is True
        assert validator._has_explanation("Just do it") is False

    def test_is_json_ready_detection(self, validator):
        """JSON readiness detection works."""
        # Valid JSON
        assert validator._is_json_ready('{"key": "value"}') is True

        # JSON indicators
        assert validator._is_json_ready("Return JSON output") is True
        assert validator._is_json_ready("output.json") is True
        assert validator._is_json_ready("{") is True

        # Not JSON
        assert validator._is_json_ready("Just plain text") is False
