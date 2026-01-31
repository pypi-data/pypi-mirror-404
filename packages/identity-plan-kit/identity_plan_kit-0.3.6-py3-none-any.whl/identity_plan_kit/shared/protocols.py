"""
Protocol definitions for extensible models and entities.

Protocols define the minimum required interface that custom implementations
must satisfy to work with the library's repositories and services.

These are used for type checking and documentation purposes.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Protocol, runtime_checkable
from uuid import UUID


# =============================================================================
# Model Protocols (SQLAlchemy models)
# =============================================================================


@runtime_checkable
class UserModelProtocol(Protocol):
    """
    Protocol defining the minimum interface for a User model.

    Custom user models must have at least these attributes to work
    with the library's UserRepository.
    """

    id: UUID
    email: str
    role_id: UUID
    display_name: str
    picture_url: str | None
    is_active: bool
    is_verified: bool
    created_at: datetime
    updated_at: datetime

    # Optional: password_hash for password-based auth
    password_hash: str | None


@runtime_checkable
class UserProviderModelProtocol(Protocol):
    """Protocol for UserProvider model."""

    id: UUID
    user_id: UUID
    code: str
    external_user_id: str


@runtime_checkable
class RefreshTokenModelProtocol(Protocol):
    """Protocol for RefreshToken model."""

    id: UUID
    user_id: UUID
    token_hash: str
    expires_at: datetime
    created_at: datetime
    revoked_at: datetime | None
    user_agent: str | None
    ip_address: str | None


@runtime_checkable
class RoleModelProtocol(Protocol):
    """Protocol for Role model."""

    id: UUID
    code: str
    name: str


@runtime_checkable
class PermissionModelProtocol(Protocol):
    """Protocol for Permission model."""

    id: UUID
    code: str
    type: str


@runtime_checkable
class PlanModelProtocol(Protocol):
    """Protocol for Plan model."""

    id: UUID
    code: str
    name: str


@runtime_checkable
class FeatureModelProtocol(Protocol):
    """Protocol for Feature model."""

    id: UUID
    code: str
    name: str


@runtime_checkable
class PlanLimitModelProtocol(Protocol):
    """Protocol for PlanLimit model."""

    id: UUID
    plan_id: UUID
    feature_id: UUID
    feature_limit: int
    period: str | None


@runtime_checkable
class UserPlanModelProtocol(Protocol):
    """Protocol for UserPlan model."""

    id: UUID
    user_id: UUID
    plan_id: UUID
    started_at: date
    ends_at: date
    custom_limits: dict[str, Any]
    is_cancelled: bool
    cancelled_at: datetime | None


@runtime_checkable
class FeatureUsageModelProtocol(Protocol):
    """Protocol for FeatureUsage model."""

    id: UUID
    user_plan_id: UUID
    feature_id: UUID
    feature_usage: int
    start_period: date
    end_period: date


# =============================================================================
# Entity Protocols (Domain entities)
# =============================================================================


@runtime_checkable
class UserEntityProtocol(Protocol):
    """
    Protocol defining the minimum interface for a User entity.

    Custom user entities must have at least these attributes to work
    with the library's services.
    """

    id: UUID
    email: str
    role_id: UUID
    display_name: str
    picture_url: str | None
    is_active: bool
    is_verified: bool
    created_at: datetime
    updated_at: datetime
    role_code: str | None
    permissions: set[str]

    def deactivate(self) -> None:
        """Deactivate the user account."""
        ...

    def activate(self) -> None:
        """Activate the user account."""
        ...

    def verify(self) -> None:
        """Mark user as verified."""
        ...


@runtime_checkable
class UserProviderEntityProtocol(Protocol):
    """Protocol for UserProvider entity."""

    id: UUID
    user_id: UUID
    code: str
    external_user_id: str


@runtime_checkable
class RefreshTokenEntityProtocol(Protocol):
    """Protocol for RefreshToken entity."""

    id: UUID
    user_id: UUID
    token_hash: str
    expires_at: datetime
    created_at: datetime
    revoked_at: datetime | None
    user_agent: str | None
    ip_address: str | None

    @property
    def is_expired(self) -> bool:
        """Check if token has expired."""
        ...

    @property
    def is_revoked(self) -> bool:
        """Check if token has been revoked."""
        ...

    @property
    def is_valid(self) -> bool:
        """Check if token is valid."""
        ...


@runtime_checkable
class RoleEntityProtocol(Protocol):
    """Protocol for Role entity."""

    id: UUID
    code: str
    name: str
    permissions: set[str]

    def has_permission(self, permission_code: str) -> bool:
        """Check if role has a specific permission."""
        ...


@runtime_checkable
class PermissionEntityProtocol(Protocol):
    """Protocol for Permission entity."""

    id: UUID
    code: str
    type: Any  # PermissionType enum


@runtime_checkable
class PlanEntityProtocol(Protocol):
    """Protocol for Plan entity."""

    id: UUID
    code: str
    name: str
    permissions: set[str]
    limits: dict[str, Any]  # dict[str, PlanLimit]

    def has_permission(self, permission_code: str) -> bool:
        """Check if plan has a specific permission."""
        ...


@runtime_checkable
class FeatureEntityProtocol(Protocol):
    """Protocol for Feature entity."""

    id: UUID
    code: str
    name: str


@runtime_checkable
class PlanLimitEntityProtocol(Protocol):
    """Protocol for PlanLimit entity."""

    id: UUID
    plan_id: UUID
    feature_id: UUID
    feature_code: str
    limit: int
    period: Any  # PeriodType | None

    @property
    def is_unlimited(self) -> bool:
        """Check if feature is unlimited."""
        ...


@runtime_checkable
class UserPlanEntityProtocol(Protocol):
    """Protocol for UserPlan entity."""

    id: UUID
    user_id: UUID
    plan_id: UUID
    plan_code: str
    started_at: date
    ends_at: date
    custom_limits: dict[str, Any]

    @property
    def is_active(self) -> bool:
        """Check if plan is currently active."""
        ...

    @property
    def is_expired(self) -> bool:
        """Check if plan has expired."""
        ...

    def get_custom_limit(self, feature_code: str) -> int | None:
        """Get custom limit for a feature if defined."""
        ...


@runtime_checkable
class FeatureUsageEntityProtocol(Protocol):
    """Protocol for FeatureUsage entity."""

    id: UUID
    user_plan_id: UUID
    feature_id: UUID
    feature_code: str
    usage: int
    start_period: date
    end_period: date

    @property
    def is_current_period(self) -> bool:
        """Check if this is the current usage period."""
        ...


# =============================================================================
# DTO Protocols (API response schemas)
# =============================================================================


@runtime_checkable
class UserResponseProtocol(Protocol):
    """Protocol for UserResponse DTO."""

    id: UUID
    email: str
    display_name: str
    picture_url: str | None
    role_code: str | None
    is_active: bool
    is_verified: bool
    created_at: datetime


@runtime_checkable
class ProfileResponseProtocol(Protocol):
    """Protocol for ProfileResponse DTO."""

    id: UUID
    email: str
    display_name: str
    picture_url: str | None
    role_code: str | None
    is_active: bool
    is_verified: bool
    created_at: datetime
    user_permissions: list[str]
    plan: Any | None  # PlanInfoResponse | None


@runtime_checkable
class PlanResponseProtocol(Protocol):
    """Protocol for PlanResponse DTO."""

    id: UUID
    code: str
    name: str
    permissions: list[str]
    limits: list[Any]  # list[PlanLimitResponse]


@runtime_checkable
class FeatureResponseProtocol(Protocol):
    """Protocol for FeatureResponse DTO."""

    id: UUID
    code: str
    name: str
