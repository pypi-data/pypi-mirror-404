"""Graceful shutdown with request draining and degradation mode."""

import asyncio
import contextlib
import signal
from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from identity_plan_kit.shared.logging import get_logger

logger = get_logger(__name__)


class ServiceMode(str, Enum):
    """Service operating modes."""

    NORMAL = "normal"
    DEGRADED = "degraded"
    DRAINING = "draining"
    SHUTDOWN = "shutdown"


@dataclass
class ShutdownState:
    """Tracks shutdown state and active requests."""

    mode: ServiceMode = ServiceMode.NORMAL
    active_requests: int = 0
    shutdown_started_at: datetime | None = None
    degradation_reason: str | None = None
    _lock: asyncio.Lock = field(default_factory=asyncio.Lock)

    async def increment_requests(self) -> None:
        """Increment active request count."""
        async with self._lock:
            self.active_requests += 1

    async def decrement_requests(self) -> None:
        """Decrement active request count."""
        async with self._lock:
            self.active_requests = max(0, self.active_requests - 1)

    async def start_draining(self) -> None:
        """Enter draining mode for graceful shutdown."""
        async with self._lock:
            self.mode = ServiceMode.DRAINING
            self.shutdown_started_at = datetime.now(UTC)
            logger.info(
                "shutdown_draining_started",
                active_requests=self.active_requests,
            )

    async def enter_degraded_mode(self, reason: str) -> None:
        """Enter degraded mode."""
        async with self._lock:
            if self.mode == ServiceMode.NORMAL:
                self.mode = ServiceMode.DEGRADED
                self.degradation_reason = reason
                logger.warning(
                    "service_degraded",
                    reason=reason,
                )

    async def exit_degraded_mode(self) -> None:
        """Exit degraded mode back to normal."""
        async with self._lock:
            if self.mode == ServiceMode.DEGRADED:
                self.mode = ServiceMode.NORMAL
                self.degradation_reason = None
                logger.info("service_recovered")

    def get_status(self) -> dict[str, Any]:
        """Get current status for health checks."""
        return {
            "mode": self.mode.value,
            "active_requests": self.active_requests,
            "shutdown_started_at": (
                self.shutdown_started_at.isoformat() if self.shutdown_started_at else None
            ),
            "degradation_reason": self.degradation_reason,
        }


# Global shutdown state
_shutdown_state = ShutdownState()


def get_shutdown_state() -> ShutdownState:
    """Get the global shutdown state."""
    return _shutdown_state


class GracefulShutdownMiddleware(BaseHTTPMiddleware):
    """
    Middleware for tracking active requests and handling graceful shutdown.

    Features:
    - Tracks active requests for draining
    - Returns 503 for new requests during shutdown
    - Allows in-flight requests to complete

    Usage:
        ```python
        from identity_plan_kit.shared.graceful_shutdown import GracefulShutdownMiddleware

        app.add_middleware(GracefulShutdownMiddleware)
        ```
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with shutdown awareness."""
        state = get_shutdown_state()

        # Reject new requests during draining/shutdown
        if state.mode in (ServiceMode.DRAINING, ServiceMode.SHUTDOWN):
            logger.debug(
                "request_rejected_draining",
                path=request.url.path,
                mode=state.mode.value,
            )
            return JSONResponse(
                status_code=503,
                content={
                    "error": "Service is shutting down",
                    "retry_after": 30,
                },
                headers={"Retry-After": "30"},
            )

        # Track request
        await state.increment_requests()
        try:
            return await call_next(request)
        finally:
            await state.decrement_requests()


async def wait_for_requests_to_drain(
    timeout: float = 30.0,  # noqa: ASYNC109
    check_interval: float = 0.5,
) -> bool:
    """
    Wait for all active requests to complete.

    Args:
        timeout: Maximum time to wait in seconds
        check_interval: How often to check request count

    Returns:
        True if all requests drained, False if timeout reached
    """
    state = get_shutdown_state()
    start = datetime.now(UTC)

    while (datetime.now(UTC) - start).total_seconds() < timeout:
        if state.active_requests == 0:
            logger.info("all_requests_drained")
            return True

        logger.debug(
            "waiting_for_requests",
            active=state.active_requests,
            elapsed=(datetime.now(UTC) - start).total_seconds(),
        )
        await asyncio.sleep(check_interval)

    logger.warning(
        "request_drain_timeout",
        remaining=state.active_requests,
        timeout=timeout,
    )
    return False


