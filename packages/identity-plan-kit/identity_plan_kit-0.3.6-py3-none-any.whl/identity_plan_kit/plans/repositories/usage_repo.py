"""Usage repository for tracking feature usage."""

from calendar import monthrange
from datetime import date
from uuid import UUID

from sqlalchemy import and_, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from identity_plan_kit.plans.domain.entities import FeatureUsage, PeriodType
from identity_plan_kit.plans.models.feature_usage import FeatureUsageModel
from identity_plan_kit.shared.logging import get_logger
from identity_plan_kit.shared.uuid7 import uuid7

logger = get_logger(__name__)

# Default lifetime period boundaries (can be overridden via config)
DEFAULT_LIFETIME_START_YEAR = 2000
DEFAULT_LIFETIME_END_YEAR = 2100


class QuotaExceededInRepoError(Exception):
    """Raised when atomic quota check fails due to limit exceeded."""

    def __init__(self, current_usage: int, limit: int, requested: int) -> None:
        self.current_usage = current_usage
        self.limit = limit
        self.requested = requested
        super().__init__(f"Quota exceeded: {current_usage}+{requested} > {limit}")


class UsageRepository:
    """Repository for feature usage data access."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_current_usage(
        self,
        user_plan_id: UUID,
        feature_id: UUID,
        period: PeriodType | None,
    ) -> int:
        """
        Get current usage for a feature in the current period.

        Args:
            user_plan_id: User plan UUID
            feature_id: Feature UUID
            period: Period type (daily/monthly/None)

        Returns:
            Current usage count
        """
        start, end = self._get_period_range(period)

        stmt = select(FeatureUsageModel.feature_usage).where(
            FeatureUsageModel.user_plan_id == user_plan_id,
            FeatureUsageModel.feature_id == feature_id,
            FeatureUsageModel.start_period == start,
            FeatureUsageModel.end_period == end,
        )
        result = await self._session.execute(stmt)
        usage = result.scalar_one_or_none()

        return usage or 0

    async def record_usage(
        self,
        user_plan_id: UUID,
        feature_id: UUID,
        amount: int,
        period: PeriodType | None,
    ) -> int:
        """
        Record feature usage, creating or updating the usage record.

        Uses upsert for atomicity.

        Args:
            user_plan_id: User plan UUID
            feature_id: Feature UUID
            amount: Amount to add
            period: Period type

        Returns:
            New total usage
        """
        start, end = self._get_period_range(period)

        # Upsert usage record
        stmt = insert(FeatureUsageModel).values(
            id=uuid7(),
            user_plan_id=user_plan_id,
            feature_id=feature_id,
            feature_usage=amount,
            start_period=start,
            end_period=end,
        )
        stmt = stmt.on_conflict_do_update(
            constraint="uq_usage_plan_feature_period",
            set_={"feature_usage": FeatureUsageModel.feature_usage + amount},
        ).returning(FeatureUsageModel.feature_usage)

        result = await self._session.execute(stmt)
        new_usage = result.scalar_one()
        await self._session.flush()

        return new_usage

    async def atomic_check_and_consume(
        self,
        user_plan_id: UUID,
        feature_id: UUID,
        amount: int,
        limit: int,
        period: PeriodType | None,
    ) -> int:
        """
        Atomically check quota and consume if within limit.

        P0 FIX: Prevents TOCTOU race condition by using conditional UPDATE/INSERT
        that only succeeds if the resulting usage is within the limit.

        For unlimited quotas (limit=-1), this always succeeds.

        Args:
            user_plan_id: User plan UUID
            feature_id: Feature UUID
            amount: Amount to consume
            limit: Usage limit (-1 for unlimited)
            period: Period type

        Returns:
            New total usage after consumption

        Raises:
            QuotaExceededInRepoError: If consumption would exceed limit
        """
        start, end = self._get_period_range(period)

        # For unlimited, just record usage without checking
        if limit == -1:
            return await self.record_usage(user_plan_id, feature_id, amount, period)

        # Check if initial amount exceeds limit (fast fail)
        if amount > limit:
            raise QuotaExceededInRepoError(current_usage=0, limit=limit, requested=amount)

        # Use INSERT...ON CONFLICT DO UPDATE with WHERE clause for atomic operation
        # This handles both new record creation and existing record update atomically
        #
        # The WHERE clause on ON CONFLICT DO UPDATE ensures:
        # - INSERT succeeds if no conflict and amount <= limit (guaranteed by check above)
        # - UPDATE only happens if current_usage + amount <= limit
        #
        # If WHERE clause fails (limit would be exceeded), RETURNING returns nothing
        upsert_stmt = insert(FeatureUsageModel).values(
            id=uuid7(),
            user_plan_id=user_plan_id,
            feature_id=feature_id,
            feature_usage=amount,
            start_period=start,
            end_period=end,
        )

        upsert_stmt = upsert_stmt.on_conflict_do_update(
            constraint="uq_usage_plan_feature_period",
            set_={"feature_usage": FeatureUsageModel.feature_usage + amount},
            # Only update if the new total is within the limit
            where=FeatureUsageModel.feature_usage + amount <= limit,
        ).returning(FeatureUsageModel.feature_usage)

        result = await self._session.execute(upsert_stmt)
        new_usage = result.scalar_one_or_none()

        if new_usage is not None:
            await self._session.flush()
            return new_usage

        # RETURNING was None - this means ON CONFLICT DO UPDATE's WHERE clause
        # didn't match (limit would be exceeded)
        # Get current usage for the error message
        current = await self.get_current_usage(user_plan_id, feature_id, period)
        raise QuotaExceededInRepoError(current_usage=current, limit=limit, requested=amount)

    async def get_all_usage(
        self,
        user_plan_id: UUID,
    ) -> list[FeatureUsage]:
        """
        Get all current usage for a user plan.

        Args:
            user_plan_id: User plan UUID

        Returns:
            List of current usage records
        """
        today = date.today()
        stmt = (
            select(FeatureUsageModel)
            .options(selectinload(FeatureUsageModel.feature))
            .where(
                FeatureUsageModel.user_plan_id == user_plan_id,
                FeatureUsageModel.start_period <= today,
                FeatureUsageModel.end_period >= today,
            )
        )
        result = await self._session.execute(stmt)
        models = result.scalars().all()

        return [self._to_entity(m) for m in models]

    async def reset_usage(
        self,
        user_plan_id: UUID,
        feature_id: UUID,
    ) -> None:
        """
        Reset usage for a feature (manual reset).

        Args:
            user_plan_id: User plan UUID
            feature_id: Feature UUID
        """
        today = date.today()
        stmt = (
            update(FeatureUsageModel)
            .where(
                FeatureUsageModel.user_plan_id == user_plan_id,
                FeatureUsageModel.feature_id == feature_id,
                FeatureUsageModel.start_period <= today,
                FeatureUsageModel.end_period >= today,
            )
            .values(feature_usage=0)
        )
        await self._session.execute(stmt)
        await self._session.flush()

    async def reset_all_usage(
        self,
        user_plan_id: UUID,
    ) -> int:
        """
        Reset all usage for a user plan in a single query.

        More efficient than calling reset_usage() in a loop.

        Args:
            user_plan_id: User plan UUID

        Returns:
            Number of usage records reset
        """
        today = date.today()
        stmt = (
            update(FeatureUsageModel)
            .where(
                FeatureUsageModel.user_plan_id == user_plan_id,
                FeatureUsageModel.start_period <= today,
                FeatureUsageModel.end_period >= today,
            )
            .values(feature_usage=0)
        )
        result = await self._session.execute(stmt)
        await self._session.flush()
        return result.rowcount

    def _get_period_range(self, period: PeriodType | None) -> tuple[date, date]:
        """
        Get start and end dates for a period.

        Args:
            period: Period type

        Returns:
            Tuple of (start_date, end_date)
        """
        today = date.today()

        if period == PeriodType.DAILY:
            return today, today
        if period == PeriodType.MONTHLY:
            start = today.replace(day=1)
            _, last_day = monthrange(today.year, today.month)
            end = today.replace(day=last_day)
            return start, end
        # No period = lifetime (use far future date)
        return (
            date(DEFAULT_LIFETIME_START_YEAR, 1, 1),
            date(DEFAULT_LIFETIME_END_YEAR, 12, 31),
        )

    def _to_entity(self, model: FeatureUsageModel) -> FeatureUsage:
        """
        Convert model to entity.

        Note: This method expects the feature relationship to be loaded.
        """
        if model.feature is None:
            logger.error(
                "feature_usage_missing_feature_relationship",
                feature_usage_id=str(model.id),
                feature_id=str(model.feature_id),
            )
            raise RuntimeError(
                f"FeatureUsage {model.id} has no feature loaded. "
                "Ensure selectinload(FeatureUsageModel.feature) is used in the query."
            )

        return FeatureUsage(
            id=model.id,
            user_plan_id=model.user_plan_id,
            feature_id=model.feature_id,
            feature_code=model.feature.code,
            usage=model.feature_usage,
            start_period=model.start_period,
            end_period=model.end_period,
        )
