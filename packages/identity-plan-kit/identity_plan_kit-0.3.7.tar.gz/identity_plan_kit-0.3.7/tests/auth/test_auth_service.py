"""Tests for AuthService - P0 priority (security-critical).

Tests cover:
- Token validation and user retrieval
- Token refresh with idempotency
- Token theft detection and account deactivation
- Logout functionality
"""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID

import pytest

from identity_plan_kit.auth.domain.entities import RefreshToken, User
from identity_plan_kit.auth.domain.exceptions import (
    TokenExpiredError,
    TokenInvalidError,
    UserInactiveError,
    UserNotFoundError,
)
from identity_plan_kit.auth.services.auth_service import AuthService
from identity_plan_kit.config import IdentityPlanKitConfig
from identity_plan_kit.shared.security import create_access_token, create_refresh_token, hash_token

pytestmark = pytest.mark.anyio


class TestGetUserFromToken:
    """Test suite for get_user_from_token method."""

    async def test_returns_user_for_valid_token(
        self,
        mock_config: IdentityPlanKitConfig,
        mock_user: User,
    ):
        """Valid access token returns user entity."""
        # Create a valid access token
        secret = mock_config.secret_key.get_secret_value()
        access_token = create_access_token(
            data={"sub": str(mock_user.id)},
            secret_key=secret,
            algorithm=mock_config.algorithm,
            expires_delta=timedelta(minutes=15),
        )

        # Mock the UoW and repository
        mock_uow = AsyncMock()
        mock_uow.__aenter__ = AsyncMock(return_value=mock_uow)
        mock_uow.__aexit__ = AsyncMock(return_value=None)
        mock_uow.users.get_by_id = AsyncMock(return_value=mock_user)

        # Create service with mocked dependencies
        mock_session_factory = MagicMock()
        service = AuthService(mock_config, mock_session_factory)

        with patch.object(service, "_create_uow", return_value=mock_uow):
            result = await service.get_user_from_token(access_token)

        assert result == mock_user
        assert result.id == mock_user.id
        assert result.email == mock_user.email

    async def test_raises_token_expired_for_expired_token(
        self,
        mock_config: IdentityPlanKitConfig,
        mock_user: User,
    ):
        """Expired access token raises TokenExpiredError."""
        secret = mock_config.secret_key.get_secret_value()
        expired_token = create_access_token(
            data={"sub": str(mock_user.id)},
            secret_key=secret,
            algorithm=mock_config.algorithm,
            expires_delta=timedelta(minutes=-5),  # Expired
        )

        mock_session_factory = MagicMock()
        service = AuthService(mock_config, mock_session_factory)

        with pytest.raises(TokenExpiredError):
            await service.get_user_from_token(expired_token)

    async def test_raises_token_invalid_for_malformed_token(
        self,
        mock_config: IdentityPlanKitConfig,
    ):
        """Malformed token raises TokenInvalidError."""
        mock_session_factory = MagicMock()
        service = AuthService(mock_config, mock_session_factory)

        with pytest.raises(TokenInvalidError):
            await service.get_user_from_token("invalid.token.here")

    async def test_raises_token_invalid_for_wrong_token_type(
        self,
        mock_config: IdentityPlanKitConfig,
        mock_user: User,
    ):
        """Refresh token used as access token raises TokenInvalidError."""
        secret = mock_config.secret_key.get_secret_value()
        refresh_token, _ = create_refresh_token(
            data={"sub": str(mock_user.id)},
            secret_key=secret,
            algorithm=mock_config.algorithm,
            expires_delta=timedelta(days=30),
        )

        mock_session_factory = MagicMock()
        service = AuthService(mock_config, mock_session_factory)

        with pytest.raises(TokenInvalidError, match="Invalid token type"):
            await service.get_user_from_token(refresh_token)

    async def test_raises_user_not_found_for_deleted_user(
        self,
        mock_config: IdentityPlanKitConfig,
        mock_user: User,
    ):
        """Token for deleted user raises UserNotFoundError."""
        secret = mock_config.secret_key.get_secret_value()
        access_token = create_access_token(
            data={"sub": str(mock_user.id)},
            secret_key=secret,
            algorithm=mock_config.algorithm,
            expires_delta=timedelta(minutes=15),
        )

        mock_uow = AsyncMock()
        mock_uow.__aenter__ = AsyncMock(return_value=mock_uow)
        mock_uow.__aexit__ = AsyncMock(return_value=None)
        mock_uow.users.get_by_id = AsyncMock(return_value=None)  # User not found

        mock_session_factory = MagicMock()
        service = AuthService(mock_config, mock_session_factory)

        with patch.object(service, "_create_uow", return_value=mock_uow):
            with pytest.raises(UserNotFoundError):
                await service.get_user_from_token(access_token)

    async def test_raises_user_inactive_for_deactivated_user(
        self,
        mock_config: IdentityPlanKitConfig,
        mock_inactive_user: User,
    ):
        """Token for inactive user raises UserInactiveError."""
        secret = mock_config.secret_key.get_secret_value()
        access_token = create_access_token(
            data={"sub": str(mock_inactive_user.id)},
            secret_key=secret,
            algorithm=mock_config.algorithm,
            expires_delta=timedelta(minutes=15),
        )

        mock_uow = AsyncMock()
        mock_uow.__aenter__ = AsyncMock(return_value=mock_uow)
        mock_uow.__aexit__ = AsyncMock(return_value=None)
        mock_uow.users.get_by_id = AsyncMock(return_value=mock_inactive_user)

        mock_session_factory = MagicMock()
        service = AuthService(mock_config, mock_session_factory)

        with patch.object(service, "_create_uow", return_value=mock_uow):
            with pytest.raises(UserInactiveError):
                await service.get_user_from_token(access_token)


