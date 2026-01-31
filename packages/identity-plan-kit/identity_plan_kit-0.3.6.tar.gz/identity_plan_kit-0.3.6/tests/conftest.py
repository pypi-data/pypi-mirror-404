"""Shared test fixtures and configuration."""

import asyncio
from collections.abc import AsyncGenerator
from datetime import UTC, date, datetime, timedelta
from typing import Any
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from identity_plan_kit.auth.domain.entities import RefreshToken, User
from identity_plan_kit.auth.services.auth_service import AuthService
from identity_plan_kit.config import IdentityPlanKitConfig
from identity_plan_kit.plans.domain.entities import PeriodType, Plan, PlanLimit, UserPlan
from identity_plan_kit.plans.services.plan_service import PlanService
from identity_plan_kit.rbac.services.rbac_service import RBACService
from identity_plan_kit.shared.lockout import LockoutConfig, LockoutManager
from identity_plan_kit.shared.rate_limiter import init_rate_limiter
from identity_plan_kit.shared.security import create_access_token, create_refresh_token
from identity_plan_kit.shared.state_store import InMemoryStateStore, StateStoreManager


# =============================================================================
# Test Constants
# =============================================================================

# Role IDs used in test fixtures (UUIDs for consistency with production schema)
TEST_ADMIN_ROLE_ID = UUID("00000000-0000-0000-0000-000000000001")
TEST_USER_ROLE_ID = UUID("00000000-0000-0000-0000-000000000002")


# =============================================================================
# Session & Event Loop Fixtures
# =============================================================================


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for the test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# =============================================================================
# Configuration Fixtures
# =============================================================================


@pytest.fixture
def mock_config() -> IdentityPlanKitConfig:
    """Create a mock configuration."""
    return IdentityPlanKitConfig(
        database_url="postgresql+asyncpg://test:test@localhost:5432/test",
        secret_key="test-secret-key-that-is-at-least-32-chars",
        google_client_id="test-client-id",
        google_client_secret="test-client-secret",
        google_redirect_uri="http://localhost:8000/auth/google/callback",
        access_token_expire_minutes=15,
        refresh_token_expire_days=30,
    )


@pytest.fixture
def secret_key() -> str:
    """Get the test secret key."""
    return "test-secret-key-that-is-at-least-32-chars"


# =============================================================================
# Entity Fixtures
# =============================================================================


@pytest.fixture
def mock_user() -> User:
    """Create a mock user entity."""
    return User(
        id=UUID("12345678-1234-1234-1234-123456789012"),
        email="test@example.com",
        role_id=TEST_USER_ROLE_ID,
        display_name="Test User",
        picture_url="https://lh3.googleusercontent.com/a-/test",
        is_active=True,
        is_verified=True,
        role_code="user",
    )


@pytest.fixture
def mock_inactive_user() -> User:
    """Create a mock inactive user entity."""
    return User(
        id=UUID("12345678-1234-1234-1234-123456789013"),
        email="inactive@example.com",
        role_id=TEST_USER_ROLE_ID,
        display_name="Inactive User",
        picture_url=None,
        is_active=False,
        is_verified=True,
        role_code="user",
    )


@pytest.fixture
def mock_admin_user() -> User:
    """Create a mock admin user entity."""
    return User(
        id=UUID("12345678-1234-1234-1234-123456789014"),
        email="admin@example.com",
        role_id=TEST_ADMIN_ROLE_ID,
        display_name="Admin User",
        picture_url="https://lh3.googleusercontent.com/a-/admin",
        is_active=True,
        is_verified=True,
        role_code="admin",
    )


@pytest.fixture
def mock_refresh_token(mock_user: User) -> RefreshToken:
    """Create a mock refresh token entity."""
    return RefreshToken(
        id=UUID("87654321-4321-4321-4321-210987654321"),
        user_id=mock_user.id,
        token_hash="mock_hash",
        expires_at=datetime.now(UTC) + timedelta(days=30),
        created_at=datetime.now(UTC),
    )


