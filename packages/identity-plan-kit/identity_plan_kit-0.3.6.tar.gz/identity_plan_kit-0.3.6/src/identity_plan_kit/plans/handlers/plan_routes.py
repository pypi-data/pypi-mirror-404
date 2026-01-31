"""Plans API routes."""

from fastapi import APIRouter, Request

from identity_plan_kit.config import IdentityPlanKitConfig
from identity_plan_kit.plans.dto.responses import (
    FeatureResponse,
    FeaturesListResponse,
    PlanLimitResponse,
    PlanResponse,
    PlansListResponse,
)
from identity_plan_kit.shared.logging import get_logger
from identity_plan_kit.shared.rate_limiter import get_rate_limiter
from identity_plan_kit.shared.schemas import ResponseModel

logger = get_logger(__name__)


def create_plans_router(config: IdentityPlanKitConfig) -> APIRouter:
    """
    Create plans router with endpoints for listing plans and features.

    Args:
        config: IdentityPlanKit configuration

    Returns:
        FastAPI router with plans endpoints
    """
    router = APIRouter(tags=["plans"])
    rate_limiter = get_rate_limiter()

    @router.get(
        "",
        response_model=ResponseModel[PlansListResponse],
        summary="Get all plans",
        description="Get all available plans with their features and limits. "
        "This endpoint is optimized to fetch all data in minimal database queries.",
    )
    @rate_limiter.limit(config.rate_limit_plans)
    async def get_all_plans(request: Request) -> ResponseModel[PlansListResponse]:
        """
        Get all plans with features and limits.

        Returns all available subscription plans with:
        - Plan details (code, name)
        - Permissions granted by each plan
        - Feature limits (with period information)

        This endpoint is optimized to load all plans with their nested
        relationships in 3 database queries instead of N+1.
        """
        kit = request.app.state.identity_plan_kit
        plans = await kit.plan_service.get_all_plans()

        plan_responses = []
        for plan in plans:
            limits = [
                PlanLimitResponse(
                    feature_id=limit.feature_id,
                    feature_code=limit.feature_code,
                    limit=limit.limit,
                    period=limit.period.value if limit.period else None,
                )
                for limit in plan.limits.values()
            ]

            plan_responses.append(
                PlanResponse(
                    id=plan.id,
                    code=plan.code,
                    name=plan.name,
                    permissions=sorted(plan.permissions),
                    limits=limits,
                )
            )

        return ResponseModel.ok(data=PlansListResponse(plans=plan_responses))

    @router.get(
        "/features",
        response_model=ResponseModel[FeaturesListResponse],
        summary="Get all features",
        description="Get all available features that can be used in plans.",
    )
    @rate_limiter.limit(config.rate_limit_plans)
    async def get_all_features(request: Request) -> ResponseModel[FeaturesListResponse]:
        """
        Get all features.

        Returns all available features that can be configured with limits in plans.
        """
        kit = request.app.state.identity_plan_kit
        features = await kit.plan_service.get_all_features()

        feature_responses = [
            FeatureResponse(
                id=feature.id,
                code=feature.code,
                name=feature.name,
            )
            for feature in features
        ]

        return ResponseModel.ok(data=FeaturesListResponse(features=feature_responses))

    return router
