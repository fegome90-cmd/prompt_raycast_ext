# api/circuit_breaker.py
import asyncio
import logging
from datetime import UTC, datetime, timedelta

logger = logging.getLogger(__name__)


class CircuitBreaker:
    """
    Thread-safe circuit breaker for async operations.

    Prevents cascading failures by disabling operations after
    consecutive failures. Automatically re-enables after cooldown period.
    """

    def __init__(self, max_failures: int = 5, timeout_seconds: int = 300):
        self._max_failures = max_failures
        self._timeout_seconds = timeout_seconds
        self._failure_count = 0
        self._disabled_until: datetime | None = None
        self._lock = asyncio.Lock()

    async def should_attempt(self) -> bool:
        """Check if operation should be attempted."""
        async with self._lock:
            # Check if disabled
            if self._disabled_until:
                if datetime.now(UTC) < self._disabled_until:
                    logger.warning(
                        f"Circuit breaker open until {self._disabled_until.isoformat()}"
                    )
                    return False
                # Reset after timeout
                logger.info("Circuit breaker timeout elapsed, resetting")
                self._failure_count = 0
                self._disabled_until = None

            return True

    async def record_success(self):
        """Record successful operation."""
        async with self._lock:
            if self._failure_count > 0:
                logger.info(f"Circuit breaker reset (was at {self._failure_count} failures)")
            self._failure_count = 0
            self._disabled_until = None

    async def record_failure(self):
        """Record failed operation and trip if needed."""
        async with self._lock:
            self._failure_count += 1

            if self._failure_count >= self._max_failures:
                self._disabled_until = datetime.now(UTC) + timedelta(
                    seconds=self._timeout_seconds
                )
                logger.error(
                    f"Circuit breaker tripped after {self._failure_count} failures, "
                    f"disabled until {self._disabled_until.isoformat()}"
                )
            else:
                logger.warning(
                    f"Circuit breaker failure count: "
                    f"{self._failure_count}/{self._max_failures}"
                )
