"""Domain type definitions."""

from hemdov.domain.types.result import (
    Failure,
    Result,
    Success,
    is_failure,
    is_success,
)

__all__ = ["Success", "Failure", "Result", "is_success", "is_failure"]
