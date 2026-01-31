"""Health check endpoints and status monitoring."""

from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any

from fastapi import APIRouter, Response, status

from identity_plan_kit.shared.logging import get_logger

logger = get_logger(__name__)

# Type alias for health check functions
HealthCheckFn = Callable[[], Awaitable["ComponentHealth"]]


class HealthStatus(str, Enum):
    """Health check status."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


@dataclass
class ComponentHealth:
    """Health status for a single component."""

    name: str
    status: HealthStatus
    latency_ms: float | None = None
    error: str | None = None
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class SystemHealth:
    """Overall system health status."""

    status: HealthStatus
    version: str
    uptime_seconds: float
    components: list[ComponentHealth]
    timestamp: str = field(default_factory=lambda: datetime.now(UTC).isoformat())

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON response."""
        return {
            "status": self.status.value,
            "version": self.version,
            "uptime_seconds": round(self.uptime_seconds, 2),
            "timestamp": self.timestamp,
            "components": [
                {
                    "name": c.name,
                    "status": c.status.value,
                    "latency_ms": round(c.latency_ms, 2) if c.latency_ms else None,
                    "error": c.error,
                    **c.details,
                }
                for c in self.components
            ],
        }


class HealthChecker:
    """
    Health check manager for monitoring system components.

    Provides both liveness and readiness probes for Kubernetes deployments:
    - /health/live: Is the process running? (always returns 200 if reachable)
    - /health/ready: Can the service handle requests? (checks dependencies)
    - /health: Full health status with component details

    Example:
        ```python
        health_checker = HealthChecker(version="1.0.0")

        # Register component checks
        health_checker.register_check("database", check_database_health)
        health_checker.register_check("redis", check_redis_health)

        # Add router to app
        app.include_router(health_checker.router, prefix="/health")
        ```
    """

    def __init__(self, version: str = "0.1.0") -> None:
        """
        Initialize health checker.

        Args:
            version: Application version string
        """
        self._version = version
        self._start_time = datetime.now(UTC)
        self._checks: dict[str, Any] = {}
        self._router = APIRouter(tags=["health"])
        self._setup_routes()

    @property
    def router(self) -> APIRouter:
        """Get the health check router."""
        return self._router

    @property
    def uptime_seconds(self) -> float:
        """Get uptime in seconds."""
        return (datetime.now(UTC) - self._start_time).total_seconds()

    def register_check(
        self,
        name: str,
        check_fn: HealthCheckFn,
        critical: bool = True,
    ) -> None:
        """
        Register a health check function.

        Args:
            name: Component name
            check_fn: Async function that returns ComponentHealth
            critical: If True, failure makes system unhealthy. If False, degraded.
        """
        self._checks[name] = {"fn": check_fn, "critical": critical}
        logger.debug("health_check_registered", component=name, critical=critical)

    async def check_health(self) -> SystemHealth:
        """
        Run all health checks and return system status.

        Returns:
            SystemHealth with all component statuses
        """
        components: list[ComponentHealth] = []
        has_critical_failure = False
        has_any_failure = False

        for name, config in self._checks.items():
            try:
                start = datetime.now(UTC)
                component = await config["fn"]()
                component.latency_ms = (datetime.now(UTC) - start).total_seconds() * 1000

                if component.status != HealthStatus.HEALTHY:
                    has_any_failure = True
                    if config["critical"]:
                        has_critical_failure = True

                components.append(component)

            except Exception as e:
                logger.exception(
                    "health_check_error",
                    component=name,
                    error=str(e),
                )
                components.append(
                    ComponentHealth(
                        name=name,
                        status=HealthStatus.UNHEALTHY,
                        error=str(e),
                    )
                )
                has_any_failure = True
                if config["critical"]:
                    has_critical_failure = True

        # Determine overall status
        if has_critical_failure:
            overall_status = HealthStatus.UNHEALTHY
        elif has_any_failure:
            overall_status = HealthStatus.DEGRADED
        else:
            overall_status = HealthStatus.HEALTHY

        return SystemHealth(
            status=overall_status,
            version=self._version,
            uptime_seconds=self.uptime_seconds,
            components=components,
        )

    def _setup_routes(self) -> None:
        """Set up health check routes."""

        @self._router.get(
            "",
            summary="Full health check",
            description="Returns detailed health status of all components",
        )
        async def health_check(response: Response) -> dict[str, Any]:
            """Full health check with component details."""
            health = await self.check_health()

            if health.status == HealthStatus.UNHEALTHY:
                response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
            elif health.status == HealthStatus.DEGRADED:
                response.status_code = status.HTTP_200_OK  # Still serving

            return health.to_dict()

        @self._router.get(
            "/live",
            summary="Liveness probe",
            description="Returns 200 if process is running (k8s liveness)",
        )
        async def liveness() -> dict[str, str]:
            """Liveness probe - is the process running?"""
            return {"status": "alive"}

        @self._router.get(
            "/ready",
            summary="Readiness probe",
            description="Returns 200 if service can handle requests (k8s readiness)",
        )
        async def readiness(response: Response) -> dict[str, Any]:
            """Readiness probe - can we handle requests?"""
            health = await self.check_health()

            if health.status == HealthStatus.UNHEALTHY:
                response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
                return {
                    "status": "not_ready",
                    "reason": "Critical components unhealthy",
                }

            return {"status": "ready"}


# Default health checker instance
_health_checker: HealthChecker | None = None


def get_health_checker() -> HealthChecker:
    """Get the global health checker instance."""
    global _health_checker  # noqa: PLW0603
    if _health_checker is None:
        _health_checker = HealthChecker()
    return _health_checker


def init_health_checker(version: str = "0.1.0") -> HealthChecker:
    """
    Initialize the global health checker.

    Args:
        version: Application version

    Returns:
        Configured HealthChecker instance
    """
    global _health_checker  # noqa: PLW0603
    _health_checker = HealthChecker(version=version)
    return _health_checker
