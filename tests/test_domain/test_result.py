"""Test Result type for explicit error handling."""

import pytest
from hemdov.domain.errors import DomainError, ErrorCategory
from hemdov.domain.types.result import (
    Success,
    Failure,
    Result,
    is_success,
    is_failure,
)


class TestSuccess:
    def test_success_contains_value(self):
        """Success must contain the success value."""
        result = Success(value="prompt text")
        assert result.value == "prompt text"

    def test_success_has_empty_degradation_flags_by_default(self):
        """Success has empty degradation flags when not specified."""
        result = Success(value="data")
        assert result.degradation_flags == {}

    def test_success_can_carry_degradation_flags(self):
        """Success can indicate degraded features via flags."""
        result = Success(
            value="prompt",
            degradation_flags={"knn_disabled": True, "metrics_failed": False}
        )
        assert result.degradation_flags["knn_disabled"] is True
        assert result.degradation_flags["metrics_failed"] is False

    def test_success_is_frozen(self):
        """Success is immutable (frozen dataclass)."""
        result = Success(value="data")
        with pytest.raises(Exception):
            result.value = "modified"


class TestFailure:
    def test_failure_contains_error(self):
        """Failure must contain the domain error."""
        error = DomainError(
            category=ErrorCategory.VALIDATION,
            message="Invalid",
            error_id="VAL-001",
            context={}
        )
        result = Failure(error=error)
        assert result.error == error

    def test_failure_is_frozen(self):
        """Failure is immutable."""
        error = DomainError(
            category=ErrorCategory.VALIDATION,
            message="Invalid",
            error_id="VAL-001",
            context={}
        )
        result = Failure(error=error)
        with pytest.raises(Exception):
            result.error = None


class TestResultHelpers:
    def test_is_success_returns_true_for_success(self):
        """is_success returns True for Success instances."""
        result: Result[str, DomainError] = Success("value")
        assert is_success(result) is True
        assert is_failure(result) is False

    def test_is_failure_returns_true_for_failure(self):
        """is_failure returns True for Failure instances."""
        error = DomainError(ErrorCategory.VALIDATION, "err", "VAL-001", {})
        result: Result[str, DomainError] = Failure(error)
        assert is_success(result) is False
        assert is_failure(result) is True

    def test_result_invariant_xor(self):
        """Result must be Success XOR Failure, never both.

        This invariant ensures we can't have invalid Result states.
        """
        success = Success("value")
        failure = Failure(DomainError(ErrorCategory.VALIDATION, "err", "VAL-001", {}))

        # Success is not failure
        assert is_success(success) ^ is_failure(success)

        # Failure is not success
        assert is_success(failure) ^ is_failure(failure)

    def test_result_type_annotation_works(self):
        """Result type annotation preserves generic types."""
        # String success, DomainError failure
        result1: Result[str, DomainError] = Success("text")

        # Int success, CacheError failure
        from hemdov.domain.errors import CacheError
        cache_err = CacheError(ErrorCategory.CACHE_OPERATION, "err", "CACHE-001", {}, "key", "get")
        result2: Result[int, CacheError] = Success(42)

        assert is_success(result1)
        assert is_success(result2)
