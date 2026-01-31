"""Auth response DTOs."""

from datetime import date, datetime
from uuid import UUID

from pydantic import EmailStr, Field

from identity_plan_kit.shared.schemas import BaseResponse


class AuthURLResponse(BaseResponse):
    """OAuth authorization URL response."""

    url: str = Field(
        ...,
        description="URL to redirect user for OAuth authentication",
    )
    state: str = Field(
        ...,
        description="State parameter for CSRF protection",
    )


class TokenResponse(BaseResponse):
    """Token response after successful authentication."""

    access_token: str = Field(
        ...,
        description="JWT access token",
    )
    token_type: str = Field(
        default="bearer",
        description="Token type (always 'bearer')",
    )
    expires_in: int = Field(
        ...,
        description="Token expiration time in seconds",
    )
    # Note: refresh_token is set in HttpOnly cookie, not returned in body


class UserResponse(BaseResponse):
    """User information response."""

    id: UUID = Field(
        ...,
        description="User ID",
    )
    email: EmailStr = Field(
        ...,
        description="User email address",
    )
    display_name: str = Field(
        ...,
        description="User display name",
    )
    picture_url: str | None = Field(
        default=None,
        description="Profile picture URL",
    )
    role_code: str | None = Field(
        default=None,
        description="User role code",
    )
    is_active: bool = Field(
        ...,
        description="Whether user account is active",
    )
    is_verified: bool = Field(
        ...,
        description="Whether user email is verified",
    )
    created_at: datetime = Field(
        ...,
        description="Account creation timestamp",
    )


class AuthenticatedUserResponse(BaseResponse):
    """Full authenticated user response with tokens."""

    user: UserResponse = Field(
        ...,
        description="User information",
    )
    tokens: TokenResponse = Field(
        ...,
        description="Authentication tokens",
    )


class PlanInfoResponse(BaseResponse):
    """User's current plan information."""

    code: str = Field(
        ...,
        description="Plan code",
    )
    name: str = Field(
        ...,
        description="Plan name",
    )
    started_at: date = Field(
        ...,
        description="Plan start date",
    )
    ends_at: date = Field(
        ...,
        description="Plan end date",
    )
    is_active: bool = Field(
        ...,
        description="Whether plan is currently active",
    )
    permissions: list[str] = Field(
        default_factory=list,
        description="List of plan-based permissions",
    )


class ProfileResponse(BaseResponse):
    """Complete user profile with plan and permissions."""

    id: UUID = Field(
        ...,
        description="User ID",
    )
    email: EmailStr = Field(
        ...,
        description="User email address",
    )
    display_name: str = Field(
        ...,
        description="User display name",
    )
    picture_url: str | None = Field(
        default=None,
        description="Profile picture URL",
    )
    role_code: str | None = Field(
        default=None,
        description="User role code",
    )
    is_active: bool = Field(
        ...,
        description="Whether user account is active",
    )
    is_verified: bool = Field(
        ...,
        description="Whether user email is verified",
    )
    created_at: datetime = Field(
        ...,
        description="Account creation timestamp",
    )
    user_permissions: list[str] = Field(
        default_factory=list,
        description="List of user's role-based permissions",
    )
    plan: PlanInfoResponse | None = Field(
        default=None,
        description="User's current plan with plan-based permissions",
    )
