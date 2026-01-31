"""Tests for auth domain entities - Unit test layer.

Tests cover:
- User entity state transitions
- RefreshToken entity properties
- UserProvider validation
"""

from datetime import UTC, datetime, timedelta
from uuid import UUID

import pytest

from identity_plan_kit.auth.domain.entities import RefreshToken, User, UserProvider


class TestUserEntity:
    """Test suite for User domain entity."""

    def test_user_creation(self):
        """User can be created with required fields."""
        user = User(
            id=UUID("12345678-1234-1234-1234-123456789012"),
            email="test@example.com",
            role_id=1,
            display_name="Test User",
        )

        assert user.email == "test@example.com"
        assert user.role_id == 1
        assert user.is_active is True  # Default
        assert user.is_verified is False  # Default

    def test_deactivate_active_user(self):
        """Active user can be deactivated."""
        user = User(
            id=UUID("12345678-1234-1234-1234-123456789012"),
            email="test@example.com",
            role_id=1,
            display_name="Test User",
            is_active=True,
        )

        user.deactivate()

        assert user.is_active is False

    def test_deactivate_already_inactive_raises(self):
        """Cannot deactivate already inactive user."""
        user = User(
            id=UUID("12345678-1234-1234-1234-123456789012"),
            email="test@example.com",
            role_id=1,
            display_name="Test User",
            is_active=False,
        )

        with pytest.raises(ValueError, match="already inactive"):
            user.deactivate()

    def test_activate_inactive_user(self):
        """Inactive user can be activated."""
        user = User(
            id=UUID("12345678-1234-1234-1234-123456789012"),
            email="test@example.com",
            role_id=1,
            display_name="Test User",
            is_active=False,
        )

        user.activate()

        assert user.is_active is True

    def test_activate_already_active_raises(self):
        """Cannot activate already active user."""
        user = User(
            id=UUID("12345678-1234-1234-1234-123456789012"),
            email="test@example.com",
            role_id=1,
            display_name="Test User",
            is_active=True,
        )

        with pytest.raises(ValueError, match="already active"):
            user.activate()

    def test_verify_unverified_user(self):
        """Unverified user can be verified."""
        user = User(
            id=UUID("12345678-1234-1234-1234-123456789012"),
            email="test@example.com",
            role_id=1,
            display_name="Test User",
            is_verified=False,
        )

        user.verify()

        assert user.is_verified is True

    def test_verify_already_verified_raises(self):
        """Cannot verify already verified user."""
        user = User(
            id=UUID("12345678-1234-1234-1234-123456789012"),
            email="test@example.com",
            role_id=1,
            display_name="Test User",
            is_verified=True,
        )

        with pytest.raises(ValueError, match="already verified"):
            user.verify()


