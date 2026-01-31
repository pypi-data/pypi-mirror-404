"""Main IdentityPlanKit class - the primary entry point for the library."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from importlib.metadata import PackageNotFoundError, version

from fastapi import APIRouter, FastAPI
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from identity_plan_kit.auth.handlers.oauth_routes import create_auth_router
from identity_plan_kit.plans.handlers.plan_routes import create_plans_router
from identity_plan_kit.auth.services.auth_service import AuthService
from identity_plan_kit.config import IdentityPlanKitConfig
from identity_plan_kit.plans.services.plan_service import (
    AuthorizationCallback,
    PlanService,
)
from identity_plan_kit.rbac.services.rbac_service import RBACService
from identity_plan_kit.shared.database import DatabaseManager
from identity_plan_kit.shared.error_formatter import (
    DefaultErrorFormatter,
    ErrorFormatter,
    RFC7807ErrorFormatter,
)
from identity_plan_kit.shared.exception_handlers import register_exception_handlers
from identity_plan_kit.shared.graceful_shutdown import (
    GracefulShutdownMiddleware,
    get_shutdown_state,
    wait_for_requests_to_drain,
)
from identity_plan_kit.shared.health import HealthChecker, init_health_checker
from identity_plan_kit.shared.lockout import AccountLockedError, LockoutConfig
from identity_plan_kit.shared.logging import configure_logging, get_logger
from identity_plan_kit.shared.metrics import (
    MetricsManager,
    MetricsMiddleware,
    get_metrics_manager,
    init_metrics_manager,
    is_prometheus_available,
)
from identity_plan_kit.shared.rate_limiter import init_rate_limiter
from identity_plan_kit.shared.request_id import RequestIDMiddleware
from identity_plan_kit.shared.state_store import (
    StateStoreManager,
    check_state_store_health,
    close_state_store,
    get_state_store_manager,
    init_state_store,
)

logger = get_logger(__name__)

# Package version - read from package metadata to avoid duplication with pyproject.toml
try:
    __version__ = version("identity-plan-kit")
except PackageNotFoundError:
    # Package not installed (running from source)
    __version__ = "0.1.0.dev0"


class IdentityPlanKit:
    """
    Main IdentityPlanKit class.

    Provides a unified interface for authentication, RBAC, and plan management
    with production-ready features:

    - **Health checks**: /health, /health/live, /health/ready endpoints
    - **Graceful shutdown**: Request draining with configurable timeout
    - **Connection retry**: Database connection with exponential backoff
    - **Startup timeout**: Fail-fast if database is unreachable

    Example:
        ```python
        from fastapi import FastAPI
        from identity_plan_kit import IdentityPlanKit, IdentityPlanKitConfig

        config = IdentityPlanKitConfig(
            database_url="postgresql+asyncpg://...",
            secret_key="your-secret-key",
            google_client_id="...",
            google_client_secret="...",
            google_redirect_uri="...",
        )

        kit = IdentityPlanKit(
            config,
            startup_timeout=30.0,      # Fail-fast on DB unreachable
            shutdown_drain_timeout=30.0,  # Wait for requests to complete
        )

        # Option 1: Auto-setup with lifespan (recommended)
        app = FastAPI(lifespan=kit.lifespan)
        kit.setup(app)

        # Option 2: Manual lifecycle management
        @asynccontextmanager
        async def lifespan(app: FastAPI):
            await kit.startup()
            yield
            await kit.shutdown()

        app = FastAPI(lifespan=lifespan)
        kit.setup(app)
        ```

    Health Check Endpoints (when include_health_routes=True):
        - GET {api_prefix}/health - Full health status with component details
        - GET {api_prefix}/health/live - Liveness probe (k8s livenessProbe)
        - GET {api_prefix}/health/ready - Readiness probe (k8s readinessProbe)

    API Prefix:
        Configure `api_prefix` to mount all routes under a custom path:
        ```python
        config = IdentityPlanKitConfig(
            api_prefix="/api/v1",  # All routes under /api/v1
            ...
        )
        # Results in: /api/v1/auth, /api/v1/health, /api/v1/metrics
        ```
    """

    def __init__(
        self,
        config: IdentityPlanKitConfig,
        session_factory: async_sessionmaker[AsyncSession] | None = None,
        startup_timeout: float = 30.0,
        shutdown_drain_timeout: float = 30.0,
        authorization_callback: AuthorizationCallback | None = None,
    ) -> None:
        """
        Initialize IdentityPlanKit.

        Args:
            config: Library configuration
            session_factory: Optional external SQLAlchemy async session factory.
                If provided, IPK will use this instead of creating its own connection pool.
                This allows sharing a single database connection pool with your application.
            startup_timeout: Timeout for database connection during startup (seconds).
                Only used when session_factory is not provided.
            shutdown_drain_timeout: Timeout for draining requests during shutdown (seconds)
            authorization_callback: Optional callback to authorize plan management operations.
                If provided, the callback will be invoked before assign_plan, cancel_plan,
                extend_plan, update_plan_limits, and reset_usage operations.

        Example with authorization callback:
            ```python
            async def check_authorization(
                operation: str,
                target_user_id: UUID,
                context: dict | None
            ) -> bool:
                if context and context.get("is_webhook"):
                    return True  # Verified webhooks are authorized
                caller = context.get("caller_user_id") if context else None
                if context and context.get("is_admin"):
                    return True  # Admins can modify any user
                if caller == target_user_id:
                    return True  # Users can modify their own plans
                return False

            kit = IdentityPlanKit(config, authorization_callback=check_authorization)
            ```

        Example with external session factory (recommended for existing apps):
            ```python
            # Your existing app's session factory
            from your_app.database import session_factory

            kit = IdentityPlanKit(config, session_factory=session_factory)
            ```

        Example without (IPK creates its own pool):
            ```python
            kit = IdentityPlanKit(config)  # IPK manages database connections
            ```
        """
        self._config = config
        self._external_session_factory = session_factory
        self._startup_timeout = startup_timeout
        self._shutdown_drain_timeout = shutdown_drain_timeout
        self._authorization_callback = authorization_callback

        # Only create DatabaseManager if no external session factory provided
        self._db_manager: DatabaseManager | None = None if session_factory else DatabaseManager()
        self._session_factory: async_sessionmaker[AsyncSession] | None = session_factory

        self._auth_service: AuthService | None = None
        self._rbac_service: RBACService | None = None
        self._plan_service: PlanService | None = None
        self._auth_router: APIRouter | None = None
        self._plans_router: APIRouter | None = None
        self._health_checker: HealthChecker | None = None
        self._metrics_manager: MetricsManager | None = None

        # Configure logging based on environment (config.log_level overrides default)
        log_level = config.log_level or ("DEBUG" if config.is_development else "INFO")
        configure_logging(
            environment=config.environment,
            log_level=log_level,
        )

        logger.info(
            "identity_plan_kit_initialized",
            environment=config.environment.value,
            version=__version__,
            external_session_factory=session_factory is not None,
        )

    @property
    def config(self) -> IdentityPlanKitConfig:
        """Get configuration."""
        return self._config

    @property
    def auth_service(self) -> AuthService:
        """Get authentication service."""
        if self._auth_service is None:
            raise RuntimeError("IdentityPlanKit not started. Call startup() first.")
        return self._auth_service

    @property
    def rbac_service(self) -> RBACService:
        """Get RBAC service."""
        if self._rbac_service is None:
            raise RuntimeError("IdentityPlanKit not started. Call startup() first.")
        return self._rbac_service

    @property
    def plan_service(self) -> PlanService:
        """Get plan service."""
        if self._plan_service is None:
            raise RuntimeError("IdentityPlanKit not started. Call startup() first.")
        return self._plan_service

    @property
    def auth_router(self) -> APIRouter:
        """Get authentication router."""
        if self._auth_router is None:
            self._auth_router = create_auth_router(self._config)
        return self._auth_router

    @property
    def plans_router(self) -> APIRouter:
        """Get plans router."""
        if self._plans_router is None:
            self._plans_router = create_plans_router(self._config)
        return self._plans_router

    @property
    def health_checker(self) -> HealthChecker:
        """Get health checker for registering custom health checks."""
        if self._health_checker is None:
            self._health_checker = init_health_checker(version=__version__)
        return self._health_checker

    @property
    def metrics_manager(self) -> MetricsManager | None:
        """Get metrics manager (None if metrics disabled)."""
        return self._metrics_manager

    @property
    def db_manager(self) -> DatabaseManager | None:
        """
        Get the database manager for direct database access.

        Returns None if using external session factory (IPK doesn't own the connection pool).
        Useful for integrations like SQLAdmin that need the engine.

        Example:
            ```python
            from sqladmin import Admin
            if kit.db_manager:
                admin = Admin(app, kit.db_manager.engine)
            ```

        Raises:
            RuntimeError: If kit hasn't been started yet and db_manager exists
        """
        if self._db_manager is None:
            return None  # Using external session factory
        if not self._db_manager.is_initialized:
            raise RuntimeError("IdentityPlanKit not started. Call startup() first.")
        return self._db_manager

    @property
    def session_factory(self) -> async_sessionmaker[AsyncSession]:
        """
        Get the session factory for direct database access.

        This returns the session factory whether it's external or internal.

        Raises:
            RuntimeError: If kit hasn't been started yet
        """
        if self._session_factory is None:
            raise RuntimeError("IdentityPlanKit not started. Call startup() first.")
        return self._session_factory

    async def startup(self) -> None:
        """
        Initialize database and services.

        Call this during application startup.

        Raises:
            DatabaseStartupTimeoutError: If database connection times out (only when not using external session factory)
            DatabaseConnectionError: If database connection fails after retries (only when not using external session factory)
        """
        logger.info("identity_plan_kit_starting")

        # Initialize database or use external session factory
        if self._external_session_factory:
            # Using external session factory - no DB management needed
            self._session_factory = self._external_session_factory
            logger.info(
                "using_external_session_factory",
                message="Using external session factory. Database lifecycle managed by host application.",
            )
        else:
            # Initialize our own database with timeout and retry
            if self._db_manager is None:
                self._db_manager = DatabaseManager()
            await self._db_manager.init(
                self._config,
                startup_timeout=self._startup_timeout,
            )
            self._session_factory = self._db_manager.session_factory

        # Initialize state store for CSRF tokens
        # Uses Redis if configured, otherwise in-memory (single instance only)
        await init_state_store(
            redis_url=self._config.redis_url,
            require_redis=self._config.require_redis or False,
        )

        # Warn about potential issues with multi-instance deployments without Redis
        if self._config.is_production and not self._config.redis_url:
            logger.warning(
                "production_without_redis",
                message="Running in production without Redis. OAuth state tokens and "
                "rate limiting will not work correctly across multiple instances. "
                "Set IPK_REDIS_URL for multi-instance deployments.",
            )

        # Initialize rate limiter
        # Uses Redis if configured, otherwise in-memory
        init_rate_limiter(
            storage_uri=self._config.redis_url,
            trust_proxy=self._config.trust_proxy_headers,
        )

        # Initialize services with session factory and extension config
        extension_config = self._config.extension_config
        self._auth_service = AuthService(
            self._config,
            self._session_factory,
            extension_config=extension_config,
        )
        self._rbac_service = RBACService(self._config, self._session_factory)
        self._plan_service = PlanService(
            self._config,
            self._session_factory,
            plan_cache_ttl_seconds=self._config.plan_cache_ttl_seconds,
            user_plan_cache_ttl_seconds=self._config.plan_cache_ttl_seconds,
            redis_url=self._config.redis_url,
            require_redis=self._config.require_redis or False,
            state_store_manager=get_state_store_manager(),
            authorization_callback=self._authorization_callback,
        )

        # Connect service backends (Redis cache, etc.)
        await self._rbac_service.startup()
        await self._plan_service.startup()

        # Initialize health checker with component checks
        self._health_checker = init_health_checker(version=__version__)

        # Only register DB health check if we manage the database
        if self._db_manager is not None:
            self._health_checker.register_check(
                "database",
                self._db_manager.check_health,
                critical=True,
            )

        # Redis is critical only in multi-instance mode (when require_redis=True)
        self._health_checker.register_check(
            "state_store",
            check_state_store_health,
            critical=self._config.require_redis or False,
        )

        # Initialize metrics if enabled
        if self._config.enable_metrics:
            if is_prometheus_available():
                self._metrics_manager = init_metrics_manager()
                logger.info("metrics_enabled", path=self._config.metrics_path)
            else:
                logger.warning(
                    "metrics_requested_but_unavailable",
                    message="Install with: pip install identity-plan-kit[metrics]",
                )

        logger.info("identity_plan_kit_started")

    async def shutdown(self) -> None:
        """
        Cleanup resources with graceful shutdown.

        Enters draining mode, waits for in-flight requests to complete,
        then closes connections.

        Call this during application shutdown.
        """
        logger.info("identity_plan_kit_stopping")

        # Start draining - rejects new requests
        state = get_shutdown_state()
        await state.start_draining()

        # Wait for in-flight requests to complete
        drained = await wait_for_requests_to_drain(
            timeout=self._shutdown_drain_timeout,
        )

        if not drained:
            logger.warning(
                "shutdown_drain_incomplete",
                active_requests=state.active_requests,
            )

        # Shutdown services
        if self._rbac_service:
            await self._rbac_service.shutdown()

        if self._plan_service:
            await self._plan_service.shutdown()

        await close_state_store()

        # Only close database if we manage it (not external session factory)
        if self._db_manager is not None:
            await self._db_manager.close()

        logger.info("identity_plan_kit_stopped")

    def setup(
        self,
        app: FastAPI,
        register_error_handlers: bool = True,
        include_health_routes: bool = True,
        include_request_id: bool = True,
        error_formatter: ErrorFormatter | None = None,
    ) -> None:
        """
        Setup IdentityPlanKit with a FastAPI application.

        This adds:
        - Auth routes at {api_prefix}{auth_prefix} (default: /auth)
        - Health check routes at {api_prefix}/health (optional)
        - Metrics endpoint at {api_prefix}{metrics_path} (if metrics enabled)
        - Request ID middleware for tracing (optional)
        - Metrics middleware for request tracking (if metrics enabled)
        - Graceful shutdown middleware
        - Kit instance to app.state for dependency access
        - Exception handlers (optional)

        All routes respect the `api_prefix` config setting. For example, with
        `api_prefix="/api/v1"`, routes will be: /api/v1/auth, /api/v1/health, etc.

        Args:
            app: FastAPI application instance
            register_error_handlers: Whether to register centralized exception handlers
            include_health_routes: Whether to include health check routes
            include_request_id: Whether to add request ID middleware for tracing
            error_formatter: Custom error formatter for customizing error response format.
                Use RFC7807ErrorFormatter for RFC 7807 Problem Details format, or
                implement your own ErrorFormatter subclass.

        Example with custom error format:
            ```python
            from identity_plan_kit.shared.error_formatter import RFC7807ErrorFormatter

            kit.setup(
                app,
                error_formatter=RFC7807ErrorFormatter(
                    base_uri="https://api.example.com/errors"
                ),
            )
            ```
        """
        # Store kit in app state for dependency access
        app.state.identity_plan_kit = self

        # Add graceful shutdown middleware (tracks active requests)
        app.add_middleware(GracefulShutdownMiddleware)

        # P1 FIX: Add request ID middleware for request tracing
        # Added after GracefulShutdown so it runs first (middleware order is LIFO)
        if include_request_id:
            app.add_middleware(RequestIDMiddleware)

        # Add metrics middleware if enabled
        # Added after RequestID so metrics can access request_id
        if self._metrics_manager is not None and self._metrics_manager.enabled:
            app.add_middleware(MetricsMiddleware, metrics=self._metrics_manager)

        # Build prefixes with optional global api_prefix
        api_prefix = self._config.api_prefix.rstrip("/")
        auth_prefix = f"{api_prefix}{self._config.auth_prefix}"
        plans_prefix = f"{api_prefix}/plans"
        health_prefix = f"{api_prefix}/health"
        metrics_prefix = f"{api_prefix}{self._config.metrics_path}"

        # Add auth router
        app.include_router(
            self.auth_router,
            prefix=auth_prefix,
        )

        # Add plans router
        app.include_router(
            self.plans_router,
            prefix=plans_prefix,
        )

        # Add health check routes
        if include_health_routes:
            app.include_router(
                self.health_checker.router,
                prefix=health_prefix,
            )

        # Add metrics endpoint if enabled
        if self._metrics_manager is not None and self._metrics_manager.enabled:
            metrics_router = self._metrics_manager.create_router()
            app.include_router(
                metrics_router,
                prefix=metrics_prefix,
            )

        # Register exception handlers
        if register_error_handlers:
            register_exception_handlers(app, error_formatter=error_formatter)

        logger.info(
            "identity_plan_kit_setup_complete",
            api_prefix=api_prefix or "(none)",
            auth_prefix=auth_prefix,
            plans_prefix=plans_prefix,
            health_prefix=health_prefix if include_health_routes else None,
            error_handlers=register_error_handlers,
            error_formatter=type(error_formatter).__name__ if error_formatter else "DefaultErrorFormatter",
            request_id_middleware=include_request_id,
            metrics_enabled=self._metrics_manager is not None,
            metrics_prefix=metrics_prefix if self._metrics_manager else None,
        )

    @asynccontextmanager
    async def lifespan(self, _app: FastAPI) -> AsyncGenerator[None, None]:
        """
        Lifespan context manager for FastAPI.

        Usage:
            ```python
            kit = IdentityPlanKit(config)

            app = FastAPI(lifespan=kit.lifespan)
            kit.setup(app)
            ```
        """
        await self.startup()
        try:
            yield
        finally:
            await self.shutdown()

    async def cleanup_expired_tokens(self, batch_size: int = 1000) -> int:
        """
        Clean up expired and revoked refresh tokens.

        This function is designed to be called by your own scheduling mechanism.
        You can use any scheduler you prefer: APScheduler, Celery, cron, etc.

        Args:
            batch_size: Maximum tokens to delete per call (default: 1000)

        Returns:
            Number of tokens deleted

        Example with APScheduler:
            ```python
            from apscheduler.schedulers.asyncio import AsyncIOScheduler

            scheduler = AsyncIOScheduler()
            scheduler.add_job(
                kit.cleanup_expired_tokens,
                'interval',
                hours=6,
                kwargs={'batch_size': 1000},
            )
            scheduler.start()
            ```

        Example with Celery Beat:
            ```python
            @celery.task
            def cleanup_tokens():
                import asyncio
                asyncio.run(kit.cleanup_expired_tokens())
            ```

        Example with simple background task:
            ```python
            async def cleanup_loop():
                while True:
                    await asyncio.sleep(6 * 3600)  # 6 hours
                    await kit.cleanup_expired_tokens()

            asyncio.create_task(cleanup_loop())
            ```
        """
        if self._session_factory is None:
            raise RuntimeError("IdentityPlanKit not started. Call startup() first.")

        # Import here to avoid circular imports at module level
        from identity_plan_kit.auth.uow import AuthUnitOfWork  # noqa: PLC0415

        async with AuthUnitOfWork(self._session_factory) as uow:
            count: int = await uow.tokens.cleanup_expired(batch_size=batch_size)
            logger.info(
                "expired_tokens_cleaned",
                count=count,
                batch_size=batch_size,
            )

            # Record metrics if enabled
            if self._metrics_manager is not None:
                self._metrics_manager.record_tokens_cleaned(count)
                self._metrics_manager.record_token_operation("cleanup")

        return count


# Re-export commonly used items for convenience
__all__ = [
    # Lockout
    "AccountLockedError",
    # Manager classes
    "DatabaseManager",
    "IdentityPlanKit",
    "LockoutConfig",
    # Error formatters
    "DefaultErrorFormatter",
    "ErrorFormatter",
    "RFC7807ErrorFormatter",
    # Metrics (optional)
    "MetricsManager",
    "StateStoreManager",
    "__version__",
    "get_metrics_manager",
    "is_prometheus_available",
]
