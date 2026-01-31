"""Circuit breaker pattern for external service calls."""

import asyncio
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from enum import Enum
from functools import wraps
from typing import TypeVar

from identity_plan_kit.shared.logging import get_logger

logger = get_logger(__name__)

T = TypeVar("T")


class CircuitState(Enum):
    """Circuit breaker states."""

    CLOSED = "closed"  # Normal operation, requests flow through
    OPEN = "open"  # Failing, requests are rejected immediately
    HALF_OPEN = "half_open"  # Testing if service has recovered


@dataclass
class CircuitStats:
    """Statistics for circuit breaker."""

    failures: int = 0
    successes: int = 0
    last_failure_time: datetime | None = None
    last_success_time: datetime | None = None
    state_changed_at: datetime = field(default_factory=lambda: datetime.now(UTC))


class CircuitBreakerError(Exception):
    """Raised when circuit is open and request is rejected."""

    def __init__(self, name: str, retry_after: float) -> None:
        self.name = name
        self.retry_after = retry_after
        super().__init__(f"Circuit breaker '{name}' is open. Retry after {retry_after:.1f}s")


class CircuitBreaker:
    """
    Circuit breaker for protecting against cascading failures.

    States:
    - CLOSED: Normal operation. Failures are counted.
    - OPEN: Service is failing. Requests fail immediately.
    - HALF_OPEN: Testing recovery. Limited requests allowed.

    Example:
        ```python
        google_breaker = CircuitBreaker(
            name="google_oauth",
            failure_threshold=5,
            recovery_timeout=60,
        )

        @google_breaker
        async def call_google_api():
            ...
        ```
    """

    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        half_open_max_calls: int = 3,
        success_threshold: int = 2,
        exclude_exceptions: tuple[type[Exception], ...] | None = None,
    ) -> None:
        """
        Initialize circuit breaker.

        Args:
            name: Name for logging and identification
            failure_threshold: Failures before opening circuit
            recovery_timeout: Seconds before attempting recovery
            half_open_max_calls: Max calls allowed in half-open state
            success_threshold: Successes in half-open before closing
            exclude_exceptions: Exceptions that don't count as failures
        """
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = timedelta(seconds=recovery_timeout)
        self.half_open_max_calls = half_open_max_calls
        self.success_threshold = success_threshold
        self.exclude_exceptions = exclude_exceptions or ()

        self._state = CircuitState.CLOSED
        self._stats = CircuitStats()
        self._half_open_calls = 0
        self._lock = asyncio.Lock()

    @property
    def state(self) -> CircuitState:
        """Get current circuit state."""
        return self._state

    @property
    def stats(self) -> CircuitStats:
        """Get circuit statistics."""
        return self._stats

    def _should_allow_request(self) -> bool:
        """Check if request should be allowed based on current state."""
        now = datetime.now(UTC)

        if self._state == CircuitState.CLOSED:
            return True

        if self._state == CircuitState.OPEN:
            # Check if recovery timeout has passed
            time_in_open = now - self._stats.state_changed_at
            if time_in_open >= self.recovery_timeout:
                self._transition_to(CircuitState.HALF_OPEN)
                return True
            return False

        if self._state == CircuitState.HALF_OPEN:
            # Allow limited calls in half-open state
            return self._half_open_calls < self.half_open_max_calls

        return False

    def _transition_to(self, new_state: CircuitState) -> None:
        """Transition to a new state."""
        old_state = self._state
        self._state = new_state
        self._stats.state_changed_at = datetime.now(UTC)

        if new_state == CircuitState.HALF_OPEN:
            self._half_open_calls = 0
            self._stats.successes = 0

        if new_state == CircuitState.CLOSED:
            self._stats.failures = 0

        logger.info(
            "circuit_breaker_state_change",
            name=self.name,
            from_state=old_state.value,
            to_state=new_state.value,
        )

    def _record_success(self) -> None:
        """Record a successful call."""
        self._stats.successes += 1
        self._stats.last_success_time = datetime.now(UTC)

        if self._state == CircuitState.HALF_OPEN and self._stats.successes >= self.success_threshold:
            self._transition_to(CircuitState.CLOSED)

    def _record_failure(self) -> None:
        """Record a failed call."""
        self._stats.failures += 1
        self._stats.last_failure_time = datetime.now(UTC)

        if self._state == CircuitState.CLOSED:
            if self._stats.failures >= self.failure_threshold:
                self._transition_to(CircuitState.OPEN)

        elif self._state == CircuitState.HALF_OPEN:
            # Any failure in half-open goes back to open
            self._transition_to(CircuitState.OPEN)

    def _get_retry_after(self) -> float:
        """Get seconds until circuit might allow requests."""
        if self._state != CircuitState.OPEN:
            return 0.0

        elapsed = datetime.now(UTC) - self._stats.state_changed_at
        remaining = self.recovery_timeout - elapsed
        return max(0.0, remaining.total_seconds())

    def __call__(self, func: Callable[..., T]) -> Callable[..., T]:
        """
        Use as decorator for async functions.

        Example:
            @circuit_breaker
            async def my_external_call():
                ...
        """

        @wraps(func)
        async def wrapper(*args: object, **kwargs: object) -> T:
            # Optimistic read for the common case (CLOSED state)
            # Avoids lock contention when circuit is healthy
            current_state = self._state

            if current_state == CircuitState.CLOSED:
                # Fast path: circuit is closed, proceed without lock
                pass
            elif current_state == CircuitState.OPEN:
                # Check if we should transition to half-open (requires lock)
                async with self._lock:
                    if not self._should_allow_request():
                        retry_after = self._get_retry_after()
                        logger.warning(
                            "circuit_breaker_rejected",
                            name=self.name,
                            state=self._state.value,
                            retry_after=retry_after,
                        )
                        raise CircuitBreakerError(self.name, retry_after)
                    # State may have changed to HALF_OPEN in _should_allow_request
                    if self._state == CircuitState.HALF_OPEN:
                        self._half_open_calls += 1
            else:  # HALF_OPEN
                async with self._lock:
                    if self._half_open_calls >= self.half_open_max_calls:
                        retry_after = self._get_retry_after()
                        logger.warning(
                            "circuit_breaker_rejected",
                            name=self.name,
                            state=self._state.value,
                            retry_after=retry_after,
                        )
                        raise CircuitBreakerError(self.name, retry_after)
                    self._half_open_calls += 1

            try:
                result = await func(*args, **kwargs)
                async with self._lock:
                    self._record_success()
                return result  # noqa: TRY300
            except self.exclude_exceptions:
                # Don't count excluded exceptions as failures
                raise
            except Exception as e:
                async with self._lock:
                    self._record_failure()
                logger.warning(
                    "circuit_breaker_failure",
                    name=self.name,
                    error=str(e),
                    failures=self._stats.failures,
                )
                raise

        return wrapper  # type: ignore[return-value]

    # Alias for decorator usage
    call = __call__