@pytest.fixture
def mock_revoked_token(mock_user: User) -> RefreshToken:
    """Create a mock revoked refresh token entity."""
    return RefreshToken(
        id=UUID("87654321-4321-4321-4321-210987654322"),
        user_id=mock_user.id,
        token_hash="revoked_hash",
        expires_at=datetime.now(UTC) + timedelta(days=30),
        created_at=datetime.now(UTC),
        revoked_at=datetime.now(UTC) - timedelta(hours=1),
    )


@pytest.fixture
def mock_expired_token(mock_user: User) -> RefreshToken:
    """Create a mock expired refresh token entity."""
    return RefreshToken(
        id=UUID("87654321-4321-4321-4321-210987654323"),
        user_id=mock_user.id,
        token_hash="expired_hash",
        expires_at=datetime.now(UTC) - timedelta(days=1),
        created_at=datetime.now(UTC) - timedelta(days=31),
    )


# =============================================================================
# Plan Entity Fixtures
# =============================================================================


@pytest.fixture
def mock_plan() -> Plan:
    """Create a mock plan entity."""
    return Plan(
        id=1,
        code="free",
        name="Free Plan",
        permissions={"read:data"},
        limits={
            "api_calls": PlanLimit(
                id=1,
                plan_id=1,
                feature_id=1,
                feature_code="api_calls",
                limit=100,
                period=PeriodType.DAILY,
            )
        },
    )


@pytest.fixture
def mock_plan_limit() -> PlanLimit:
    """Create a mock plan limit."""
    return PlanLimit(
        id=1,
        plan_id=1,
        feature_id=1,
        feature_code="api_calls",
        limit=100,
        period=PeriodType.DAILY,
    )


@pytest.fixture
def mock_unlimited_plan_limit() -> PlanLimit:
    """Create a mock unlimited plan limit."""
    return PlanLimit(
        id=2,
        plan_id=2,
        feature_id=1,
        feature_code="api_calls",
        limit=-1,  # Unlimited
        period=PeriodType.DAILY,
    )


@pytest.fixture
def mock_user_plan(mock_user: User) -> UserPlan:
    """Create a mock user plan."""
    return UserPlan(
        id=1,
        user_id=mock_user.id,
        plan_id=1,
        plan_code="free",
        started_at=date.today() - timedelta(days=10),
        ends_at=date.today() + timedelta(days=20),
        custom_limits={},
    )


@pytest.fixture
def mock_expired_user_plan(mock_user: User) -> UserPlan:
    """Create a mock expired user plan."""
    return UserPlan(
        id=2,
        user_id=mock_user.id,
        plan_id=1,
        plan_code="free",
        started_at=date.today() - timedelta(days=60),
        ends_at=date.today() - timedelta(days=30),
        custom_limits={},
    )


# =============================================================================
# State Store Fixtures
# =============================================================================


@pytest.fixture
async def state_store() -> AsyncGenerator[InMemoryStateStore, None]:
    """Initialize and return state store."""
    store = InMemoryStateStore()
    await store.start()
    yield store
    await store.stop()


@pytest.fixture
async def state_store_manager() -> AsyncGenerator[StateStoreManager, None]:
    """Create and initialize a state store manager."""
    manager = StateStoreManager()
    await manager.init()
    yield manager
    await manager.close()


# =============================================================================
# Rate Limiter Fixtures
# =============================================================================


@pytest.fixture
async def rate_limiter():
    """Initialize and return rate limiter."""
    limiter = init_rate_limiter()
    yield limiter


# =============================================================================
# Mock Session & Repository Fixtures
# =============================================================================


@pytest.fixture
def mock_session() -> AsyncMock:
    """Create a mock SQLAlchemy async session."""
    session = AsyncMock(spec=AsyncSession)
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.flush = AsyncMock()
    session.close = AsyncMock()
    return session


