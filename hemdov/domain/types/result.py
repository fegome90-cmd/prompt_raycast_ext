"""Result type for explicit error handling.

Instead of conflating "not found" and "error" in Optional[dict],
Result makes success and failure explicit in the type system.
"""

from typing import TypeVar, Generic
from dataclasses import dataclass, field

# Import DomainError for type annotation
from hemdov.domain.errors import DomainError

T = TypeVar('T')  # Success value type
E = TypeVar('E', bound=DomainError)  # Failure error type


@dataclass(frozen=True)
class Success(Generic[T]):
    """Represents a successful operation.

    Attributes:
        value: The success value of type T
        degradation_flags: Optional flags indicating degraded features
                           (CLAUDE.md compliance for graceful degradation)
    """
    value: T
    degradation_flags: dict[str, bool] = field(default_factory=dict)


@dataclass(frozen=True)
class Failure(Generic[E]):
    """Represents a failed operation.

    Attributes:
        error: The domain error that caused the failure
    """
    error: E


# Type alias for Result union type
Result = Success[T] | Failure[E]


def is_success(result: Result[T, E]) -> bool:
    """Check if Result is a Success.

    Usage:
        result = await operation()
        if is_success(result):
            value = result.value
        else:
            error = result.error
    """
    return isinstance(result, Success)


def is_failure(result: Result[T, E]) -> bool:
    """Check if Result is a Failure.

    Usage:
        result = await operation()
        if is_failure(result):
            handle_error(result.error)
    """
    return isinstance(result, Failure)