class TestRefreshTokens:
    """Test suite for refresh_tokens method - includes idempotency and security tests."""

    async def test_successful_token_refresh(
        self,
        mock_config: IdentityPlanKitConfig,
        mock_user: User,
    ):
        """Successful refresh returns new tokens and revokes old one."""
        secret = mock_config.secret_key.get_secret_value()
        refresh_token, token_hash = create_refresh_token(
            data={"sub": str(mock_user.id)},
            secret_key=secret,
            algorithm=mock_config.algorithm,
            expires_delta=timedelta(days=30),
        )

        # Create a valid stored token
        stored_token = RefreshToken(
            id=UUID("87654321-4321-4321-4321-210987654321"),
            user_id=mock_user.id,
            token_hash=token_hash,
            expires_at=datetime.now(UTC) + timedelta(days=30),
            created_at=datetime.now(UTC),
        )

        mock_uow = AsyncMock()
        mock_uow.__aenter__ = AsyncMock(return_value=mock_uow)
        mock_uow.__aexit__ = AsyncMock(return_value=None)
        mock_uow.tokens.get_by_hash = AsyncMock(return_value=stored_token)
        mock_uow.tokens.revoke = AsyncMock()
        mock_uow.tokens.create = AsyncMock()
        mock_uow.users.get_by_id = AsyncMock(return_value=mock_user)

        # Mock state store for idempotency cache
        mock_state_store = AsyncMock()
        mock_state_store.get = AsyncMock(return_value=None)  # No cached result
        mock_state_store.set = AsyncMock()

        mock_session_factory = MagicMock()
        service = AuthService(mock_config, mock_session_factory)

        with (
            patch.object(service, "_create_uow", return_value=mock_uow),
            patch(
                "identity_plan_kit.auth.services.auth_service.get_state_store",
                return_value=mock_state_store,
            ),
        ):
            user, new_access, new_refresh = await service.refresh_tokens(refresh_token)

        assert user.id == mock_user.id
        assert new_access is not None
        assert new_refresh is not None
        assert new_refresh != refresh_token  # Token rotated

        # Verify old token was revoked
        mock_uow.tokens.revoke.assert_called_once_with(stored_token.id)

        # Verify idempotency cache was set
        mock_state_store.set.assert_called_once()

    async def test_refresh_is_idempotent_within_window(
        self,
        mock_config: IdentityPlanKitConfig,
        mock_user: User,
    ):
        """Same refresh token returns regenerated tokens when cache hit occurs."""
        secret = mock_config.secret_key.get_secret_value()
        refresh_token, token_hash = create_refresh_token(
            data={"sub": str(mock_user.id)},
            secret_key=secret,
            algorithm=mock_config.algorithm,
            expires_delta=timedelta(days=30),
        )

        # Create a mock stored token (the "new" token from previous refresh)
        new_token_hash = "mock_new_token_hash"
        stored_new_token = RefreshToken(
            id=UUID("87654321-4321-4321-4321-210987654321"),
            user_id=mock_user.id,
            token_hash=new_token_hash,
            expires_at=datetime.now(UTC) + timedelta(days=30),
            created_at=datetime.now(UTC),
        )

        # Simulate cached result from previous refresh (security fix: only stores reference)
        cached_result = {
            "user_id": str(mock_user.id),
            "new_token_hash": new_token_hash,
        }

        mock_uow = AsyncMock()
        mock_uow.__aenter__ = AsyncMock(return_value=mock_uow)
        mock_uow.__aexit__ = AsyncMock(return_value=None)
        mock_uow.users.get_by_id = AsyncMock(return_value=mock_user)
        mock_uow.tokens.get_by_hash = AsyncMock(return_value=stored_new_token)

        mock_state_store = AsyncMock()
        mock_state_store.get = AsyncMock(return_value=cached_result)  # Cache hit!

        mock_session_factory = MagicMock()
        service = AuthService(mock_config, mock_session_factory)

        with (
            patch.object(service, "_create_uow", return_value=mock_uow),
            patch(
                "identity_plan_kit.auth.services.auth_service.get_state_store",
                return_value=mock_state_store,
            ),
        ):
            user, access_token, new_refresh_token = await service.refresh_tokens(
                refresh_token
            )

        # Should return regenerated tokens (not original)
        assert user.id == mock_user.id
        assert access_token is not None
        assert new_refresh_token is not None
        # Tokens are regenerated (JWTs are stateless), so they won't equal the cache reference
        # The important thing is that the user gets valid tokens without triggering token reuse

    async def test_expired_token_raises_error(
        self,
        mock_config: IdentityPlanKitConfig,
        mock_user: User,
    ):
        """Expired refresh token raises TokenExpiredError."""
        secret = mock_config.secret_key.get_secret_value()
        refresh_token, token_hash = create_refresh_token(
            data={"sub": str(mock_user.id)},
            secret_key=secret,
            algorithm=mock_config.algorithm,
            expires_delta=timedelta(days=30),
        )

        # Create an expired stored token
        stored_token = RefreshToken(
            id=UUID("87654321-4321-4321-4321-210987654321"),
            user_id=mock_user.id,
            token_hash=token_hash,
            expires_at=datetime.now(UTC) - timedelta(days=1),  # Expired
            created_at=datetime.now(UTC) - timedelta(days=31),
        )

        mock_uow = AsyncMock()
        mock_uow.__aenter__ = AsyncMock(return_value=mock_uow)
        mock_uow.__aexit__ = AsyncMock(return_value=None)
        mock_uow.tokens.get_by_hash = AsyncMock(return_value=stored_token)

        mock_state_store = AsyncMock()
        mock_state_store.get = AsyncMock(return_value=None)

        mock_session_factory = MagicMock()
        service = AuthService(mock_config, mock_session_factory)

        with (
            patch.object(service, "_create_uow", return_value=mock_uow),
            patch(
                "identity_plan_kit.auth.services.auth_service.get_state_store",
                return_value=mock_state_store,
            ),
        ):
            with pytest.raises(TokenExpiredError):
                await service.refresh_tokens(refresh_token)

    async def test_revoked_token_triggers_security_response(
        self,
        mock_config: IdentityPlanKitConfig,
        mock_user: User,
    ):
        """Revoked token reuse triggers account deactivation (token theft detection)."""
        secret = mock_config.secret_key.get_secret_value()
        refresh_token, token_hash = create_refresh_token(
            data={"sub": str(mock_user.id)},
            secret_key=secret,
            algorithm=mock_config.algorithm,
            expires_delta=timedelta(days=30),
        )

        # Create a revoked token (potential theft scenario)
        revoked_token = RefreshToken(
            id=UUID("87654321-4321-4321-4321-210987654321"),
            user_id=mock_user.id,
            token_hash=token_hash,
            expires_at=datetime.now(UTC) + timedelta(days=30),
            created_at=datetime.now(UTC) - timedelta(hours=1),
            revoked_at=datetime.now(UTC) - timedelta(minutes=30),  # Already revoked!
        )

        # Active user that should be deactivated
        active_user = User(
            id=mock_user.id,
            email=mock_user.email,
            role_id=mock_user.role_id,
            display_name="Test User",
            is_active=True,
            is_verified=True,
        )

        mock_uow = AsyncMock()
        mock_uow.__aenter__ = AsyncMock(return_value=mock_uow)
        mock_uow.__aexit__ = AsyncMock(return_value=None)
        mock_uow.tokens.get_by_hash = AsyncMock(return_value=revoked_token)
        mock_uow.tokens.revoke_all_for_user = AsyncMock()
        mock_uow.users.get_by_id = AsyncMock(return_value=active_user)
        mock_uow.users.deactivate = AsyncMock()

        mock_state_store = AsyncMock()
        mock_state_store.get = AsyncMock(return_value=None)

        mock_session_factory = MagicMock()
        service = AuthService(mock_config, mock_session_factory)

        with (
            patch.object(service, "_create_uow", return_value=mock_uow),
            patch(
                "identity_plan_kit.auth.services.auth_service.get_state_store",
                return_value=mock_state_store,
            ),
        ):
            with pytest.raises(TokenInvalidError, match="revoked"):
                await service.refresh_tokens(refresh_token)

        # Verify all tokens were revoked
        mock_uow.tokens.revoke_all_for_user.assert_called_once_with(mock_user.id)

        # Verify user was deactivated (P1 security fix)
        mock_uow.users.deactivate.assert_called_once_with(
            mock_user.id, reason="token_theft_suspected"
        )

    async def test_token_not_found_raises_error(
        self,
        mock_config: IdentityPlanKitConfig,
        mock_user: User,
    ):
        """Unknown refresh token raises TokenInvalidError."""
        secret = mock_config.secret_key.get_secret_value()
        refresh_token, _ = create_refresh_token(
            data={"sub": str(mock_user.id)},
            secret_key=secret,
            algorithm=mock_config.algorithm,
            expires_delta=timedelta(days=30),
        )

        mock_uow = AsyncMock()
        mock_uow.__aenter__ = AsyncMock(return_value=mock_uow)
        mock_uow.__aexit__ = AsyncMock(return_value=None)
        mock_uow.tokens.get_by_hash = AsyncMock(return_value=None)  # Not found

        mock_state_store = AsyncMock()
        mock_state_store.get = AsyncMock(return_value=None)

        mock_session_factory = MagicMock()
        service = AuthService(mock_config, mock_session_factory)

        with (
            patch.object(service, "_create_uow", return_value=mock_uow),
            patch(
                "identity_plan_kit.auth.services.auth_service.get_state_store",
                return_value=mock_state_store,
            ),
        ):
            with pytest.raises(TokenInvalidError, match="Token not found"):
                await service.refresh_tokens(refresh_token)


