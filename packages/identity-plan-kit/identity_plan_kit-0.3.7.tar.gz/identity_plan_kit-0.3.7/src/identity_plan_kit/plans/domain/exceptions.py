"""Plans domain exceptions with error codes."""

from datetime import date

from identity_plan_kit.shared.exceptions import (
    AuthorizationError,
    NotFoundError,
    RateLimitError,
)


class PlanError(AuthorizationError):
    """Base exception for plan errors."""

    code = "PLAN_ERROR"
    message = "Plan error"


class PlanNotFoundError(NotFoundError):
    """Plan not found."""

    code = "PLAN_NOT_FOUND"
    message = "Plan not found"

    def __init__(self, plan_code: str | None = None) -> None:
        self.plan_code = plan_code
        msg = f"Plan not found: {plan_code}" if plan_code else "Plan not found"
        super().__init__(message=msg, details={"plan_code": plan_code} if plan_code else None)


class UserPlanNotFoundError(PlanError):
    """User has no active plan."""

    code = "USER_PLAN_NOT_FOUND"
    message = "No active plan"
    status_code = 402  # Payment Required


class PlanExpiredError(PlanError):
    """User's plan has expired."""

    code = "PLAN_EXPIRED"
    message = "Plan has expired"
    status_code = 402  # Payment Required


class FeatureNotFoundError(NotFoundError):
    """Feature does not exist."""

    code = "FEATURE_NOT_FOUND"
    message = "Feature not found"

    def __init__(self, feature_code: str | None = None) -> None:
        self.feature_code = feature_code
        msg = f"Feature not found: {feature_code}" if feature_code else "Feature not found"
        super().__init__(
            message=msg, details={"feature_code": feature_code} if feature_code else None
        )


class FeatureNotAvailableError(PlanError):
    """Feature not available in user's plan."""

    code = "FEATURE_NOT_AVAILABLE"
    message = "Feature not available"

    def __init__(
        self,
        feature_code: str | None = None,
        plan_code: str | None = None,
    ) -> None:
        self.feature_code = feature_code
        self.plan_code = plan_code
        msg = f"Feature '{feature_code}' not available"
        if plan_code:
            msg += f" in plan '{plan_code}'"
        super().__init__(
            message=msg,
            details={"feature_code": feature_code, "plan_code": plan_code},
        )


class QuotaExceededError(RateLimitError):
    """Usage quota exceeded."""

    code = "QUOTA_EXCEEDED"
    message = "Usage quota exceeded"

    def __init__(
        self,
        feature_code: str,
        limit: int,
        used: int,
        period: str | None = None,
    ) -> None:
        self.feature_code = feature_code
        self.limit = limit
        self.used = used
        self.period = period

        msg = f"Quota exceeded for '{feature_code}': {used}/{limit}"
        if period:
            msg += f" ({period})"
        super().__init__(
            message=msg,
            details={
                "feature_code": feature_code,
                "limit": limit,
                "used": used,
                "period": period,
                "remaining": limit - used,
            },
        )

    @property
    def remaining(self) -> int:
        """Get remaining quota (can be negative if over limit)."""
        return self.limit - self.used


class InvalidPlanDatesError(PlanError):
    """Invalid plan date range."""

    code = "INVALID_PLAN_DATES"
    message = "Invalid plan date range"
    status_code = 400  # Bad Request

    def __init__(
        self,
        message: str,
        started_at: date | None = None,
        ends_at: date | None = None,
    ) -> None:
        self.started_at = started_at
        self.ends_at = ends_at
        super().__init__(
            message=message,
            details={
                "started_at": str(started_at) if started_at else None,
                "ends_at": str(ends_at) if ends_at else None,
            },
        )


class InvalidCustomLimitsError(PlanError):
    """Invalid custom limits value."""

    code = "INVALID_CUSTOM_LIMITS"
    message = "Invalid custom limits"
    status_code = 400  # Bad Request

    def __init__(
        self,
        message: str,
        invalid_keys: list[str] | None = None,
    ) -> None:
        self.invalid_keys = invalid_keys or []
        super().__init__(
            message=message,
            details={"invalid_keys": self.invalid_keys} if self.invalid_keys else None,
        )


class PlanAssignmentError(PlanError):
    """Error assigning plan to user."""

    code = "PLAN_ASSIGNMENT_ERROR"
    message = "Failed to assign plan"
    status_code = 400  # Bad Request

    def __init__(
        self,
        message: str,
        user_id: str | None = None,
        plan_id: str | None = None,
    ) -> None:
        self.user_id = user_id
        self.plan_id = plan_id
        super().__init__(
            message=message,
            details={"user_id": user_id, "plan_id": plan_id},
        )


class UserNotFoundError(NotFoundError):
    """User not found (foreign key constraint violation)."""

    code = "USER_NOT_FOUND"
    message = "User not found"

    def __init__(self, user_id: str | None = None) -> None:
        self.user_id = user_id
        msg = f"User not found: {user_id}" if user_id else "User not found"
        super().__init__(message=msg, details={"user_id": user_id} if user_id else None)


class PlanAuthorizationError(AuthorizationError):
    """Raised when a plan operation is not authorized.

    This exception is raised when the authorization callback returns False
    for a privileged plan operation.
    """

    code = "PLAN_AUTHORIZATION_ERROR"
    message = "Not authorized to perform this operation"

    def __init__(
        self,
        message: str,
        operation: str,
        target_user_id: str,
        caller_user_id: str | None = None,
    ) -> None:
        self.operation = operation
        self.target_user_id = target_user_id
        self.caller_user_id = caller_user_id
        super().__init__(
            message=message,
            details={
                "operation": operation,
                "target_user_id": target_user_id,
                "caller_user_id": caller_user_id,
            },
        )
