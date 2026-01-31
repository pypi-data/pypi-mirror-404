"""Auth module Unit of Work."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from identity_plan_kit.auth.repositories.token_repo import RefreshTokenRepository
from identity_plan_kit.auth.repositories.user_repo import UserRepository
from identity_plan_kit.plans.repositories.plan_repo import PlanRepository
from identity_plan_kit.rbac.repositories.rbac_repo import RBACRepository
from identity_plan_kit.shared.uow import BaseUnitOfWork

if TYPE_CHECKING:
    from identity_plan_kit.shared.registry import ExtensionConfig


class AuthUnitOfWork(BaseUnitOfWork):
    """
    Unit of Work for authentication operations.

    Provides access to user, token, plan, and RBAC repositories within a transaction.
    The plan and RBAC repositories are included to support atomic user registration
    with default plan/role assignment.

    Supports custom model/entity classes via extension configuration.

    Usage with internal session (IPK manages transaction):
        ```python
        async with AuthUnitOfWork(session_factory) as uow:
            user = await uow.users.get_by_email(email)
            await uow.tokens.create(user.id, token_hash, expires_at)
            # Commits automatically on successful exit
        ```

    Usage with external session (your app manages transaction):
        ```python
        async with your_session.begin():
            async with AuthUnitOfWork(session_factory, session=your_session) as uow:
                user = await uow.users.get_by_email(email)
                # Your other operations in same transaction
            # You control commit/rollback
        ```

    Usage with custom models (extension configuration):
        ```python
        extension_config = ExtensionConfig(
            models=ModelRegistry(user_model=ExtendedUserModel),
            entities=EntityRegistry(user_entity=ExtendedUser),
        )
        async with AuthUnitOfWork(session_factory, extension_config=extension_config) as uow:
            user = await uow.users.get_by_email(email)  # Returns ExtendedUser
        ```
    """

    users: UserRepository
    tokens: RefreshTokenRepository
    plans: PlanRepository
    rbac: RBACRepository

    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        session: AsyncSession | None = None,
        extension_config: ExtensionConfig | None = None,
    ) -> None:
        """
        Initialize Auth Unit of Work.

        Args:
            session_factory: SQLAlchemy async session factory
            session: Optional external session for transaction participation
            extension_config: Optional extension config for custom model/entity classes
        """
        super().__init__(session_factory, session=session, extension_config=extension_config)
        # Type annotations for repositories (initialized in _init_repositories)
        self.users: UserRepository
        self.tokens: RefreshTokenRepository
        self.plans: PlanRepository
        self.rbac: RBACRepository

    def _init_repositories(self) -> None:
        """
        Initialize auth repositories with extension config support.

        If extension_config is provided, repositories will use custom model/entity classes.
        Otherwise, they use the default classes from the library.
        """
        models = self._get_model_registry()
        entities = self._get_entity_registry()

        # Initialize repositories with registries for custom model/entity support
        self.users = UserRepository(
            self.session,
            model_class=models.get_user_model(),
            entity_class=entities.get_user_entity(),
            provider_model_class=models.get_user_provider_model(),
        )
        self.tokens = RefreshTokenRepository(
            self.session,
            model_class=models.get_refresh_token_model(),
            entity_class=entities.get_refresh_token_entity(),
        )
        # PlanRepository and RBACRepository will use their defaults for now
        # They will be updated to support extension config in subsequent changes
        self.plans = PlanRepository(self.session)
        self.rbac = RBACRepository(self.session)
