"""Domain type definitions."""

from hemdov.domain.types.result import (
    Success,
    Failure,
    Result,
    is_success,
    is_failure,
)

__all__ = ["Success", "Failure", "Result", "is_success", "is_failure"]
