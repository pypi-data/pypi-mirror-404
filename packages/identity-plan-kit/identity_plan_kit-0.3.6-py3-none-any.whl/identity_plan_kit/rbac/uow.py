"""RBAC module Unit of Work."""

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from identity_plan_kit.rbac.repositories.rbac_repo import RBACRepository
from identity_plan_kit.shared.uow import BaseUnitOfWork


class RBACUnitOfWork(BaseUnitOfWork):
    """
    Unit of Work for RBAC operations.

    Provides access to RBAC repository within a transaction.

    Usage with internal session:
        ```python
        async with RBACUnitOfWork(session_factory) as uow:
            role = await uow.rbac.get_role_by_id(role_id)
            permissions = await uow.rbac.get_role_permissions(role_id)
            # Commits automatically on successful exit
        ```

    Usage with external session:
        ```python
        async with RBACUnitOfWork(session_factory, session=your_session) as uow:
            role = await uow.rbac.get_role_by_id(role_id)
            # You control commit/rollback
        ```
    """

    rbac: RBACRepository

    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        session: AsyncSession | None = None,
    ) -> None:
        super().__init__(session_factory, session=session)
        self.rbac: RBACRepository

    def _init_repositories(self) -> None:
        """Initialize RBAC repositories."""
        self.rbac = RBACRepository(self.session)
