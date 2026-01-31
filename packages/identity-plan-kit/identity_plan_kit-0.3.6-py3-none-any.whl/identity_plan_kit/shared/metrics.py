"""Prometheus metrics for IdentityPlanKit.

This module provides optional Prometheus metrics for monitoring and observability.
Metrics are only collected when enabled via configuration.

Installation:
    pip install identity-plan-kit[metrics]

Usage:
    config = IdentityPlanKitConfig(enable_metrics=True)
    kit = IdentityPlanKit(config)
    # Metrics available at /metrics endpoint
"""

from __future__ import annotations

import time
from collections.abc import Callable, Generator
from contextlib import contextmanager
from typing import TYPE_CHECKING, Any

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from starlette.routing import Match
from starlette.types import ASGIApp

from identity_plan_kit.shared.logging import get_logger

if TYPE_CHECKING:
    from fastapi import APIRouter

logger = get_logger(__name__)

# Check if prometheus_client is available
_prometheus_available = False
try:
    from prometheus_client import (
        CONTENT_TYPE_LATEST,
        CollectorRegistry,
        Counter,
        Gauge,
        Histogram,
        generate_latest,
    )

    _prometheus_available = True
except ImportError:
    # prometheus-client not installed
    pass


class MetricsManager:
    """
    Manages Prometheus metrics collection and exposure.

    This class encapsulates all metrics to avoid global state pollution
    and allows for proper cleanup in tests.

    Example:
        ```python
        metrics = MetricsManager()
        metrics.setup()

        # Track request
        with metrics.track_request("GET", "/api/users", 200):
            pass

        # Get metrics endpoint
        app.include_router(metrics.router, prefix="/metrics")
        ```
    """

    def __init__(self, registry: CollectorRegistry | None = None) -> None:
        """
        Initialize metrics manager.

        Args:
            registry: Optional custom registry. Uses default if not provided.
        """
        if not _prometheus_available:
            logger.warning(
                "prometheus_client_not_installed",
                message="Install with: pip install identity-plan-kit[metrics]",
            )
            self._enabled = False
            return

        self._enabled = True
        self._registry = registry or CollectorRegistry(auto_describe=True)
        self._setup_metrics()

    def _setup_metrics(self) -> None:
        """Set up all Prometheus metrics."""
        if not self._enabled:
            return

        # HTTP Request metrics
        self.http_requests_total = Counter(
            "ipk_http_requests_total",
            "Total HTTP requests",
            ["method", "endpoint", "status_code"],
            registry=self._registry,
        )

        self.http_request_duration_seconds = Histogram(
            "ipk_http_request_duration_seconds",
            "HTTP request duration in seconds",
            ["method", "endpoint"],
            buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
            registry=self._registry,
        )

        self.http_requests_in_progress = Gauge(
            "ipk_http_requests_in_progress",
            "Number of HTTP requests currently being processed",
            ["method"],
            registry=self._registry,
        )

        # Authentication metrics
        self.auth_attempts_total = Counter(
            "ipk_auth_attempts_total",
            "Total authentication attempts",
            ["provider", "result"],  # result: success, failure, error
            registry=self._registry,
        )

        self.token_operations_total = Counter(
            "ipk_token_operations_total",
            "Total token operations",
            ["operation"],  # operation: refresh, revoke, cleanup
            registry=self._registry,
        )

        self.tokens_cleaned_total = Counter(
            "ipk_tokens_cleaned_total",
            "Total expired tokens cleaned up",
            registry=self._registry,
        )

        # Circuit breaker metrics
        self.circuit_breaker_state = Gauge(
            "ipk_circuit_breaker_state",
            "Circuit breaker state (0=closed, 1=open, 2=half_open)",
            ["name"],
            registry=self._registry,
        )

        self.circuit_breaker_failures_total = Counter(
            "ipk_circuit_breaker_failures_total",
            "Total circuit breaker failures",
            ["name"],
            registry=self._registry,
        )

        # Database metrics
        self.db_connections_active = Gauge(
            "ipk_db_connections_active",
            "Number of active database connections",
            registry=self._registry,
        )

        self.db_query_duration_seconds = Histogram(
            "ipk_db_query_duration_seconds",
            "Database query duration in seconds",
            ["operation"],  # operation: select, insert, update, delete
            buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0),
            registry=self._registry,
        )

        # Quota/Usage metrics
        self.quota_checks_total = Counter(
            "ipk_quota_checks_total",
            "Total quota checks",
            ["feature", "result"],  # result: allowed, exceeded
            registry=self._registry,
        )

        self.quota_usage_ratio = Gauge(
            "ipk_quota_usage_ratio",
            "Current quota usage ratio (usage/limit)",
            ["feature"],
            registry=self._registry,
        )

        # Rate limiting metrics
        self.rate_limit_hits_total = Counter(
            "ipk_rate_limit_hits_total",
            "Total rate limit hits",
            ["endpoint"],
            registry=self._registry,
        )

        # Health check metrics
        self.health_check_duration_seconds = Histogram(
            "ipk_health_check_duration_seconds",
            "Health check duration in seconds",
            ["component"],
            buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5),
            registry=self._registry,
        )

        self.component_health_status = Gauge(
            "ipk_component_health_status",
            "Component health status (1=healthy, 0=unhealthy)",
            ["component"],
            registry=self._registry,
        )

        logger.info("metrics_initialized")

    @property
    def enabled(self) -> bool:
        """Check if metrics are enabled."""
        return self._enabled

    @contextmanager
    def track_request(
        self,
        method: str,
        endpoint: str,
    ) -> Generator[dict[str, Any], None, None]:
        """
        Context manager to track HTTP request metrics.

        Args:
            method: HTTP method
            endpoint: Request endpoint/path

        Yields:
            Dict to store status_code for the response
        """
        if not self._enabled:
            yield {}
            return

        context: dict[str, Any] = {"status_code": 500}
        start_time = time.perf_counter()
        self.http_requests_in_progress.labels(method=method).inc()

        try:
            yield context
        finally:
            duration = time.perf_counter() - start_time
            status_code = str(context.get("status_code", 500))

            self.http_requests_total.labels(
                method=method,
                endpoint=endpoint,
                status_code=status_code,
            ).inc()

            self.http_request_duration_seconds.labels(
                method=method,
                endpoint=endpoint,
            ).observe(duration)

            self.http_requests_in_progress.labels(method=method).dec()

    def record_auth_attempt(
        self,
        provider: str,
        result: str,
    ) -> None:
        """Record an authentication attempt."""
        if self._enabled:
            self.auth_attempts_total.labels(provider=provider, result=result).inc()

    def record_token_operation(self, operation: str) -> None:
        """Record a token operation (refresh, revoke, cleanup)."""
        if self._enabled:
            self.token_operations_total.labels(operation=operation).inc()

    def record_tokens_cleaned(self, count: int) -> None:
        """Record number of tokens cleaned up."""
        if self._enabled:
            self.tokens_cleaned_total.inc(count)

    def set_circuit_breaker_state(self, name: str, state: int) -> None:
        """Set circuit breaker state (0=closed, 1=open, 2=half_open)."""
        if self._enabled:
            self.circuit_breaker_state.labels(name=name).set(state)

    def record_circuit_breaker_failure(self, name: str) -> None:
        """Record a circuit breaker failure."""
        if self._enabled:
            self.circuit_breaker_failures_total.labels(name=name).inc()

    def set_db_connections(self, count: int) -> None:
        """Set the number of active database connections."""
        if self._enabled:
            self.db_connections_active.set(count)

    def record_quota_check(self, feature: str, result: str) -> None:
        """Record a quota check (allowed/exceeded)."""
        if self._enabled:
            self.quota_checks_total.labels(feature=feature, result=result).inc()

    def set_quota_usage(self, feature: str, ratio: float) -> None:
        """Set quota usage ratio for a feature."""
        if self._enabled:
            self.quota_usage_ratio.labels(feature=feature).set(ratio)

    def record_rate_limit_hit(self, endpoint: str) -> None:
        """Record a rate limit hit."""
        if self._enabled:
            self.rate_limit_hits_total.labels(endpoint=endpoint).inc()

    def record_health_check(
        self,
        component: str,
        duration: float,
        healthy: bool,
    ) -> None:
        """Record health check result."""
        if self._enabled:
            self.health_check_duration_seconds.labels(component=component).observe(duration)
            self.component_health_status.labels(component=component).set(1 if healthy else 0)

    def get_metrics(self) -> bytes:
        """Generate metrics output for Prometheus scraping."""
        if not self._enabled:
            return b"# Metrics disabled\n"
        return generate_latest(self._registry)

    def create_router(self, path: str = "") -> APIRouter:
        """
        Create FastAPI router for metrics endpoint.

        Args:
            path: Path for the metrics endpoint (empty for root)

        Returns:
            FastAPI router with metrics endpoint
        """
        # Import here to avoid requiring fastapi as mandatory dependency
        from fastapi import APIRouter  # noqa: PLC0415
        from fastapi.responses import Response as FastAPIResponse  # noqa: PLC0415

        router = APIRouter(tags=["metrics"])

        @router.get(path or "/", include_in_schema=False)
        async def metrics_endpoint() -> FastAPIResponse:
            """Prometheus metrics endpoint."""
            return FastAPIResponse(
                content=self.get_metrics(),
                media_type=CONTENT_TYPE_LATEST if self._enabled else "text/plain",
            )

        return router


