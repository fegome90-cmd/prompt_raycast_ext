"""Unit tests for IFEvalValidator."""

import pytest

from hemdov.domain.services.ifeval_validator import (
    IFEvalValidator,
    ValidationResult,
    action_verbs_constraint,
    json_format_constraint,
    min_length_constraint,
)


class TestMinLengthConstraint:
    """Tests for min_length_constraint."""

    def test_passes_when_length_met(self):
        """Constraint passes when prompt meets minimum length."""
        constraint = min_length_constraint(min_chars=50)
        passed, reason = constraint("a" * 50)
        assert passed is True
        assert "50 chars" in reason

    def test_passes_when_length_exceeded(self):
        """Constraint passes when prompt exceeds minimum length."""
        constraint = min_length_constraint(min_chars=50)
        passed, reason = constraint("a" * 100)
        assert passed is True

    def test_fails_when_too_short(self):
        """Constraint fails when prompt is too short."""
        constraint = min_length_constraint(min_chars=50)
        passed, reason = constraint("a" * 49)
        assert passed is False
        assert "49 chars" in reason

    def test_ignores_whitespace(self):
        """Constraint ignores leading/trailing whitespace."""
        constraint = min_length_constraint(min_chars=5)
        passed, _ = constraint("  abc  ")
        # After stripping whitespace, "abc" is only 3 chars < 5
        assert passed is False

        # But with enough content it should pass
        passed, _ = constraint("  abcdef  ")
        # After stripping, "abcdef" is 6 chars >= 5
        assert passed is True


class TestActionVerbsConstraint:
    """Tests for action_verbs_constraint."""

    def test_default_verbs(self):
        """Default verbs are detected."""
        constraint = action_verbs_constraint()

        # Each default verb should be detected
        test_cases = [
            ("Create something", True),
            ("implement something", True),
            ("Write something", True),
            ("build something", True),
            ("develop something", True),
            ("add something", True),
        ]

        for prompt, expected in test_cases:
            passed, reason = constraint(prompt)
            assert passed is expected, f"Failed for: {prompt}"

    def test_case_insensitive(self):
        """Verb detection is case-insensitive."""
        constraint = action_verbs_constraint()
        passed, _ = constraint("CREATE something")
        assert passed is True

    def test_fails_when_no_verb(self):
        """Constraint fails when no action verb found."""
        constraint = action_verbs_constraint()
        passed, reason = constraint("hello world")
        assert passed is False
        assert "none" in reason

    def test_custom_verbs(self):
        """Custom verbs can be specified."""
        constraint = action_verbs_constraint(verbs=["generate", "optimize"])

        passed, _ = constraint("generate code")
        assert passed is True

        passed, _ = constraint("create code")
        assert passed is False


class TestJSONFormatConstraint:
    """Tests for json_format_constraint."""

    def test_passes_valid_json_object(self):
        """Valid JSON object passes."""
        constraint = json_format_constraint()
        passed, reason = constraint('{"key": "value"}')
        assert passed is True
        assert "Valid JSON" in reason

    def test_passes_valid_json_array(self):
        """Valid JSON array passes."""
        constraint = json_format_constraint()
        passed, reason = constraint('["item1", "item2"]')
        assert passed is True

    def test_passes_valid_json_primitive(self):
        """Valid JSON primitives pass."""
        constraint = json_format_constraint()

        for value in ['"string"', "true", "false", "null", "123"]:
            passed, _ = constraint(value)
            assert passed is True, f"Failed for: {value}"

    def test_fails_invalid_json_syntax(self):
        """Invalid JSON syntax fails."""
        constraint = json_format_constraint()
        passed, reason = constraint('{"key": value}')
        assert passed is False
        assert "Invalid JSON" in reason

    def test_passes_non_json_prompts(self):
        """Non-JSON prompts are acceptable."""
        constraint = json_format_constraint()
        passed, reason = constraint("Create a function")
        assert passed is True
        assert "acceptable" in reason


