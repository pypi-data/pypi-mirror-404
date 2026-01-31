"""Database configuration and session management with production-ready features."""

import asyncio
from collections.abc import AsyncGenerator, Callable
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from functools import wraps
from typing import TYPE_CHECKING, ParamSpec, TypeVar

from sqlalchemy import MetaData, text

if TYPE_CHECKING:
    from identity_plan_kit.shared.health import ComponentHealth
from sqlalchemy.exc import DBAPIError, OperationalError
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase
from tenacity import (
    RetryError,
    before_sleep_log,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from identity_plan_kit.config import IdentityPlanKitConfig
from identity_plan_kit.shared.logging import get_logger

logger = get_logger(__name__)

P = ParamSpec("P")
T = TypeVar("T")


# Retry configuration for transient database errors
RETRYABLE_EXCEPTIONS = (OperationalError, DBAPIError, OSError, ConnectionRefusedError)

# Startup defaults
DEFAULT_STARTUP_TIMEOUT = 30.0
DEFAULT_CONNECTION_RETRY_ATTEMPTS = 5
DEFAULT_CONNECTION_RETRY_MAX_WAIT = 10.0


class DatabaseConnectionError(Exception):
    """Raised when database connection fails after retries."""

    pass


class DatabaseStartupTimeoutError(Exception):
    """Raised when database startup exceeds timeout."""

    pass


def with_db_retry(
    max_attempts: int = 3,
    min_wait: float = 0.1,
    max_wait: float = 2.0,
) -> Callable[[Callable[P, T]], Callable[P, T]]:
    """
    Decorator for retrying database operations on transient failures.

    Retries on OperationalError and DBAPIError (connection issues,
    pool exhaustion, network glitches).

    Args:
        max_attempts: Maximum retry attempts (default: 3)
        min_wait: Minimum wait between retries in seconds (default: 0.1)
        max_wait: Maximum wait between retries in seconds (default: 2.0)

    Example:
        @with_db_retry()
        async def get_user(self, user_id: UUID) -> User | None:
            ...
    """

    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        @wraps(func)
        @retry(
            retry=retry_if_exception_type(RETRYABLE_EXCEPTIONS),
            stop=stop_after_attempt(max_attempts),
            wait=wait_exponential(multiplier=min_wait, max=max_wait),
            reraise=True,
        )
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            return await func(*args, **kwargs)  # type: ignore[misc]

        return wrapper  # type: ignore[return-value]

    return decorator


# Naming convention for constraints (helps with migrations)
NAMING_CONVENTION: dict[str, str] = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""

    metadata = MetaData(naming_convention=NAMING_CONVENTION)


class DatabaseManager:
    """
    Manages database connections and sessions.

    P1 FIX: Replaces global state with an injectable, testable class.
    Each IdentityPlanKit instance owns its own DatabaseManager.

    Example:
        ```python
        db = DatabaseManager()
        await db.init(config)

        async with db.session() as session:
            result = await session.execute(query)

        await db.close()
        ```
    """

    def __init__(self) -> None:
        self._engine: AsyncEngine | None = None
        self._session_factory: async_sessionmaker[AsyncSession] | None = None

    @property
    def engine(self) -> AsyncEngine:
        """Get the database engine."""
        if self._engine is None:
            raise RuntimeError("Database not initialized. Call init() first.")
        return self._engine

    @property
    def session_factory(self) -> async_sessionmaker[AsyncSession]:
        """Get the session factory for dependency injection."""
        if self._session_factory is None:
            raise RuntimeError("Database not initialized. Call init() first.")
        return self._session_factory

    @property
    def is_initialized(self) -> bool:
        """Check if database has been initialized."""
        return self._engine is not None and self._session_factory is not None

    async def _verify_connection_with_retry(
        self,
        max_attempts: int,
        max_wait: float,
    ) -> None:
        """Verify database connection with retry logic."""

        @retry(
            retry=retry_if_exception_type(RETRYABLE_EXCEPTIONS),
            stop=stop_after_attempt(max_attempts),
            wait=wait_exponential(multiplier=1, min=1, max=max_wait),
            before_sleep=before_sleep_log(logger, log_level=20),  # INFO
            reraise=True,
        )
        async def _verify() -> None:
            async with self._engine.begin() as conn:  # type: ignore[union-attr]
                await conn.execute(text("SELECT 1"))
            logger.debug("database_connection_verified")

        await _verify()

    async def _cleanup_on_failure(self) -> None:
        """Cleanup engine on failed initialization."""
        if self._engine is not None:
            await self._engine.dispose()
            self._engine = None
            self._session_factory = None

    async def init(
        self,
        config: IdentityPlanKitConfig,
        startup_timeout: float = DEFAULT_STARTUP_TIMEOUT,
        retry_attempts: int = DEFAULT_CONNECTION_RETRY_ATTEMPTS,
        retry_max_wait: float = DEFAULT_CONNECTION_RETRY_MAX_WAIT,
    ) -> None:
        """
        Initialize the database engine and session factory with retry and timeout.

        Args:
            config: IdentityPlanKit configuration
            startup_timeout: Maximum time to wait for database connection (seconds)
            retry_attempts: Number of connection retry attempts
            retry_max_wait: Maximum wait between retries (seconds)

        Raises:
            DatabaseStartupTimeoutError: If connection times out
            DatabaseConnectionError: If connection fails after retries
        """
        logger.info(
            "initializing_database",
            pool_size=config.database_pool_size,
            echo=config.database_echo,
            startup_timeout=startup_timeout,
            retry_attempts=retry_attempts,
            statement_timeout_ms=config.database_statement_timeout_ms,
        )

        # Create engine with connection and query timeouts
        self._engine = create_async_engine(
            config.database_url,
            echo=config.database_echo,
            pool_size=config.database_pool_size,
            max_overflow=10,
            pool_pre_ping=True,
            pool_recycle=3600,  # Recycle connections after 1 hour
            connect_args={
                "server_settings": {
                    "statement_timeout": str(config.database_statement_timeout_ms),
                },
            },
        )

        self._session_factory = async_sessionmaker(
            bind=self._engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
        )

        # Attempt connection with timeout and retry
        try:
            await asyncio.wait_for(
                self._verify_connection_with_retry(retry_attempts, retry_max_wait),
                timeout=startup_timeout,
            )
        except TimeoutError as e:
            logger.exception(
                "database_startup_timeout",
                timeout=startup_timeout,
            )
            await self._cleanup_on_failure()
            raise DatabaseStartupTimeoutError(
                f"Database connection timed out after {startup_timeout}s"
            ) from e
        except RetryError as e:
            last_error = e.last_attempt.exception() if e.last_attempt else None
            logger.exception(
                "database_connection_failed",
                attempts=retry_attempts,
                error=str(last_error),
            )
            await self._cleanup_on_failure()
            raise DatabaseConnectionError(
                f"Failed to connect to database after {retry_attempts} attempts: {last_error}"
            ) from e
        except Exception as e:
            logger.exception(
                "database_connection_error",
                error=str(e),
            )
            await self._cleanup_on_failure()
            raise DatabaseConnectionError(f"Database connection failed: {e}") from e

        logger.info("database_initialized")

    async def close(self) -> None:
        """Close the database engine and cleanup connections."""
        if self._engine is not None:
            logger.info("closing_database")
            await self._engine.dispose()
            self._engine = None
            self._session_factory = None
            logger.info("database_closed")

    @asynccontextmanager
    async def session(self) -> AsyncGenerator[AsyncSession, None]:
        """
        Get an async database session.

        Usage:
            async with db.session() as session:
                result = await session.execute(query)

        Yields:
            An AsyncSession instance
        """
        if self._session_factory is None:
            raise RuntimeError("Database not initialized. Call init() first.")

        async with self._session_factory() as session:
            try:
                yield session
                await session.commit()
            except BaseException:
                # Use BaseException to catch all exceptions including KeyboardInterrupt
                # and ensure proper rollback of database transactions
                await session.rollback()
                raise

    async def verify_connection(self) -> bool:
        """
        Verify database connection is working.

        Returns:
            True if connection is successful

        Raises:
            RuntimeError: If database is not initialized
        """
        if self._engine is None:
            raise RuntimeError("Database not initialized. Call init() first.")

        async with self._engine.begin() as conn:
            await conn.execute(text("SELECT 1"))

        logger.debug("database_connection_verified")
        return True

    async def get_health_status(self) -> dict[str, bool | str]:
        """
        Get database health status.

        Returns:
            Dict with health information
        """
        try:
            await self.verify_connection()
            return {"healthy": True}  # noqa: TRY300
        except Exception as e:
            logger.exception("database_health_check_failed", error=str(e))
            return {"healthy": False, "error": str(e)}

    async def check_health(self) -> "ComponentHealth":
        """
        Health check function for HealthChecker integration.

        Returns:
            ComponentHealth with database status
        """
        # Import here to avoid circular imports
        from identity_plan_kit.shared.health import ComponentHealth, HealthStatus  # noqa: PLC0415

        start = datetime.now(UTC)
        try:
            await self.verify_connection()
            latency = (datetime.now(UTC) - start).total_seconds() * 1000
            return ComponentHealth(
                name="database",
                status=HealthStatus.HEALTHY,
                latency_ms=latency,
            )
        except RuntimeError:
            return ComponentHealth(
                name="database",
                status=HealthStatus.UNHEALTHY,
                error="Database not initialized",
            )
        except Exception as e:
            return ComponentHealth(
                name="database",
                status=HealthStatus.UNHEALTHY,
                error=str(e),
            )

    async def create_tables(self) -> None:
        """
        Create all tables defined in the models.

        Warning: Only use this in development/testing. Use Alembic migrations
        in production.
        """
        if self._engine is None:
            raise RuntimeError("Database not initialized. Call init() first.")

        logger.warning("creating_tables", warning="Use migrations in production")
        async with self._engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("tables_created")

    async def drop_tables(self) -> None:
        """
        Drop all tables.

        Warning: This will delete all data! Only use in development/testing.
        """
        if self._engine is None:
            raise RuntimeError("Database not initialized. Call init() first.")

        logger.warning("dropping_tables", warning="This will delete all data!")
        async with self._engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        logger.info("tables_dropped")
