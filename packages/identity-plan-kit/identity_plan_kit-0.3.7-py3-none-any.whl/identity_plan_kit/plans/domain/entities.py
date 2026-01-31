"""Plans domain entities."""

from dataclasses import dataclass, field
from datetime import date
from enum import Enum
from typing import Any
from uuid import UUID


class PeriodType(str, Enum):
    """Usage period type."""

    DAILY = "daily"
    MONTHLY = "monthly"


@dataclass
class Feature:
    """
    Feature domain entity.

    Represents a trackable/limitable feature in the system.
    """

    id: UUID
    code: str
    name: str

    def __post_init__(self) -> None:
        """Validate entity after initialization."""
        if not self.code:
            raise ValueError("Feature code cannot be empty")


@dataclass
class Plan:
    """
    Subscription plan domain entity.

    Represents a subscription tier with associated permissions and limits.
    """

    id: UUID
    code: str
    name: str
    permissions: set[str] = field(default_factory=set)
    limits: dict[str, "PlanLimit"] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate entity after initialization."""
        if not self.code:
            raise ValueError("Plan code cannot be empty")

    def has_permission(self, permission_code: str) -> bool:
        """Check if plan has a specific permission."""
        return permission_code in self.permissions

    def get_feature_limit(self, feature_code: str) -> "PlanLimit | None":
        """Get limit for a feature."""
        return self.limits.get(feature_code)


@dataclass
class PlanLimit:
    """
    Plan limit for a feature.

    Defines usage limits per feature per plan.
    """

    id: UUID
    plan_id: UUID
    feature_id: UUID
    feature_code: str
    limit: int  # -1 means unlimited
    period: PeriodType | None  # None means lifetime/no reset

    @property
    def is_unlimited(self) -> bool:
        """Check if feature is unlimited."""
        return self.limit == -1


@dataclass
class UserPlan:
    """
    User's active subscription plan.

    Links a user to a plan with optional custom limits.
    """

    id: UUID
    user_id: UUID
    plan_id: UUID
    plan_code: str
    started_at: date
    ends_at: date
    custom_limits: dict[str, Any] = field(default_factory=dict)

    @property
    def is_active(self) -> bool:
        """Check if plan is currently active."""
        today = date.today()
        return self.started_at <= today <= self.ends_at

    @property
    def is_expired(self) -> bool:
        """Check if plan has expired."""
        return date.today() > self.ends_at

    def get_custom_limit(self, feature_code: str) -> int | None:
        """Get custom limit for a feature if defined."""
        return self.custom_limits.get(feature_code)


@dataclass
class FeatureUsage:
    """
    Feature usage tracking.

    Tracks how much of a feature a user has consumed in a period.
    """

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
        today = date.today()
        return self.start_period <= today <= self.end_period