class TestIFEvalValidator:
    """Tests for IFEvalValidator."""

    def test_init_default_threshold(self):
        """Default threshold is 0.7 when not specified."""
        validator = IFEvalValidator()
        assert validator.threshold == 0.7

    def test_init_custom_threshold(self):
        """Custom threshold can be set."""
        validator = IFEvalValidator(threshold=0.5)
        assert validator.threshold == 0.5

    def test_validate_returns_validation_result(self):
        """Validate returns ValidationResult with correct structure."""
        validator = IFEvalValidator(threshold=0.7)
        result = validator.validate("test prompt")

        assert isinstance(result, ValidationResult)
        assert isinstance(result.score, float)
        assert 0.0 <= result.score <= 1.0
        assert isinstance(result.passed, bool)
        assert isinstance(result.details, dict)

    def test_validate_score_calculation(self):
        """Score is calculated as passed/total constraints."""
        validator = IFEvalValidator(threshold=0.7)

        # Test with a prompt that should fail some constraints
        result = validator.validate("hi")  # Too short, no action verb
        # With 3 constraints: fails 2, passes 1 (json constraint)
        assert result.score == pytest.approx(1/3)

    def test_validate_passed_uses_threshold(self):
        """Passed status is based on score vs threshold."""
        validator = IFEvalValidator(threshold=0.5)

        # Score 0.33 < 0.5 should fail
        result = validator.validate("hi")
        assert result.passed is False

        # Score 1.0 >= 0.5 should pass
        long_prompt = "Implement " + "x" * 100  # Has verb, long enough
        result = validator.validate(long_prompt)
        assert result.passed is True

    def test_validate_details_contains_all_constraints(self):
        """Details dict contains results for all constraints."""
        validator = IFEvalValidator(threshold=0.0)
        result = validator.validate("test")

        # Should have 3 constraint results
        assert len(result.details) == 3

        # Each detail should be a (passed, reason) tuple
        for key, value in result.details.items():
            assert key.startswith("constraint_")
            assert isinstance(value, tuple)
            assert len(value) == 2
            assert isinstance(value[0], bool)
            assert isinstance(value[1], str)

    def test_get_threshold(self):
        """get_threshold returns current threshold."""
        validator = IFEvalValidator(threshold=0.8)
        assert validator.get_threshold() == 0.8

    def test_full_prompt_passes_all_constraints(self):
        """A well-formed prompt passes all constraints."""
        validator = IFEvalValidator(threshold=0.7)
        prompt = "Implement a comprehensive user authentication system with JWT tokens, refresh logic, and secure password hashing using bcrypt"

        result = validator.validate(prompt)

        assert result.score == 1.0
        assert result.passed is True

        # Check individual constraints
        for _, (passed, _) in result.details.items():
            assert passed is True


class TestCalibrationLoading:
    """Tests for calibration data loading utility."""

    def test_load_calibrated_threshold_from_file(self, tmp_path):
        """Threshold is loaded from calibration file if exists."""
        import json
        from pathlib import Path

        # Create temporary calibration file
        calibration_data = {
            "calibrated_threshold": 0.65,
            "results": [],
            "statistics": {},
        }
        calibration_file = tmp_path / "ifeval-calibration.json"
        calibration_file.write_text(json.dumps(calibration_data))

        # Import the load function from bootstrap script
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
        from bootstrap_ifeval_calibration import load_calibrated_threshold

        threshold = load_calibrated_threshold(calibration_file)
        assert threshold == 0.65

    def test_load_calibrated_threshold_fallback(self, tmp_path):
        """Falls back to 0.7 when calibration file doesn't exist."""
        # Import the load function from bootstrap script
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
        from bootstrap_ifeval_calibration import load_calibrated_threshold

        # Use non-existent file path
        threshold = load_calibrated_threshold(tmp_path / "nonexistent.json")
        assert threshold == 0.7
