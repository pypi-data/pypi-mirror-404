"""Base Unit of Work pattern implementation."""

from __future__ import annotations

from abc import ABC, abstractmethod
from types import TracebackType
from typing import TYPE_CHECKING

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from identity_plan_kit.shared.logging import get_logger

if TYPE_CHECKING:
    from identity_plan_kit.shared.registry import ExtensionConfig

logger = get_logger(__name__)


class AbstractUnitOfWork(ABC):
    """
    Abstract base class for Unit of Work pattern.

    Provides transaction management and repository access.
    All writes should occur within a UoW context to ensure atomicity.

    Usage:
        async with uow_factory() as uow:
            user = await uow.users.get_by_id(user_id)
            user.deactivate()
            await uow.users.update(user)
            # Commit happens automatically on successful exit
    """

    @abstractmethod
    async def __aenter__(self) -> "AbstractUnitOfWork":
        """Enter the async context and start a transaction."""
        raise NotImplementedError

    @abstractmethod
    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Exit the async context, commit or rollback."""
        raise NotImplementedError

    @abstractmethod
    async def commit(self) -> None:
        """Commit the current transaction."""
        raise NotImplementedError

    @abstractmethod
    async def rollback(self) -> None:
        """Rollback the current transaction."""
        raise NotImplementedError


class BaseUnitOfWork(AbstractUnitOfWork):
    """
    Base implementation of Unit of Work with SQLAlchemy.

    Subclasses should add repository properties for their domain.

    Supports two modes:
    1. Internal session: Creates and manages its own session from the factory
    2. External session: Uses a provided session (for transaction participation)

    When using external session mode, commit/rollback are NO-OPs since the
    external caller controls the transaction lifecycle.

    Supports extension configuration for custom model/entity classes.
    """

    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        session: AsyncSession | None = None,
        extension_config: ExtensionConfig | None = None,
    ) -> None:
        """
        Initialize Unit of Work.

        Args:
            session_factory: SQLAlchemy async session factory
            session: Optional external session for transaction participation.
                If provided, UoW will use this session instead of creating a new one.
                The external caller is responsible for commit/rollback/close.
            extension_config: Optional extension configuration for custom model/entity classes.
                If not provided, uses default classes from the library.
        """
        self._session_factory = session_factory
        self._session: AsyncSession | None = session
        self._owns_session = session is None  # True if we created the session
        self._extension_config = extension_config

    @property
    def session(self) -> AsyncSession:
        """Get the current session."""
        if self._session is None:
            raise RuntimeError("UnitOfWork not started. Use 'async with' context.")
        return self._session

    @property
    def extension_config(self) -> ExtensionConfig | None:
        """Get the extension configuration."""
        return self._extension_config

    def _get_model_registry(self):
        """Get the model registry from extension config or create default."""
        if self._extension_config:
            return self._extension_config.models
        # Import here to avoid circular imports
        from identity_plan_kit.shared.registry import ModelRegistry

        return ModelRegistry()

    def _get_entity_registry(self):
        """Get the entity registry from extension config or create default."""
        if self._extension_config:
            return self._extension_config.entities
        # Import here to avoid circular imports
        from identity_plan_kit.shared.registry import EntityRegistry

        return EntityRegistry()

    async def __aenter__(self) -> "BaseUnitOfWork":
        """Start a new session/transaction or use external session."""
        if self._session is None:
            self._session = self._session_factory()
            self._owns_session = True
        self._init_repositories()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Commit on success, rollback on exception (only if we own the session)."""
        if self._owns_session and self._session is not None:
            if exc_type is not None:
                await self.rollback()
                logger.debug("uow_rollback", exception=str(exc_val))
            else:
                await self.commit()
                logger.debug("uow_commit")

            await self._session.close()
            self._session = None
        else:
            # External session - don't commit/rollback/close
            # Just log that we're exiting
            logger.debug(
                "uow_exit_external_session",
                had_exception=exc_type is not None,
            )

    async def commit(self) -> None:
        """Commit the current transaction (no-op for external session)."""
        if self._owns_session:
            await self.session.commit()

    async def rollback(self) -> None:
        """Rollback the current transaction (no-op for external session)."""
        if self._owns_session:
            await self.session.rollback()

    def _init_repositories(self) -> None:
        """
        Initialize repositories with the current session.

        Override in subclasses to set up domain-specific repositories.
        Uses extension config registries if available to support custom models/entities.
        """
        pass