class TestLogout:
    """Test suite for logout method."""

    async def test_logout_single_session(
        self,
        mock_config: IdentityPlanKitConfig,
        mock_user: User,
    ):
        """Logout revokes single token when refresh_token provided."""
        secret = mock_config.secret_key.get_secret_value()
        refresh_token, token_hash = create_refresh_token(
            data={"sub": str(mock_user.id)},
            secret_key=secret,
            algorithm=mock_config.algorithm,
            expires_delta=timedelta(days=30),
        )

        stored_token = RefreshToken(
            id=UUID("87654321-4321-4321-4321-210987654321"),
            user_id=mock_user.id,
            token_hash=token_hash,
            expires_at=datetime.now(UTC) + timedelta(days=30),
            created_at=datetime.now(UTC),
        )

        mock_uow = AsyncMock()
        mock_uow.__aenter__ = AsyncMock(return_value=mock_uow)
        mock_uow.__aexit__ = AsyncMock(return_value=None)
        mock_uow.tokens.get_by_hash = AsyncMock(return_value=stored_token)
        mock_uow.tokens.revoke = AsyncMock()

        mock_session_factory = MagicMock()
        service = AuthService(mock_config, mock_session_factory)

        with patch.object(service, "_create_uow", return_value=mock_uow):
            await service.logout(mock_user.id, refresh_token=refresh_token)

        mock_uow.tokens.revoke.assert_called_once_with(stored_token.id)

    async def test_logout_all_sessions(
        self,
        mock_config: IdentityPlanKitConfig,
        mock_user: User,
    ):
        """Logout everywhere revokes all user tokens."""
        mock_uow = AsyncMock()
        mock_uow.__aenter__ = AsyncMock(return_value=mock_uow)
        mock_uow.__aexit__ = AsyncMock(return_value=None)
        mock_uow.tokens.revoke_all_for_user = AsyncMock(return_value=5)

        mock_session_factory = MagicMock()
        service = AuthService(mock_config, mock_session_factory)

        with patch.object(service, "_create_uow", return_value=mock_uow):
            await service.logout(mock_user.id, everywhere=True)

        mock_uow.tokens.revoke_all_for_user.assert_called_once_with(mock_user.id)

    async def test_logout_with_nonexistent_token(
        self,
        mock_config: IdentityPlanKitConfig,
        mock_user: User,
    ):
        """Logout with unknown token completes without error."""
        secret = mock_config.secret_key.get_secret_value()
        refresh_token, _ = create_refresh_token(
            data={"sub": str(mock_user.id)},
            secret_key=secret,
            algorithm=mock_config.algorithm,
            expires_delta=timedelta(days=30),
        )

        mock_uow = AsyncMock()
        mock_uow.__aenter__ = AsyncMock(return_value=mock_uow)
        mock_uow.__aexit__ = AsyncMock(return_value=None)
        mock_uow.tokens.get_by_hash = AsyncMock(return_value=None)

        mock_session_factory = MagicMock()
        service = AuthService(mock_config, mock_session_factory)

        with patch.object(service, "_create_uow", return_value=mock_uow):
            # Should not raise
            await service.logout(mock_user.id, refresh_token=refresh_token)