class MetricsMiddleware(BaseHTTPMiddleware):
    """
    Middleware for collecting HTTP request metrics.

    Automatically tracks request count, duration, and in-progress requests.
    """

    def __init__(self, app: ASGIApp, metrics: MetricsManager) -> None:
        super().__init__(app)
        self._metrics = metrics

    def _get_endpoint_name(self, request: Request) -> str:
        """Extract endpoint name from request, normalizing path parameters."""
        # Try to get the route path template (e.g., /users/{user_id})
        for route in request.app.routes:
            match, _ = route.matches(request.scope)
            if match == Match.FULL:
                return getattr(route, "path", request.url.path)

        # Fallback to actual path (less ideal for cardinality)
        return request.url.path

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Any],
    ) -> Response:
        """Process request and collect metrics."""
        if not self._metrics.enabled:
            return await call_next(request)

        method = request.method
        endpoint = self._get_endpoint_name(request)

        with self._metrics.track_request(method, endpoint) as context:
            response = await call_next(request)
            context["status_code"] = response.status_code
            return response


# Global metrics instance (lazy initialization)
_metrics_manager: MetricsManager | None = None


def get_metrics_manager() -> MetricsManager | None:
    """Get the global metrics manager instance."""
    return _metrics_manager


def init_metrics_manager(registry: CollectorRegistry | None = None) -> MetricsManager:
    """
    Initialize the global metrics manager.

    Args:
        registry: Optional custom Prometheus registry

    Returns:
        Initialized MetricsManager instance
    """
    global _metrics_manager  # noqa: PLW0603
    _metrics_manager = MetricsManager(registry)
    return _metrics_manager


def is_prometheus_available() -> bool:
    """Check if prometheus_client is installed."""
    return _prometheus_available
