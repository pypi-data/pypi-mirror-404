"""Scheduled cleanup tasks for token and session management.

Provides integrated cleanup scheduling to prevent database bloat from
expired tokens and stale data.
"""

import asyncio
import random
import threading
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from enum import Enum
from typing import TYPE_CHECKING

from identity_plan_kit.shared.audit import audit_token_cleanup
from identity_plan_kit.shared.logging import get_logger

if TYPE_CHECKING:
    from identity_plan_kit.kit import IdentityPlanKit

logger = get_logger(__name__)


class CleanupInterval(Enum):
    """Predefined cleanup intervals."""

    HOURLY = timedelta(hours=1)
    DAILY = timedelta(days=1)
    WEEKLY = timedelta(weeks=1)


@dataclass
class CleanupConfig:
    """Configuration for cleanup scheduler."""

    # Token cleanup settings
    token_cleanup_interval: timedelta = timedelta(hours=6)
    token_cleanup_batch_size: int = 1000
    token_cleanup_enabled: bool = True

    # Maximum batches per run (prevents long-running cleanup)
    max_batches_per_run: int = 10

    # Jitter to prevent thundering herd (percentage of interval)
    jitter_percent: float = 0.1


class CleanupScheduler:
    """
    Background scheduler for cleanup tasks.

    P1 FIX: Provides integrated token cleanup scheduling to prevent
    database bloat from accumulated expired tokens.

    Example:
        ```python
        from identity_plan_kit import IdentityPlanKit

        kit = IdentityPlanKit(config)
        scheduler = CleanupScheduler(kit)

        # Start with FastAPI lifespan
        @asynccontextmanager
        async def lifespan(app: FastAPI):
            await kit.startup()
            scheduler.start()
            yield
            scheduler.stop()
            await kit.shutdown()
        ```
    """

    def __init__(
        self,
        cleanup_func: Callable[[int], Awaitable[int]],
        config: CleanupConfig | None = None,
    ) -> None:
        """
        Initialize cleanup scheduler.

        Args:
            cleanup_func: Async function that performs cleanup and returns count deleted.
                         Signature: async def cleanup(batch_size: int) -> int
            config: Cleanup configuration (uses defaults if None)
        """
        self._cleanup_func = cleanup_func
        self._config = config or CleanupConfig()
        self._task: asyncio.Task[None] | None = None
        self._running = False
        self._last_run: datetime | None = None
        self._total_cleaned: int = 0
        self._consecutive_failures: int = 0
        self._max_consecutive_failures: int = 3  # Stop after 3 consecutive failures
        self._lock = threading.Lock()  # Protects _running and _task

    @property
    def is_running(self) -> bool:
        """Check if scheduler is running."""
        return self._running

    @property
    def last_run(self) -> datetime | None:
        """Get timestamp of last cleanup run."""
        return self._last_run

    @property
    def total_cleaned(self) -> int:
        """Get total items cleaned since scheduler started."""
        return self._total_cleaned

    def start(self) -> None:
        """Start the cleanup scheduler background task."""
        with self._lock:
            if self._running:
                logger.warning("cleanup_scheduler_already_running")
                return

            if not self._config.token_cleanup_enabled:
                logger.info("cleanup_scheduler_disabled")
                return

            self._running = True
            self._task = asyncio.create_task(self._run_loop())
            # RELIABILITY FIX: Add task supervision to detect unexpected failures
            self._task.add_done_callback(self._handle_task_done)
            logger.info(
                "cleanup_scheduler_started",
                interval=str(self._config.token_cleanup_interval),
                batch_size=self._config.token_cleanup_batch_size,
            )

    def _handle_task_done(self, task: asyncio.Task[None]) -> None:
        """
        Handle cleanup task completion or failure.

        This callback is invoked when the background task completes,
        either normally (due to stop()) or unexpectedly (due to error).
        """
        if not self._running:
            # Task was intentionally stopped
            return

        try:
            # Check if task raised an exception
            exc = task.exception()
            if exc is not None:
                logger.error(
                    "cleanup_scheduler_task_failed",
                    error=str(exc),
                    error_type=type(exc).__name__,
                )
                # Attempt to restart the task
                self._attempt_restart()
        except asyncio.CancelledError:
            # Task was cancelled, which is expected during stop()
            logger.debug("cleanup_scheduler_task_cancelled")
        except asyncio.InvalidStateError:
            # Task hasn't completed yet (shouldn't happen in done callback)
            pass

    def _attempt_restart(self) -> None:
        """Attempt to restart the cleanup task after failure."""
        with self._lock:
            if not self._running:
                return

            self._consecutive_failures += 1

            if self._consecutive_failures >= self._max_consecutive_failures:
                logger.critical(
                    "cleanup_scheduler_max_failures_reached",
                    consecutive_failures=self._consecutive_failures,
                    message="Cleanup scheduler stopped due to repeated failures. Manual intervention required.",
                )
                self._running = False
                return

            logger.warning(
                "cleanup_scheduler_restarting",
                consecutive_failures=self._consecutive_failures,
                max_failures=self._max_consecutive_failures,
            )
            self._task = asyncio.create_task(self._run_loop())
            self._task.add_done_callback(self._handle_task_done)

    def stop(self) -> None:
        """Stop the cleanup scheduler."""
        with self._lock:
            if not self._running:
                return

            self._running = False
            if self._task:
                self._task.cancel()
                self._task = None

            logger.info(
                "cleanup_scheduler_stopped",
                total_cleaned=self._total_cleaned,
            )

    async def _run_loop(self) -> None:
        """Background loop that runs cleanup at intervals."""
        while self._running:
            try:
                # Calculate sleep time with jitter
                interval = self._config.token_cleanup_interval
                jitter_seconds = interval.total_seconds() * self._config.jitter_percent

                # random.uniform is fine for jitter (not cryptographic)
                actual_interval = interval.total_seconds() + random.uniform(  # noqa: S311
                    -jitter_seconds, jitter_seconds
                )

                await asyncio.sleep(actual_interval)

                if self._running:
                    await self.run_cleanup()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.exception(
                    "cleanup_scheduler_error",
                    error=str(e),
                )
                # Continue running despite errors
                await asyncio.sleep(60)  # Back off for a minute on error

    async def run_cleanup(self) -> int:
        """
        Run cleanup immediately (can be called manually).

        Returns:
            Total number of items cleaned
        """
        if not self._config.token_cleanup_enabled:
            return 0

        start_time = datetime.now(UTC)
        total_deleted = 0
        batches = 0

        try:
            while batches < self._config.max_batches_per_run:
                deleted = await self._cleanup_func(self._config.token_cleanup_batch_size)
                total_deleted += deleted
                batches += 1

                if deleted < self._config.token_cleanup_batch_size:
                    # No more to delete
                    break

            duration = (datetime.now(UTC) - start_time).total_seconds()

            logger.info(
                "cleanup_completed",
                total_deleted=total_deleted,
                batches=batches,
                duration_seconds=duration,
            )

            # Audit log
            audit_token_cleanup(
                deleted_count=total_deleted,
                batch_size=self._config.token_cleanup_batch_size,
                has_more=(batches >= self._config.max_batches_per_run),
            )

            self._last_run = datetime.now(UTC)
            self._total_cleaned += total_deleted
            # Reset consecutive failures on success
            self._consecutive_failures = 0

            return total_deleted  # noqa: TRY300

        except Exception as e:
            logger.exception(
                "cleanup_failed",
                error=str(e),
                batches_completed=batches,
                items_deleted=total_deleted,
            )
            raise

    def get_status(self) -> dict[str, bool | str | int | None]:
        """Get scheduler status for health checks."""
        return {
            "running": self._running,
            "enabled": self._config.token_cleanup_enabled,
            "last_run": self._last_run.isoformat() if self._last_run else None,
            "total_cleaned": self._total_cleaned,
            "interval": str(self._config.token_cleanup_interval),
            "batch_size": self._config.token_cleanup_batch_size,
            "consecutive_failures": self._consecutive_failures,
        }


def create_cleanup_scheduler_for_kit(
    kit: "IdentityPlanKit",
    config: CleanupConfig | None = None,
) -> CleanupScheduler:
    """
    Create a cleanup scheduler for an IdentityPlanKit instance.

    Convenience function that wires up the scheduler to use
    kit.cleanup_expired_tokens().

    Args:
        kit: IdentityPlanKit instance
        config: Optional cleanup configuration

    Returns:
        Configured CleanupScheduler

    Example:
        ```python
        kit = IdentityPlanKit(config)
        scheduler = create_cleanup_scheduler_for_kit(kit)

        # In your lifespan:
        await kit.startup()
        scheduler.start()
        yield
        scheduler.stop()
        await kit.shutdown()
        ```
    """
    # Check for required method instead of importing to avoid circular import
    if not hasattr(kit, "cleanup_expired_tokens") or not callable(kit.cleanup_expired_tokens):
        raise TypeError("Expected IdentityPlanKit instance with cleanup_expired_tokens method")

    return CleanupScheduler(
        cleanup_func=kit.cleanup_expired_tokens,
        config=config,
    )
