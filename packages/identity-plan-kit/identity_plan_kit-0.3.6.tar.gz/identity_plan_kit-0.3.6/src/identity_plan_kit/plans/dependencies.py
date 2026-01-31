"""Plans FastAPI dependencies."""

from collections.abc import Callable
from typing import TYPE_CHECKING, Annotated, Any

from fastapi import Depends, HTTPException, Request, Response, status

from identity_plan_kit.auth.dependencies import CurrentUser
from identity_plan_kit.plans.domain.exceptions import (
    FeatureNotAvailableError,
    PlanExpiredError,
    QuotaExceededError,
    UserPlanNotFoundError,
)
from identity_plan_kit.plans.dto.usage import UsageInfo
from identity_plan_kit.shared.logging import get_logger

if TYPE_CHECKING:
    from identity_plan_kit import IdentityPlanKit
logger = get_logger(__name__)


def requires_plan(plan_code: str | None = None) -> Callable[..., Any]:
    """
    Dependency that requires user to have an active plan.

    Optionally requires a specific plan.

    Usage:
        @app.get("/pro/feature")
        @requires_plan("pro")
        async def pro_feature(user: CurrentUser):
            ...

        @app.get("/any-plan")
        @requires_plan()
        async def any_plan_feature(user: CurrentUser):
            ...

    Args:
        plan_code: Required plan code (None = any plan)

    Returns:
        FastAPI dependency
    """

    async def dependency(
        request: Request,
        user: CurrentUser,
    ) -> None:
        kit = request.app.state.identity_plan_kit
        plan_service = kit.plan_service

        try:
            user_plan = await plan_service.get_user_plan(user.id)

            if plan_code and user_plan.plan_code != plan_code:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Required plan: {plan_code}",
                )

        except (UserPlanNotFoundError, PlanExpiredError):
            # Let exception handlers process these with proper error codes
            raise

    return Depends(dependency)


def requires_feature(
    feature_code: str,
    consume: int = 0,
    include_headers: bool = True,
) -> Callable[..., Any]:
    """
    Dependency that requires access to a feature and optionally consumes quota.

    Returns UsageInfo containing current usage state (used, limit, remaining).
    This allows endpoints to include usage information in their responses
    without additional database queries.

    **Idempotency Support:**

    When ``consume > 0`` and the request includes an ``X-Idempotency-Key`` header,
    the quota consumption is idempotent. Duplicate requests with the same key
    within the configured TTL window return cached results without double-deducting.

    Usage:
        @app.post("/api/generate")
        async def generate(
            user: CurrentUser,
            usage: Annotated[UsageInfo, requires_feature("ai_generation", consume=1)],
        ):
            # usage contains: used, limit, remaining, period
            # Client can include X-Idempotency-Key header for safe retries
            return {"success": True, "usage": usage_to_dict(usage)}

        @app.get("/api/exports")
        async def list_exports(
            user: CurrentUser,
            _: Annotated[UsageInfo, requires_feature("exports")],  # Just check access
        ):
            ...

    Args:
        feature_code: Required feature code
        consume: Amount of quota to consume (0 = just check access)
        include_headers: If True, adds X-Quota-* headers to the response

    Returns:
        FastAPI dependency that yields UsageInfo
    """

    async def dependency(
        request: Request,
        response: Response,
        user: CurrentUser,
    ) -> UsageInfo:
        kit: IdentityPlanKit = request.app.state.identity_plan_kit
        plan_service = kit.plan_service

        try:
            if consume > 0:
                # Extract idempotency key from header for safe retries
                idempotency_key = request.headers.get("X-Idempotency-Key")

                # Check and consume quota - returns UsageInfo
                # When idempotency_key provided, duplicate requests return cached result
                usage_info = await plan_service.check_and_consume_quota(
                    user_id=user.id,
                    feature_code=feature_code,
                    amount=consume,
                    idempotency_key=idempotency_key,
                )
            else:
                # Just check access and get current usage info
                usage_info = await plan_service.get_usage_info(
                    user_id=user.id,
                    feature_code=feature_code,
                )

            # Add quota headers to response
            if include_headers:
                response.headers["X-Quota-Limit"] = str(usage_info.limit)
                response.headers["X-Quota-Used"] = str(usage_info.used)
                response.headers["X-Quota-Remaining"] = str(usage_info.remaining)
                if usage_info.period:
                    response.headers["X-Quota-Period"] = usage_info.period

            return usage_info

        except (QuotaExceededError, UserPlanNotFoundError, PlanExpiredError, FeatureNotAvailableError):
            # Let exception handlers process these with proper error codes
            # Quota headers are added by quota_exceeded_handler
            raise

    return Depends(dependency)


def FeatureUsage(  # noqa: N802 - intentionally PascalCase for type alias convention
    feature_code: str,
    consume: int = 0,
    include_headers: bool = True,
) -> Any:
    """
    Type alias factory for requires_feature dependency.

    Provides cleaner type annotations in endpoint definitions:

        @app.post("/api/generate")
        async def generate(
            user: CurrentUser,
            usage: FeatureUsage("ai_generation", consume=1),
        ):
            # Client can include X-Idempotency-Key header for safe retries
            return {"success": True, "remaining": usage.remaining}

    This is equivalent to:
        usage: Annotated[UsageInfo, requires_feature("ai_generation", consume=1)]

    **Idempotency:** When ``consume > 0``, the ``X-Idempotency-Key`` request header
    enables safe retries without double-deducting quota.

    Args:
        feature_code: Required feature code
        consume: Amount of quota to consume (0 = just check access)
        include_headers: If True, adds X-Quota-* headers to the response

    Returns:
        Annotated type hint with the dependency
    """
    return Annotated[UsageInfo, requires_feature(feature_code, consume, include_headers)]