@asynccontextmanager
async def graceful_shutdown_context(
    drain_timeout: float = 30.0,
    cleanup_callbacks: list[Callable] | None = None,
) -> AsyncIterator[None]:
    """
    Context manager for graceful shutdown.

    Usage:
        ```python
        async with graceful_shutdown_context(cleanup_callbacks=[cleanup_db]):
            yield
        # Shutdown happens here with draining
        ```

    Args:
        drain_timeout: How long to wait for requests to drain
        cleanup_callbacks: Async functions to call during cleanup
    """
    state = get_shutdown_state()
    cleanup_callbacks = cleanup_callbacks or []

    # Set up signal handlers
    shutdown_event = asyncio.Event()

    def handle_signal(sig: signal.Signals) -> None:
        logger.info("shutdown_signal_received", signal=sig.name)
        shutdown_event.set()

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        # Windows doesn't support add_signal_handler
        with contextlib.suppress(NotImplementedError):
            loop.add_signal_handler(sig, lambda s=sig: handle_signal(s))

    try:
        yield
    finally:
        # Start graceful shutdown
        logger.info("graceful_shutdown_starting")
        await state.start_draining()

        # Wait for in-flight requests
        await wait_for_requests_to_drain(timeout=drain_timeout)

        # Run cleanup callbacks
        for callback in cleanup_callbacks:
            try:
                logger.debug("running_cleanup_callback", callback=callback.__name__)
                await callback()
            except Exception as e:
                logger.exception(
                    "cleanup_callback_error",
                    callback=callback.__name__,
                    error=str(e),
                )

        # Update state to shutdown
        state.mode = ServiceMode.SHUTDOWN
        logger.info("graceful_shutdown_complete")


class DegradedModeManager:
    """
    Manages degraded mode for the service.

    When dependencies fail, the service can enter degraded mode to:
    - Serve cached responses
    - Return partial data
    - Skip non-critical features

    Usage:
        ```python
        degradation = DegradedModeManager()

        # When a dependency fails
        await degradation.mark_dependency_unhealthy("redis")

        # Check if feature should degrade
        if degradation.should_skip_feature("caching"):
            return cached_response

        # When dependency recovers
        await degradation.mark_dependency_healthy("redis")
        ```
    """

    def __init__(self) -> None:
        self._unhealthy_dependencies: set[str] = set()
        self._feature_dependencies: dict[str, set[str]] = {
            # Feature -> set of dependencies it requires
            "caching": {"redis"},
            "distributed_state": {"redis"},
            "permission_cache": {"redis"},
        }
        self._lock = asyncio.Lock()

    async def mark_dependency_unhealthy(self, dependency: str) -> None:
        """Mark a dependency as unhealthy."""
        async with self._lock:
            self._unhealthy_dependencies.add(dependency)

        state = get_shutdown_state()
        await state.enter_degraded_mode(f"Dependency unhealthy: {dependency}")

        logger.warning(
            "dependency_marked_unhealthy",
            dependency=dependency,
        )

    async def mark_dependency_healthy(self, dependency: str) -> None:
        """Mark a dependency as healthy again."""
        async with self._lock:
            self._unhealthy_dependencies.discard(dependency)
            remaining = len(self._unhealthy_dependencies)

        if remaining == 0:
            state = get_shutdown_state()
            await state.exit_degraded_mode()

        logger.info(
            "dependency_marked_healthy",
            dependency=dependency,
        )

    def should_skip_feature(self, feature: str) -> bool:
        """Check if a feature should be skipped due to degradation."""
        required_deps = self._feature_dependencies.get(feature, set())
        return bool(required_deps & self._unhealthy_dependencies)

    def get_unhealthy_dependencies(self) -> set[str]:
        """Get set of currently unhealthy dependencies."""
        return self._unhealthy_dependencies.copy()


# Global degradation manager
_degradation_manager: DegradedModeManager | None = None


def get_degradation_manager() -> DegradedModeManager:
    """Get the global degradation manager."""
    global _degradation_manager  # noqa: PLW0603
    if _degradation_manager is None:
        _degradation_manager = DegradedModeManager()
    return _degradation_manager
