"""Integration test fixtures using testcontainers.

Provides real PostgreSQL database fixtures for high-confidence testing.
"""

from collections.abc import AsyncGenerator, Callable, Generator
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

# Skip entire module if testcontainers not available
pytest.importorskip("testcontainers")

from testcontainers.postgres import PostgresContainer

from identity_plan_kit.shared.database import Base


# =============================================================================
# Database Fixtures
# =============================================================================

# Module-level container singleton (shared across tests in a module)
_container: PostgresContainer | None = None
_engine: AsyncEngine | None = None


@pytest.fixture(scope="module")
def postgres_container() -> Generator[PostgresContainer, None, None]:
    """Start a PostgreSQL container for the test module."""
    global _container
    if _container is None:
        _container = PostgresContainer("postgres:15-alpine")
        _container.start()
    yield _container
    # Don't stop here - let module cleanup handle it


@pytest.fixture(scope="module")
def database_url(postgres_container: PostgresContainer) -> str:
    """Get the async database URL from the container."""
    sync_url = postgres_container.get_connection_url()
    return sync_url.replace("psycopg2", "asyncpg")


@pytest.fixture
async def db_engine(database_url: str) -> AsyncGenerator[AsyncEngine, None]:
    """Create async database engine connected to the container."""
    engine = create_async_engine(
        database_url,
        echo=False,
        pool_size=10,
        max_overflow=20,
    )

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    await engine.dispose()


@pytest.fixture
def session_factory(db_engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    """Create a session factory for services."""
    return async_sessionmaker(
        db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )


@pytest.fixture
async def db_session(db_engine: AsyncEngine) -> AsyncGenerator[AsyncSession, None]:
    """Create a database session with transaction rollback for test isolation."""
    async_session_factory = async_sessionmaker(
        db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session_factory() as session:
        async with session.begin():
            yield session
            await session.rollback()


# =============================================================================
# Data Factory Fixtures
# =============================================================================


@pytest.fixture
def create_test_role(db_session: AsyncSession) -> Callable[..., Any]:
    """Factory to create test roles."""
    from identity_plan_kit.rbac.models.role import RoleModel

    async def _create(code: str = "user", name: str = "User") -> int:
        role = RoleModel(code=code, name=name)
        db_session.add(role)
        await db_session.flush()
        return role.id

    return _create


@pytest.fixture
def create_test_user(
    db_session: AsyncSession,
    create_test_role: Callable[..., Any],
) -> Callable[..., Any]:
    """Factory to create test users."""
    from identity_plan_kit.auth.models.user import UserModel

    async def _create(
        email: str = "test@example.com",
        role_code: str = "user",
        is_active: bool = True,
        display_name: str | None = None,
        picture_url: str | None = None,
    ) -> UUID:
        # Check if role exists
        result = await db_session.execute(
            text("SELECT id FROM roles WHERE code = :code").bindparams(code=role_code)
        )
        row = result.fetchone()
        role_id = row[0] if row else await create_test_role(code=role_code, name=role_code.title())

        # Default display_name to email prefix if not provided
        if display_name is None:
            display_name = email.split("@")[0]

        user = UserModel(
            email=email,
            role_id=role_id,
            display_name=display_name,
            picture_url=picture_url,
            is_active=is_active,
            is_verified=True,
        )
        db_session.add(user)
        await db_session.flush()
        return user.id

    return _create


@pytest.fixture
def create_test_refresh_token(db_session: AsyncSession) -> Callable[..., Any]:
    """Factory to create test refresh tokens."""
    from identity_plan_kit.auth.models.refresh_token import RefreshTokenModel

    async def _create(
        user_id: UUID,
        token_hash: str = "test_hash",
        expires_days: int = 30,
        expires_at: datetime | None = None,
        revoked: bool = False,
    ) -> UUID:
        token = RefreshTokenModel(
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at or (datetime.now(UTC) + timedelta(days=expires_days)),
            revoked_at=datetime.now(UTC) if revoked else None,
        )
        db_session.add(token)
        await db_session.flush()
        return token.id

    return _create


@pytest.fixture
def create_plan(db_session: AsyncSession) -> Callable[..., Any]:
    """Factory to create test plans."""
    from identity_plan_kit.plans.models.plan import PlanModel

    async def _create(code: str = "free", name: str = "Free Plan") -> int:
        plan = PlanModel(code=code, name=name)
        db_session.add(plan)
        await db_session.flush()
        return plan.id

    return _create


@pytest.fixture
def create_feature(db_session: AsyncSession) -> Callable[..., Any]:
    """Factory to create test features."""
    from identity_plan_kit.plans.models.feature import FeatureModel

    async def _create(code: str = "api_calls", name: str = "API Calls") -> int:
        feature = FeatureModel(code=code, name=name)
        db_session.add(feature)
        await db_session.flush()
        return feature.id

    return _create


@pytest.fixture
def create_plan_limit(db_session: AsyncSession) -> Callable[..., Any]:
    """Factory to create test plan limits."""
    from identity_plan_kit.plans.models.plan_limit import PlanLimitModel

    async def _create(
        plan_id: int,
        feature_id: int,
        limit: int = 100,
        period: str | None = "daily",
    ) -> int:
        plan_limit = PlanLimitModel(
            plan_id=plan_id,
            feature_id=feature_id,
            feature_limit=limit,
            period=period,
        )
        db_session.add(plan_limit)
        await db_session.flush()
        return plan_limit.id

    return _create


@pytest.fixture
def create_user_plan(db_session: AsyncSession) -> Callable[..., Any]:
    """Factory to create test user plans."""
    from datetime import date

    from identity_plan_kit.plans.models.user_plan import UserPlanModel

    async def _create(
        user_id: UUID,
        plan_id: int,
        days_remaining: int = 30,
    ) -> int:
        user_plan = UserPlanModel(
            user_id=user_id,
            plan_id=plan_id,
            started_at=date.today(),
            ends_at=date.today() + timedelta(days=days_remaining),
        )
        db_session.add(user_plan)
        await db_session.flush()
        return user_plan.id

    return _create


@pytest.fixture
def create_feature_usage(db_session: AsyncSession) -> Callable[..., Any]:
    """Factory to create test feature usage records."""
    from datetime import date

    from identity_plan_kit.plans.models.feature_usage import FeatureUsageModel

    async def _create(
        user_plan_id: int,
        feature_id: int,
        usage: int = 0,
        start_period: date | None = None,
        end_period: date | None = None,
    ) -> int:
        today = date.today()
        usage_record = FeatureUsageModel(
            user_plan_id=user_plan_id,
            feature_id=feature_id,
            feature_usage=usage,
            start_period=start_period or today,
            end_period=end_period or today,
        )
        db_session.add(usage_record)
        await db_session.flush()
        return usage_record.id

    return _create