@pytest.fixture
def mock_session_factory(mock_session: AsyncMock) -> MagicMock:
    """Create a mock session factory."""
    factory = MagicMock(spec=async_sessionmaker)

    # Make the factory return a context manager
    cm = AsyncMock()
    cm.__aenter__ = AsyncMock(return_value=mock_session)
    cm.__aexit__ = AsyncMock(return_value=None)
    factory.return_value = cm

    return factory


# =============================================================================
# Auth Service Fixtures
# =============================================================================


@pytest.fixture
def mock_auth_service(
    mock_config: IdentityPlanKitConfig,
    mock_session_factory: MagicMock,
) -> AuthService:
    """Create a mock auth service."""
    return AuthService(mock_config, mock_session_factory)


# =============================================================================
# Lockout Manager Fixtures
# =============================================================================


@pytest.fixture
def lockout_config() -> LockoutConfig:
    """Create lockout configuration for testing."""
    return LockoutConfig(
        max_attempts=5,
        lockout_duration_minutes=15,
        attempt_window_minutes=15,
        track_by_ip=True,
    )


@pytest.fixture
async def lockout_manager(
    state_store: InMemoryStateStore,
    lockout_config: LockoutConfig,
) -> LockoutManager:
    """Create a lockout manager with in-memory state store."""
    return LockoutManager(state_store, lockout_config)


# =============================================================================
# RBAC Service Fixtures
# =============================================================================


@pytest.fixture
def mock_rbac_service(
    mock_config: IdentityPlanKitConfig,
    mock_session_factory: MagicMock,
) -> RBACService:
    """Create a mock RBAC service."""
    return RBACService(mock_config, mock_session_factory)


# =============================================================================
# Plan Service Fixtures
# =============================================================================


@pytest.fixture
def mock_plan_service(
    mock_config: IdentityPlanKitConfig,
    mock_session_factory: MagicMock,
) -> PlanService:
    """Create a mock plan service."""
    return PlanService(mock_config, mock_session_factory)


# =============================================================================
# Token Generation Helpers
# =============================================================================


@pytest.fixture
def create_test_tokens(mock_config: IdentityPlanKitConfig, mock_user: User):
    """Factory to create test tokens for a user."""

    def _create(
        user: User | None = None,
        expired: bool = False,
    ) -> tuple[str, str, str]:
        """
        Create access and refresh tokens.

        Returns:
            Tuple of (access_token, refresh_token, token_hash)
        """
        target_user = user or mock_user
        secret = mock_config.secret_key.get_secret_value()

        if expired:
            expires_delta = timedelta(minutes=-5)
        else:
            expires_delta = timedelta(minutes=mock_config.access_token_expire_minutes)

        access_token = create_access_token(
            data={"sub": str(target_user.id)},
            secret_key=secret,
            algorithm=mock_config.algorithm,
            expires_delta=expires_delta,
        )

        refresh_expires = timedelta(days=-1) if expired else timedelta(days=30)
        refresh_token, token_hash = create_refresh_token(
            data={"sub": str(target_user.id)},
            secret_key=secret,
            algorithm=mock_config.algorithm,
            expires_delta=refresh_expires,
        )

        return access_token, refresh_token, token_hash

    return _create


# =============================================================================
# Mock UoW Helpers
# =============================================================================


class MockUnitOfWork:
    """Mock Unit of Work for testing."""

    def __init__(self) -> None:
        self.users = AsyncMock()
        self.tokens = AsyncMock()
        self.rbac = AsyncMock()
        self.plans = AsyncMock()
        self.usage = AsyncMock()
        self._committed = False
        self._rolled_back = False

    async def __aenter__(self) -> "MockUnitOfWork":
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,  # noqa: ARG002
        exc_tb: Any,  # noqa: ARG002
    ) -> None:
        if exc_type is None:
            self._committed = True
        else:
            self._rolled_back = True


@pytest.fixture
def mock_uow() -> MockUnitOfWork:
    """Create a mock Unit of Work."""
    return MockUnitOfWork()
