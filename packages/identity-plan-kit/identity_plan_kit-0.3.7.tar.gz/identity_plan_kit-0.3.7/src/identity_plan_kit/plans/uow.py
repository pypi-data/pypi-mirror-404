"""Plans module Unit of Work."""

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from identity_plan_kit.plans.repositories.plan_repo import PlanRepository
from identity_plan_kit.plans.repositories.usage_repo import UsageRepository
from identity_plan_kit.shared.uow import BaseUnitOfWork


class PlansUnitOfWork(BaseUnitOfWork):
    """
    Unit of Work for plan and usage operations.

    Provides access to plan and usage repositories within a transaction.

    Usage with internal session:
        ```python
        async with PlansUnitOfWork(session_factory) as uow:
            user_plan = await uow.plans.get_user_active_plan(user_id)
            await uow.usage.record_usage(user_plan.id, feature_id, amount)
            # Commits automatically on successful exit
        ```

    Usage with external session:
        ```python
        async with PlansUnitOfWork(session_factory, session=your_session) as uow:
            user_plan = await uow.plans.get_user_active_plan(user_id)
            # You control commit/rollback
        ```
    """

    plans: PlanRepository
    usage: UsageRepository

    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        session: AsyncSession | None = None,
    ) -> None:
        super().__init__(session_factory, session=session)
        self.plans: PlanRepository
        self.usage: UsageRepository

    def _init_repositories(self) -> None:
        """Initialize plan repositories."""
        self.plans = PlanRepository(self.session)
        self.usage = UsageRepository(self.session)
