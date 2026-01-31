"""Tests for auth dependencies (P1 exception handling fix)."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from identity_plan_kit.auth.dependencies import get_current_user, get_optional_user
from identity_plan_kit.auth.domain.entities import User
from identity_plan_kit.auth.domain.exceptions import (
    AuthError,
    TokenExpiredError,
    TokenInvalidError,
    UserInactiveError,
    UserNotFoundError,
)

pytestmark = pytest.mark.anyio


class TestGetCurrentUser:
    """Test suite for get_current_user dependency."""

    @pytest.fixture
    def mock_request(self):
        """Create a mock request with kit in app state."""
        request = MagicMock()
        request.app.state.identity_plan_kit = MagicMock()
        request.app.state.identity_plan_kit.auth_service = AsyncMock()
        return request

    async def test_returns_user_on_valid_token(self, mock_request, mock_user):
        """Test that valid token returns user."""
        mock_request.app.state.identity_plan_kit.auth_service.get_user_from_token = AsyncMock(
            return_value=mock_user
        )
        credentials = MagicMock()
        credentials.credentials = "valid_token"

        user = await get_current_user(
            request=mock_request,
            credentials=credentials,
            access_token=None,
        )

        assert user == mock_user

    async def test_uses_cookie_when_no_bearer(self, mock_request, mock_user):
        """Test that cookie token is used when no bearer token."""
        mock_request.app.state.identity_plan_kit.auth_service.get_user_from_token = AsyncMock(
            return_value=mock_user
        )

        user = await get_current_user(
            request=mock_request,
            credentials=None,
            access_token="cookie_token",
        )

        assert user == mock_user

    async def test_raises_401_when_no_token(self, mock_request):
        """Test that 401 is raised when no token provided."""
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(
                request=mock_request,
                credentials=None,
                access_token=None,
            )

        assert exc_info.value.status_code == 401
        assert "Not authenticated" in exc_info.value.detail

    async def test_raises_401_on_expired_token(self, mock_request):
        """Test that 401 is raised on expired token."""
        mock_request.app.state.identity_plan_kit.auth_service.get_user_from_token = AsyncMock(
            side_effect=TokenExpiredError()
        )
        credentials = MagicMock()
        credentials.credentials = "expired_token"

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(
                request=mock_request,
                credentials=credentials,
                access_token=None,
            )

        assert exc_info.value.status_code == 401
        assert "expired" in exc_info.value.detail.lower()

    async def test_raises_401_on_invalid_token(self, mock_request):
        """Test that 401 is raised on invalid token."""
        mock_request.app.state.identity_plan_kit.auth_service.get_user_from_token = AsyncMock(
            side_effect=TokenInvalidError()
        )
        credentials = MagicMock()
        credentials.credentials = "invalid_token"

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(
                request=mock_request,
                credentials=credentials,
                access_token=None,
            )

        assert exc_info.value.status_code == 401

    async def test_raises_403_on_inactive_user(self, mock_request):
        """Test that 403 is raised for inactive user."""
        mock_request.app.state.identity_plan_kit.auth_service.get_user_from_token = AsyncMock(
            side_effect=UserInactiveError()
        )
        credentials = MagicMock()
        credentials.credentials = "valid_token"

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(
                request=mock_request,
                credentials=credentials,
                access_token=None,
            )

        assert exc_info.value.status_code == 403
        assert "inactive" in exc_info.value.detail.lower()


class TestGetOptionalUser:
    """Test suite for get_optional_user dependency (P1 fix validation)."""

    @pytest.fixture
    def mock_request(self):
        """Create a mock request with kit in app state."""
        request = MagicMock()
        request.app.state.identity_plan_kit = MagicMock()
        request.app.state.identity_plan_kit.auth_service = AsyncMock()
        return request

    async def test_returns_user_on_valid_token(self, mock_request, mock_user):
        """Test that valid token returns user."""
        mock_request.app.state.identity_plan_kit.auth_service.get_user_from_token = AsyncMock(
            return_value=mock_user
        )
        credentials = MagicMock()
        credentials.credentials = "valid_token"

        user = await get_optional_user(
            request=mock_request,
            credentials=credentials,
            access_token=None,
        )

        assert user == mock_user

    async def test_returns_none_when_no_token(self, mock_request):
        """Test that None is returned when no token provided."""
        user = await get_optional_user(
            request=mock_request,
            credentials=None,
            access_token=None,
        )

        assert user is None

    async def test_returns_none_on_auth_error(self, mock_request):
        """Test that None is returned on AuthError (expected)."""
        mock_request.app.state.identity_plan_kit.auth_service.get_user_from_token = AsyncMock(
            side_effect=TokenExpiredError()
        )
        credentials = MagicMock()
        credentials.credentials = "expired_token"

        user = await get_optional_user(
            request=mock_request,
            credentials=credentials,
            access_token=None,
        )

        assert user is None

    async def test_reraises_unexpected_exception(self, mock_request):
        """Test that unexpected exceptions are re-raised (P1 fix)."""
        mock_request.app.state.identity_plan_kit.auth_service.get_user_from_token = AsyncMock(
            side_effect=RuntimeError("Database connection failed")
        )
        credentials = MagicMock()
        credentials.credentials = "valid_token"

        # P1 fix: Should re-raise unexpected exceptions, not swallow them
        with pytest.raises(RuntimeError, match="Database connection failed"):
            await get_optional_user(
                request=mock_request,
                credentials=credentials,
                access_token=None,
            )

    async def test_returns_none_on_token_invalid(self, mock_request):
        """Test that TokenInvalidError returns None."""
        mock_request.app.state.identity_plan_kit.auth_service.get_user_from_token = AsyncMock(
            side_effect=TokenInvalidError()
        )
        credentials = MagicMock()
        credentials.credentials = "invalid_token"

        user = await get_optional_user(
            request=mock_request,
            credentials=credentials,
            access_token=None,
        )

        assert user is None
