"""Plans response DTOs."""

from uuid import UUID

from pydantic import Field

from identity_plan_kit.shared.schemas import BaseResponse


class FeatureResponse(BaseResponse):
    """Feature information."""

    id: UUID = Field(
        ...,
        description="Feature ID",
    )
    code: str = Field(
        ...,
        description="Feature code (e.g., 'api_calls', 'storage')",
    )
    name: str = Field(
        ...,
        description="Human-readable feature name",
    )


class PlanLimitResponse(BaseResponse):
    """Feature limit within a plan."""

    feature_id: UUID = Field(
        ...,
        description="Feature ID",
    )
    feature_code: str = Field(
        ...,
        description="Feature code",
    )
    limit: int = Field(
        ...,
        description="Usage limit (-1 for unlimited)",
    )
    period: str | None = Field(
        default=None,
        description="Period type: 'daily', 'monthly', or null for lifetime",
    )


class PlanResponse(BaseResponse):
    """Plan with all features and limits."""

    id: UUID = Field(
        ...,
        description="Plan ID",
    )
    code: str = Field(
        ...,
        description="Plan code (e.g., 'free', 'pro', 'enterprise')",
    )
    name: str = Field(
        ...,
        description="Human-readable plan name",
    )
    permissions: list[str] = Field(
        default_factory=list,
        description="List of permissions granted by this plan",
    )
    limits: list[PlanLimitResponse] = Field(
        default_factory=list,
        description="Feature limits for this plan",
    )


class PlansListResponse(BaseResponse):
    """List of all plans."""

    plans: list[PlanResponse] = Field(
        ...,
        description="List of all available plans",
    )


class FeaturesListResponse(BaseResponse):
    """List of all features."""

    features: list[FeatureResponse] = Field(
        ...,
        description="List of all available features",
    )


class QuotaResponse(BaseResponse):
    """
    Quota/usage information for a feature.

    Include this in your API responses to inform users about their current
    usage state without additional database queries.

    Example usage:
        @app.post("/api/generate")
        async def generate(
            user: CurrentUser,
            usage: Annotated[UsageInfo, requires_feature("ai_generation", consume=1)],
        ) -> GenerateResponse:
            result = await do_generation()
            return GenerateResponse(
                data=result,
                quota=QuotaResponse.from_usage_info(usage),
            )
    """

    used: int = Field(
        ...,
        description="Current usage count in the period",
    )
    limit: int = Field(
        ...,
        description="Usage limit for the period (-1 for unlimited)",
    )
    remaining: int = Field(
        ...,
        description="Remaining quota (-1 for unlimited)",
    )
    period: str | None = Field(
        default=None,
        description="Period type: 'daily', 'monthly', or null for lifetime",
    )

    @classmethod
    def from_usage_info(cls, usage_info: "UsageInfo") -> "QuotaResponse":
        """
        Create QuotaResponse from UsageInfo dataclass.

        This is the recommended way to include quota in responses:
            quota=QuotaResponse.from_usage_info(usage)
        """
        return cls(
            used=usage_info.used,
            limit=usage_info.limit,
            remaining=usage_info.remaining,
            period=usage_info.period,
        )


# Import UsageInfo for type hints (avoid circular import)
from identity_plan_kit.plans.dto.usage import UsageInfo  # noqa: E402