class TestRefreshTokenEntity:
    """Test suite for RefreshToken domain entity."""

    def test_token_creation(self):
        """RefreshToken can be created with required fields."""
        expires_at = datetime.now(UTC) + timedelta(days=30)
        token = RefreshToken(
            id=UUID("12345678-1234-1234-1234-123456789012"),
            user_id=UUID("87654321-4321-4321-4321-210987654321"),
            token_hash="abc123hash",
            expires_at=expires_at,
        )

        assert token.token_hash == "abc123hash"
        assert token.revoked_at is None

    def test_is_expired_false_for_valid_token(self):
        """is_expired is False for non-expired token."""
        token = RefreshToken(
            id=UUID("12345678-1234-1234-1234-123456789012"),
            user_id=UUID("87654321-4321-4321-4321-210987654321"),
            token_hash="abc123hash",
            expires_at=datetime.now(UTC) + timedelta(days=30),
        )

        assert token.is_expired is False

    def test_is_expired_true_for_expired_token(self):
        """is_expired is True for expired token."""
        token = RefreshToken(
            id=UUID("12345678-1234-1234-1234-123456789012"),
            user_id=UUID("87654321-4321-4321-4321-210987654321"),
            token_hash="abc123hash",
            expires_at=datetime.now(UTC) - timedelta(days=1),
        )

        assert token.is_expired is True

    def test_is_revoked_false_for_active_token(self):
        """is_revoked is False for non-revoked token."""
        token = RefreshToken(
            id=UUID("12345678-1234-1234-1234-123456789012"),
            user_id=UUID("87654321-4321-4321-4321-210987654321"),
            token_hash="abc123hash",
            expires_at=datetime.now(UTC) + timedelta(days=30),
        )

        assert token.is_revoked is False

    def test_is_revoked_true_for_revoked_token(self):
        """is_revoked is True for revoked token."""
        token = RefreshToken(
            id=UUID("12345678-1234-1234-1234-123456789012"),
            user_id=UUID("87654321-4321-4321-4321-210987654321"),
            token_hash="abc123hash",
            expires_at=datetime.now(UTC) + timedelta(days=30),
            revoked_at=datetime.now(UTC),
        )

        assert token.is_revoked is True

    def test_is_valid_true_for_active_non_expired(self):
        """is_valid is True for active, non-expired token."""
        token = RefreshToken(
            id=UUID("12345678-1234-1234-1234-123456789012"),
            user_id=UUID("87654321-4321-4321-4321-210987654321"),
            token_hash="abc123hash",
            expires_at=datetime.now(UTC) + timedelta(days=30),
        )

        assert token.is_valid is True

    def test_is_valid_false_for_expired(self):
        """is_valid is False for expired token."""
        token = RefreshToken(
            id=UUID("12345678-1234-1234-1234-123456789012"),
            user_id=UUID("87654321-4321-4321-4321-210987654321"),
            token_hash="abc123hash",
            expires_at=datetime.now(UTC) - timedelta(days=1),
        )

        assert token.is_valid is False

    def test_is_valid_false_for_revoked(self):
        """is_valid is False for revoked token."""
        token = RefreshToken(
            id=UUID("12345678-1234-1234-1234-123456789012"),
            user_id=UUID("87654321-4321-4321-4321-210987654321"),
            token_hash="abc123hash",
            expires_at=datetime.now(UTC) + timedelta(days=30),
            revoked_at=datetime.now(UTC),
        )

        assert token.is_valid is False

    def test_revoke_active_token(self):
        """Active token can be revoked."""
        token = RefreshToken(
            id=UUID("12345678-1234-1234-1234-123456789012"),
            user_id=UUID("87654321-4321-4321-4321-210987654321"),
            token_hash="abc123hash",
            expires_at=datetime.now(UTC) + timedelta(days=30),
        )

        token.revoke()

        assert token.is_revoked is True
        assert token.revoked_at is not None

    def test_revoke_already_revoked_raises(self):
        """Cannot revoke already revoked token."""
        token = RefreshToken(
            id=UUID("12345678-1234-1234-1234-123456789012"),
            user_id=UUID("87654321-4321-4321-4321-210987654321"),
            token_hash="abc123hash",
            expires_at=datetime.now(UTC) + timedelta(days=30),
            revoked_at=datetime.now(UTC),
        )

        with pytest.raises(ValueError, match="already revoked"):
            token.revoke()


class TestUserProviderEntity:
    """Test suite for UserProvider domain entity."""

    def test_valid_google_provider(self):
        """Google provider is valid."""
        provider = UserProvider(
            id=1,
            user_id=UUID("12345678-1234-1234-1234-123456789012"),
            code="google",
            external_user_id="google_12345",
        )

        assert provider.code == "google"
        assert provider.external_user_id == "google_12345"

    def test_invalid_provider_code_raises(self):
        """Invalid provider code raises ValueError."""
        with pytest.raises(ValueError, match="Invalid provider code"):
            UserProvider(
                id=1,
                user_id=UUID("12345678-1234-1234-1234-123456789012"),
                code="invalid_provider",
                external_user_id="user_123",
            )