class TestAuthenticateGoogle:
    """Test suite for Google OAuth authentication."""

    async def test_creates_new_user_on_first_login(
        self,
        mock_config: IdentityPlanKitConfig,
    ):
        """New Google user creates account and default plan on first login."""
        mock_google_user = MagicMock()
        mock_google_user.id = "google_123"
        mock_google_user.email = "newuser@gmail.com"
        mock_google_user.name = "New User"
        mock_google_user.picture = "https://lh3.googleusercontent.com/a-/test"
        mock_google_user.email_verified = True

        new_user = User(
            id=UUID("12345678-1234-1234-1234-123456789099"),
            email="newuser@gmail.com",
            role_id=2,
            display_name="New User",
            picture_url="https://lh3.googleusercontent.com/a-/test",
            is_active=True,
            is_verified=True,
        )

        # Mock role and plan objects
        mock_role = MagicMock()
        mock_role.id = UUID("00000000-0000-0000-0000-000000000002")

        mock_plan = MagicMock()
        mock_plan.id = UUID("00000000-0000-0000-0000-000000000001")

        mock_uow = AsyncMock()
        mock_uow.__aenter__ = AsyncMock(return_value=mock_uow)
        mock_uow.__aexit__ = AsyncMock(return_value=None)
        mock_uow.users.get_or_create_with_provider = AsyncMock(
            return_value=(new_user, True)  # created=True
        )
        mock_uow.tokens.create = AsyncMock()
        mock_uow.plans.create_user_plan = AsyncMock()  # Mock for default plan creation
        mock_uow.rbac.get_role_by_code = AsyncMock(return_value=mock_role)
        mock_uow.plans.get_plan_by_code = AsyncMock(return_value=mock_plan)

        mock_lockout = AsyncMock()
        mock_lockout.check_lockout = AsyncMock()
        mock_lockout.clear_failures = AsyncMock()

        mock_state_store = AsyncMock()

        mock_session_factory = MagicMock()
        service = AuthService(mock_config, mock_session_factory)

        with (
            patch.object(service, "_create_uow", return_value=mock_uow),
            patch.object(service, "_get_lockout_manager", return_value=mock_lockout),
            patch.object(
                service._google_oauth, "authenticate", return_value=mock_google_user
            ),
            patch(
                "identity_plan_kit.auth.services.auth_service.get_state_store",
                return_value=mock_state_store,
            ),
        ):
            user, access_token, refresh_token = await service.authenticate_google(
                code="auth_code_123",
                user_agent="Test Browser",
                ip_address="1.2.3.4",
            )

        assert user.email == "newuser@gmail.com"
        assert access_token is not None
        assert refresh_token is not None

        # Verify lockout was cleared on success
        mock_lockout.clear_failures.assert_called()

        # Verify default plan was created atomically with user
        mock_uow.plans.create_user_plan.assert_called_once_with(
            user_id=new_user.id,
            plan_id=mock_plan.id,
        )

    async def test_rejects_inactive_user(
        self,
        mock_config: IdentityPlanKitConfig,
    ):
        """Inactive user cannot authenticate."""
        mock_google_user = MagicMock()
        mock_google_user.id = "google_123"
        mock_google_user.email = "inactive@gmail.com"
        mock_google_user.name = "Inactive User"
        mock_google_user.picture = None
        mock_google_user.email_verified = True

        inactive_user = User(
            id=UUID("12345678-1234-1234-1234-123456789099"),
            email="inactive@gmail.com",
            role_id=2,
            display_name="Inactive User",
            is_active=False,
            is_verified=True,
        )

        mock_uow = AsyncMock()
        mock_uow.__aenter__ = AsyncMock(return_value=mock_uow)
        mock_uow.__aexit__ = AsyncMock(return_value=None)
        mock_uow.users.get_or_create_with_provider = AsyncMock(
            return_value=(inactive_user, False)
        )

        mock_lockout = AsyncMock()
        mock_lockout.check_lockout = AsyncMock()

        mock_session_factory = MagicMock()
        service = AuthService(mock_config, mock_session_factory)

        with (
            patch.object(service, "_create_uow", return_value=mock_uow),
            patch.object(service, "_get_lockout_manager", return_value=mock_lockout),
            patch.object(
                service._google_oauth, "authenticate", return_value=mock_google_user
            ),
        ):
            with pytest.raises(UserInactiveError):
                await service.authenticate_google(code="auth_code_123")
