"""Plans module - Subscription plans and usage tracking."""

from identity_plan_kit.plans.dependencies import (
    FeatureUsage,
    requires_feature,
    requires_plan,
)
from identity_plan_kit.plans.domain.entities import Feature, Plan, PlanLimit, UserPlan
from identity_plan_kit.plans.domain.exceptions import (
    FeatureNotAvailableError,
    FeatureNotFoundError,
    InvalidCustomLimitsError,
    InvalidPlanDatesError,
    PlanAssignmentError,
    PlanAuthorizationError,
    PlanExpiredError,
    PlanNotFoundError,
    QuotaExceededError,
    UserPlanNotFoundError,
)
from identity_plan_kit.plans.dto.responses import QuotaResponse
from identity_plan_kit.plans.dto.usage import UsageInfo
from identity_plan_kit.plans.repositories.plan_repo import PlanRepository
from identity_plan_kit.plans.repositories.usage_repo import UsageRepository
from identity_plan_kit.plans.uow import PlansUnitOfWork

__all__ = [
    # Entities
    "Feature",
    # Exceptions
    "FeatureNotAvailableError",
    "FeatureNotFoundError",
    "InvalidCustomLimitsError",
    "InvalidPlanDatesError",
    "Plan",
    "PlanAssignmentError",
    "PlanAuthorizationError",
    "PlanExpiredError",
    "PlanLimit",
    "PlanNotFoundError",
    # Repositories (for direct use with external sessions)
    "PlanRepository",
    # Unit of Work
    "PlansUnitOfWork",
    "QuotaExceededError",
    # DTOs
    "QuotaResponse",
    "UsageInfo",
    "UsageRepository",
    "UserPlan",
    "UserPlanNotFoundError",
    # Dependencies
    "FeatureUsage",
    "requires_feature",
    "requires_plan",
]
