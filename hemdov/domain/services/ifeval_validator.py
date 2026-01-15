"""
IFEval Validator - Real validation with 3 constraints (v2.1-no-mocks).

This is a simplified IFEval-style validator for prompt quality assessment.
Uses 3 basic constraints that can be evaluated WITHOUT an LLM:

1. Minimum length: ≥50 characters
2. Action verbs: create, implement, write, build, develop, add
3. JSON format: prompt must be valid JSON

This allows generating REAL calibration scores from the catalog,
not mock/random data like v2.0.
"""

import json
import logging
from dataclasses import dataclass
from typing import Protocol

logger = logging.getLogger(__name__)


class Constraint(Protocol):
    """A constraint that can be evaluated on a prompt."""

    def __call__(self, prompt: str) -> tuple[bool, str]:
        """
        Evaluate constraint on prompt.

        Returns:
            (passed, reason) - tuple of pass status and explanation
        """
        ...


@dataclass
class ValidationResult:
    """Result of IFEval validation."""

    score: float  # 0.0 to 1.0
    passed: bool  # Whether score >= threshold
    details: dict[str, tuple[bool, str]]  # Constraint results


# ============================================================================
# Constraint Implementations
# ============================================================================

def min_length_constraint(min_chars: int = 50) -> Constraint:
    """
    Constraint: Prompt must have minimum length.

    Args:
        min_chars: Minimum character count (default: 50)

    Returns:
        Constraint function
    """
    def check(prompt: str) -> tuple[bool, str]:
        length = len(prompt.strip())
        passed = length >= min_chars
        reason = f"Length: {length} chars (min: {min_chars})"
        return passed, reason

    return check


def action_verbs_constraint(verbs: list[str] | None = None) -> Constraint:
    """
    Constraint: Prompt must contain at least one action verb.

    Args:
        verbs: List of action verbs to check (default: create, implement, write, build, develop, add)

    Returns:
        Constraint function
    """
    if verbs is None:
        verbs = ["create", "implement", "write", "build", "develop", "add"]

    def check(prompt: str) -> tuple[bool, str]:
        prompt_lower = prompt.lower()
        found = [verb for verb in verbs if verb.lower() in prompt_lower]
        passed = len(found) > 0
        reason = f"Action verbs found: {found or 'none'}"
        return passed, reason

    return check


def json_format_constraint() -> Constraint:
    """
    Constraint: Prompt must be valid JSON.

    Note: This checks if the prompt is a valid JSON string,
    not if it contains JSON.

    Returns:
        Constraint function
    """
    def check(prompt: str) -> tuple[bool, str]:
        try:
            json.loads(prompt)
            passed = True
            reason = "Valid JSON"
        except json.JSONDecodeError:
            # Try to see if it's a JSON-like structure
            prompt_stripped = prompt.strip()
            if prompt_stripped.startswith(('{', '[', '"')) or prompt_stripped in ('true', 'false', 'null'):
                passed = False
                reason = "Invalid JSON syntax"
            else:
                # Not JSON-like at all, which is fine for non-JSON prompts
                passed = True
                reason = "Not JSON (acceptable for non-JSON prompts)"

        return passed, reason

    return check


# Default constraints for IFEval validation
CONSTRAINTS: list[Constraint] = [
    min_length_constraint(min_chars=50),
    action_verbs_constraint(),
    json_format_constraint(),
]


# ============================================================================
# IFEval Validator
# ============================================================================

class IFEvalValidator:
    """
    IFEval-style prompt validator with real constraints.

    This validator uses 3 simple constraints that can be evaluated
    without an LLM, enabling real calibration data generation.

    The threshold must be provided by the caller - this keeps the
    domain layer pure (no file I/O).

    Usage:
        # Load threshold from infrastructure layer
        threshold = load_threshold_from_calibration()  # 0.67
        validator = IFEvalValidator(threshold=threshold)
        result = validator.validate('Create a function to sort a list')
        print(result.score)  # 0.0 to 1.0
    """

    def __init__(
        self,
        constraints: list[Constraint] | None = None,
        threshold: float = 0.7,
    ):
        """
        Initialize IFEval validator.

        Args:
            constraints: List of constraint functions (default: 3 basic constraints)
            threshold: Pass threshold (0.0-1.0), must be provided by caller
        """
        self.constraints = constraints or CONSTRAINTS
        self.threshold = threshold
        logger.info(f"IFEvalValidator initialized with threshold={threshold}")

    def validate(self, prompt: str) -> ValidationResult:
        """
        Validate prompt against all constraints.

        Args:
            prompt: Prompt string to validate

        Returns:
            ValidationResult with score, passed status, and constraint details
        """
        details: dict[str, tuple[bool, str]] = {}
        passed_count = 0

        # Evaluate each constraint
        for i, constraint in enumerate(self.constraints):
            passed, reason = constraint(prompt)
            constraint_name = f"constraint_{i}"
            details[constraint_name] = (passed, reason)
            if passed:
                passed_count += 1

        # Calculate score (0.0 to 1.0)
        score = passed_count / len(self.constraints) if self.constraints else 0.0

        # Determine if passed (score >= threshold)
        passed = score >= self.threshold

        return ValidationResult(
            score=score,
            passed=passed,
            details=details,
        )

    def get_threshold(self) -> float:
        """Get current threshold."""
        return self.threshold


# ============================================================================
# Standalone Test
# ============================================================================

if __name__ == "__main__":
    # Quick test
    validator = IFEvalValidator(threshold=0.7)

    test_prompts = [
        "Create a function to sort a list",  # Good (has action verb, but short)
        "Implement a user authentication system with JWT tokens and refresh logic",  # Good
        "hi",  # Bad (too short, no action verb)
        '{"prompt": "Create a function"}',  # Good (valid JSON, action verb)
    ]

    for prompt in test_prompts:
        result = validator.validate(prompt)
        print(f"\nPrompt: {prompt[:50]}...")
        print(f"  Score: {result.score:.2f}")
        print(f"  Passed: {result.passed} (threshold: {validator.threshold})")
        for name, (passed, reason) in result.details.items():
            status = "✅" if passed else "❌"
            print(f"    {status} {name}: {reason}")
