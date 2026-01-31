"""Auth request DTOs."""

from pydantic import Field

from identity_plan_kit.shared.schemas import BaseRequest


class OAuthCallbackRequest(BaseRequest):
    """OAuth callback request data."""

    code: str = Field(
        ...,
        description="Authorization code from OAuth provider",
    )
    state: str | None = Field(
        default=None,
        description="State parameter for CSRF protection",
    )
    error: str | None = Field(
        default=None,
        description="Error code if authentication failed",
    )
    error_description: str | None = Field(
        default=None,
        description="Human-readable error description",
    )


class RefreshTokenRequest(BaseRequest):
    """Refresh token request."""

    refresh_token: str | None = Field(
        default=None,
        description="Refresh token (if not in cookie)",
    )


class LogoutRequest(BaseRequest):
    """Logout request."""

    everywhere: bool = Field(
        default=False,
        description="Revoke all sessions (logout everywhere)",
    )


class UpdateProfileRequest(BaseRequest):
    """Profile update request."""

    display_name: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
        description="User display name (1-100 characters)",
    )
    picture_url: str | None = Field(
        default=None,
        max_length=500,
        description="Profile picture URL (max 500 characters, or empty string to clear)",
    )
