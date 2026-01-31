"""Plan repository for data access."""

from datetime import date, datetime, timedelta, timezone
from typing import Any
from uuid import UUID

from sqlalchemy import delete, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from identity_plan_kit.plans.domain.entities import (
    Feature,
    PeriodType,
    Plan,
    PlanLimit,
    UserPlan,
)
from identity_plan_kit.plans.domain.exceptions import (
    PlanAssignmentError,
    PlanNotFoundError,
    UserNotFoundError,
)
from identity_plan_kit.plans.models.feature import FeatureModel
from identity_plan_kit.plans.models.plan import PlanModel
from identity_plan_kit.plans.models.plan_limit import PlanLimitModel
from identity_plan_kit.plans.models.plan_permission import PlanPermissionModel
from identity_plan_kit.plans.models.user_plan import UserPlanModel
from identity_plan_kit.shared.logging import get_logger
from identity_plan_kit.shared.uuid7 import uuid7

logger = get_logger(__name__)

# Default "lifetime" plan duration in years from today
# Used when no ends_at is provided for plan assignment
LIFETIME_PLAN_YEARS = 100


class PlanRepository:
    """Repository for plan data access."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_all_plans(self) -> list[Plan]:
        """
        Get all plans with their permissions and limits.

        This is an optimized method that loads all plans with their
        nested relationships in 3 queries (plans, permissions, limits)
        instead of N+1 queries.

        Returns:
            List of all Plan entities with permissions and limits
        """
        stmt = (
            select(PlanModel)
            .options(
                selectinload(PlanModel.permissions).selectinload(PlanPermissionModel.permission),
                selectinload(PlanModel.limits).selectinload(PlanLimitModel.feature),
            )
            .order_by(PlanModel.name)
        )
        result = await self._session.execute(stmt)
        models = result.scalars().all()

        return [self._plan_to_entity(model) for model in models]

    async def get_all_features(self) -> list[Feature]:
        """
        Get all features.

        Returns:
            List of all Feature entities
        """
        stmt = select(FeatureModel).order_by(FeatureModel.name)
        result = await self._session.execute(stmt)
        models = result.scalars().all()

        return [Feature(id=model.id, code=model.code, name=model.name) for model in models]

    async def get_plan_by_id(self, plan_id: UUID) -> Plan | None:
        """
        Get plan by ID with permissions and limits.

        Args:
            plan_id: Plan UUID

        Returns:
            Plan entity or None
        """
        stmt = (
            select(PlanModel)
            .options(
                selectinload(PlanModel.permissions).selectinload(PlanPermissionModel.permission),
                selectinload(PlanModel.limits).selectinload(PlanLimitModel.feature),
            )
            .where(PlanModel.id == plan_id)
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()

        if model is None:
            return None

        return self._plan_to_entity(model)

    async def get_plan_by_code(self, code: str) -> Plan | None:
        """
        Get plan by code.

        Args:
            code: Plan code (e.g., "pro")

        Returns:
            Plan entity or None
        """
        stmt = (
            select(PlanModel)
            .options(
                selectinload(PlanModel.permissions).selectinload(PlanPermissionModel.permission),
                selectinload(PlanModel.limits).selectinload(PlanLimitModel.feature),
            )
            .where(PlanModel.code == code)
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()

        if model is None:
            return None

        return self._plan_to_entity(model)

    async def get_user_active_plan(
        self,
        user_id: UUID,
        for_update: bool = False,
    ) -> UserPlan | None:
        """
        Get user's active plan.

        Args:
            user_id: User UUID
            for_update: If True, lock the row for update (prevents race conditions
                in read-modify-write operations like custom limits merge)

        Returns:
            UserPlan entity or None
        """
        today = date.today()
        stmt = (
            select(UserPlanModel)
            .options(selectinload(UserPlanModel.plan))
            .where(
                UserPlanModel.user_id == user_id,
                UserPlanModel.started_at <= today,
                UserPlanModel.ends_at >= today,
            )
            .order_by(UserPlanModel.ends_at.desc())
            .limit(1)
        )

        # Apply row-level lock if requested (prevents race conditions)
        if for_update:
            stmt = stmt.with_for_update()

        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()

        if model is None:
            return None

        return self._user_plan_to_entity(model)

    async def get_user_active_plan_with_details(
        self, user_id: UUID
    ) -> tuple[UserPlan, Plan] | None:
        """
        Get user's active plan with full plan details (permissions and limits).

        This is an optimized method that loads everything in a single query,
        avoiding the N+1 problem of fetching user_plan then plan separately.

        Args:
            user_id: User UUID

        Returns:
            Tuple of (UserPlan, Plan) or None if no active plan
        """
        today = date.today()
        stmt = (
            select(UserPlanModel)
            .options(
                selectinload(UserPlanModel.plan).options(
                    selectinload(PlanModel.permissions).selectinload(
                        PlanPermissionModel.permission
                    ),
                    selectinload(PlanModel.limits).selectinload(PlanLimitModel.feature),
                )
            )
            .where(
                UserPlanModel.user_id == user_id,
                UserPlanModel.started_at <= today,
                UserPlanModel.ends_at >= today,
            )
            .order_by(UserPlanModel.ends_at.desc())
            .limit(1)
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()

        if model is None:
            return None

        user_plan = self._user_plan_to_entity(model)
        plan = self._plan_to_entity(model.plan)

        return user_plan, plan

    async def get_plan_limit(
        self,
        plan_id: UUID,
        feature_code: str,
    ) -> PlanLimit | None:
        """
        Get limit for a feature in a plan.

        Args:
            plan_id: Plan UUID
            feature_code: Feature code

        Returns:
            PlanLimit entity or None
        """
        stmt = (
            select(PlanLimitModel)
            .join(FeatureModel)
            .options(selectinload(PlanLimitModel.feature))
            .where(
                PlanLimitModel.plan_id == plan_id,
                FeatureModel.code == feature_code,
            )
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()

        if model is None:
            return None

        return self._limit_to_entity(model)

    async def get_feature_by_code(self, code: str) -> Feature | None:
        """
        Get feature by code.

        Args:
            code: Feature code

        Returns:
            Feature entity or None
        """
        stmt = select(FeatureModel).where(FeatureModel.code == code)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()

        if model is None:
            return None

        return Feature(id=model.id, code=model.code, name=model.name)

    def _plan_to_entity(self, model: PlanModel) -> Plan:
        """
        Convert plan model to entity.

        Note: This method expects relationships (permissions, limits) to be loaded.
        Use selectinload() when querying plans.
        """
        permissions: set[str] = set()
        for pp in model.permissions:
            if pp.permission is None:
                logger.warning(
                    "plan_permission_missing_relationship",
                    plan_id=str(model.id),
                    plan_permission_id=str(pp.id),
                )
                continue
            permissions.add(pp.permission.code)

        limits: dict[str, PlanLimit] = {}
        for pl in model.limits:
            if pl.feature is None:
                logger.warning(
                    "plan_limit_missing_feature_relationship",
                    plan_id=str(model.id),
                    plan_limit_id=str(pl.id),
                )
                continue
            limits[pl.feature.code] = self._limit_to_entity(pl)

        return Plan(
            id=model.id,
            code=model.code,
            name=model.name,
            permissions=permissions,
            limits=limits,
        )

    def _user_plan_to_entity(self, model: UserPlanModel) -> UserPlan:
        """
        Convert user plan model to entity.

        Note: This method expects the plan relationship to be loaded.
        Use selectinload(UserPlanModel.plan) when querying user plans.
        """
        if model.plan is None:
            # This indicates a bug - plan relationship should always be loaded
            logger.error(
                "user_plan_missing_plan_relationship",
                user_plan_id=str(model.id),
                plan_id=str(model.plan_id),
            )
            raise RuntimeError(
                f"UserPlan {model.id} has no plan loaded. "
                "Ensure selectinload(UserPlanModel.plan) is used in the query."
            )

        return UserPlan(
            id=model.id,
            user_id=model.user_id,
            plan_id=model.plan_id,
            plan_code=model.plan.code,
            started_at=model.started_at,
            ends_at=model.ends_at,
            custom_limits=model.custom_limits or {},
        )

    def _limit_to_entity(self, model: PlanLimitModel) -> PlanLimit:
        """
        Convert limit model to entity.

        Note: This method expects the feature relationship to be loaded.
        """
        if model.feature is None:
            logger.error(
                "plan_limit_missing_feature_relationship",
                plan_limit_id=str(model.id),
                feature_id=str(model.feature_id),
            )
            raise RuntimeError(
                f"PlanLimit {model.id} has no feature loaded. "
                "Ensure selectinload(PlanLimitModel.feature) is used in the query."
            )

        period = PeriodType(model.period) if model.period else None
        return PlanLimit(
            id=model.id,
            plan_id=model.plan_id,
            feature_id=model.feature_id,
            feature_code=model.feature.code,
            limit=model.feature_limit,
            period=period,
        )

    async def create_user_plan(
        self,
        user_id: UUID,
        plan_id: UUID,
        started_at: date | None = None,
        ends_at: date | None = None,
        custom_limits: dict[str, Any] | None = None,
    ) -> UserPlan:
        """
        Create a user plan assignment.

        Args:
            user_id: User UUID
            plan_id: Plan UUID to assign
            started_at: Plan start date (defaults to today)
            ends_at: Plan end date (defaults to LIFETIME_PLAN_YEARS from now)
            custom_limits: Optional custom limits override

        Returns:
            Created UserPlan entity

        Raises:
            UserNotFoundError: If user_id doesn't exist
            PlanNotFoundError: If plan_id doesn't exist
            PlanAssignmentError: For other database constraint violations
        """
        today = date.today()
        # Default to "lifetime" plan if no end date specified
        default_ends_at = date(today.year + LIFETIME_PLAN_YEARS, today.month, today.day)
        model = UserPlanModel(
            id=uuid7(),
            user_id=user_id,
            plan_id=plan_id,
            started_at=started_at or today,
            ends_at=ends_at or default_ends_at,
            custom_limits=custom_limits or {},
        )
        self._session.add(model)

        try:
            await self._session.flush()
        except IntegrityError as e:
            await self._session.rollback()
            error_msg = str(e.orig) if e.orig else str(e)

            # Check for specific foreign key violations
            if "user_plans_user_id_fkey" in error_msg or "users" in error_msg.lower():
                logger.warning(
                    "user_plan_creation_failed_user_not_found",
                    user_id=str(user_id),
                    plan_id=str(plan_id),
                )
                raise UserNotFoundError(user_id=str(user_id)) from e

            if "user_plans_plan_id_fkey" in error_msg or "plans" in error_msg.lower():
                logger.warning(
                    "user_plan_creation_failed_plan_not_found",
                    user_id=str(user_id),
                    plan_id=str(plan_id),
                )
                raise PlanNotFoundError(plan_code=str(plan_id)) from e

            # Generic constraint violation
            logger.error(
                "user_plan_creation_failed",
                user_id=str(user_id),
                plan_id=str(plan_id),
                error=error_msg,
            )
            raise PlanAssignmentError(
                message=f"Failed to assign plan: {error_msg}",
                user_id=str(user_id),
                plan_id=str(plan_id),
            ) from e

        # Reload with relationships
        await self._session.refresh(model, ["plan"])

        logger.info(
            "user_plan_created",
            user_id=str(user_id),
            plan_id=str(plan_id),
        )

        return self._user_plan_to_entity(model)

    async def get_user_plan_by_id(self, user_plan_id: UUID) -> UserPlan | None:
        """
        Get a user plan by its ID.

        Args:
            user_plan_id: UserPlan UUID

        Returns:
            UserPlan entity or None
        """
        stmt = (
            select(UserPlanModel)
            .options(selectinload(UserPlanModel.plan))
            .where(UserPlanModel.id == user_plan_id)
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()

        if model is None:
            return None

        return self._user_plan_to_entity(model)

    async def update_user_plan(
        self,
        user_plan_id: UUID,
        ends_at: date | None = None,
        custom_limits: dict[str, Any] | None = None,
    ) -> UserPlan | None:
        """
        Update a user plan.

        Args:
            user_plan_id: UserPlan UUID
            ends_at: New end date (None to keep current)
            custom_limits: New custom limits (None to keep current)

        Returns:
            Updated UserPlan entity or None if not found
        """
        # Build update values
        values: dict[str, Any] = {}
        if ends_at is not None:
            values["ends_at"] = ends_at
        if custom_limits is not None:
            values["custom_limits"] = custom_limits

        if not values:
            # Nothing to update, just return current
            return await self.get_user_plan_by_id(user_plan_id)

        stmt = (
            update(UserPlanModel)
            .where(UserPlanModel.id == user_plan_id)
            .values(**values)
            .returning(UserPlanModel.id)
        )
        result = await self._session.execute(stmt)
        updated_id = result.scalar_one_or_none()

        if updated_id is None:
            return None

        await self._session.flush()

        logger.info(
            "user_plan_updated",
            user_plan_id=str(user_plan_id),
            updates=list(values.keys()),
        )

        return await self.get_user_plan_by_id(user_plan_id)

    async def cancel_user_plan(
        self,
        user_id: UUID,
        immediate: bool = False,
    ) -> bool:
        """
        Cancel user's active plan.

        Args:
            user_id: User UUID
            immediate: If True, cancel immediately (ends_at = yesterday).
                      If False, plan is marked as cancelled but remains active
                      until current ends_at (scheduled cancellation).

        Returns:
            True if a plan was cancelled, False if no active plan found
        """
        user_plan = await self.get_user_active_plan(user_id)
        if user_plan is None:
            return False

        now = datetime.now(timezone.utc)
        values: dict[str, Any] = {
            "is_cancelled": True,
            "cancelled_at": now,
        }

        if immediate:
            # Set ends_at to yesterday to immediately deactivate
            values["ends_at"] = date.today() - timedelta(days=1)

        stmt = (
            update(UserPlanModel)
            .where(UserPlanModel.id == user_plan.id)
            .values(**values)
        )
        await self._session.execute(stmt)
        await self._session.flush()

        logger.info(
            "user_plan_cancelled",
            user_id=str(user_id),
            user_plan_id=str(user_plan.id),
            immediate=immediate,
        )

        return True

    async def expire_user_plan(
        self,
        user_plan_id: UUID,
    ) -> bool:
        """
        Immediately expire a specific user plan.

        Args:
            user_plan_id: UserPlan UUID to expire

        Returns:
            True if plan was expired, False if not found
        """
        yesterday = date.today() - timedelta(days=1)
        stmt = (
            update(UserPlanModel)
            .where(UserPlanModel.id == user_plan_id)
            .values(ends_at=yesterday)
            .returning(UserPlanModel.id)
        )
        result = await self._session.execute(stmt)
        expired_id = result.scalar_one_or_none()

        if expired_id is None:
            return False

        await self._session.flush()

        logger.info(
            "user_plan_expired",
            user_plan_id=str(user_plan_id),
        )

        return True

    async def delete_user_plan(
        self,
        user_plan_id: UUID,
    ) -> bool:
        """
        Hard delete a user plan record.

        Note: This also deletes associated usage records (CASCADE).
        Use with caution - prefer expire_user_plan for soft delete.

        Args:
            user_plan_id: UserPlan UUID to delete

        Returns:
            True if deleted, False if not found
        """
        stmt = (
            delete(UserPlanModel)
            .where(UserPlanModel.id == user_plan_id)
            .returning(UserPlanModel.id)
        )
        result = await self._session.execute(stmt)
        deleted_id = result.scalar_one_or_none()

        if deleted_id is None:
            return False

        await self._session.flush()

        logger.warning(
            "user_plan_deleted",
            user_plan_id=str(user_plan_id),
        )

        return True
