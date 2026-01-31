"""Refresh token repository."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING, Generic, TypeVar
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from identity_plan_kit.auth.domain.entities import RefreshToken
from identity_plan_kit.auth.models.refresh_token import RefreshTokenModel
from identity_plan_kit.shared.logging import get_logger

if TYPE_CHECKING:
    from identity_plan_kit.shared.registry import EntityRegistry, ModelRegistry

logger = get_logger(__name__)

# Type variables for generic repository
M = TypeVar("M", bound=RefreshTokenModel)  # Model type
E = TypeVar("E", bound=RefreshToken)  # Entity type


class RefreshTokenRepository(Generic[M, E]):
    """
    Repository for refresh token data access.

    Supports generic model and entity types for extensibility.

    Type Parameters:
        M: The token model type (default: RefreshTokenModel)
        E: The token entity type (default: RefreshToken)
    """

    # Default classes - can be overridden via constructor
    _model_class: type[M] = RefreshTokenModel  # type: ignore[assignment]
    _entity_class: type[E] = RefreshToken  # type: ignore[assignment]

    def __init__(
        self,
        session: AsyncSession,
        model_class: type[M] | None = None,
        entity_class: type[E] | None = None,
    ) -> None:
        """
        Initialize the token repository.

        Args:
            session: SQLAlchemy async session
            model_class: Optional custom token model class
            entity_class: Optional custom token entity class
        """
        self._session = session

        if model_class is not None:
            self._model_class = model_class
        if entity_class is not None:
            self._entity_class = entity_class

    @classmethod
    def from_registry(
        cls,
        session: AsyncSession,
        models: ModelRegistry,
        entities: EntityRegistry,
    ) -> RefreshTokenRepository:
        """
        Create repository from registries.

        Args:
            session: SQLAlchemy async session
            models: Model registry with model classes
            entities: Entity registry with entity classes

        Returns:
            Configured RefreshTokenRepository instance
        """
        return cls(
            session=session,
            model_class=models.get_refresh_token_model(),
            entity_class=entities.get_refresh_token_entity(),
        )

    async def create(
        self,
        user_id: UUID,
        token_hash: str,
        expires_at: datetime,
        user_agent: str | None = None,
        ip_address: str | None = None,
        **extra_fields,
    ) -> E:
        """
        Create a new refresh token.

        Args:
            user_id: User UUID
            token_hash: Hashed token for storage
            expires_at: Token expiration time
            user_agent: Client user agent
            ip_address: Client IP address
            **extra_fields: Additional fields for extended models

        Returns:
            Created refresh token entity
        """
        model = self._model_class(
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at,
            user_agent=user_agent,
            ip_address=ip_address,
            **extra_fields,
        )
        self._session.add(model)
        await self._session.flush()

        logger.debug(
            "refresh_token_created",
            user_id=str(user_id),
            token_id=str(model.id),
        )

        return self._to_entity(model)

    async def get_by_hash(
        self,
        token_hash: str,
        for_update: bool = False,
    ) -> E | None:
        """
        Get refresh token by its hash.

        Args:
            token_hash: Hashed token
            for_update: If True, lock the row for update (prevents race conditions)

        Returns:
            Refresh token entity or None
        """
        stmt = select(self._model_class).where(
            self._model_class.token_hash == token_hash,
            self._model_class.revoked_at.is_(None),
        )

        # Apply row-level lock if requested (P1 race condition fix)
        if for_update:
            stmt = stmt.with_for_update()

        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()

        if model is None:
            return None

        return self._to_entity(model)

    async def revoke(self, token_id: UUID) -> None:
        """
        Revoke a refresh token.

        Args:
            token_id: Token UUID to revoke
        """
        stmt = (
            update(self._model_class)
            .where(self._model_class.id == token_id)
            .values(revoked_at=datetime.now(UTC))
        )
        await self._session.execute(stmt)
        await self._session.flush()

        logger.info("refresh_token_revoked", token_id=str(token_id))

    async def revoke_all_for_user(self, user_id: UUID) -> int:
        """
        Revoke all refresh tokens for a user.

        Used when user changes password or logs out everywhere.

        Args:
            user_id: User UUID

        Returns:
            Number of tokens revoked
        """
        stmt = (
            update(self._model_class)
            .where(
                self._model_class.user_id == user_id,
                self._model_class.revoked_at.is_(None),
            )
            .values(revoked_at=datetime.now(UTC))
        )
        result = await self._session.execute(stmt)
        await self._session.flush()

        count = result.rowcount
        logger.info(
            "refresh_tokens_revoked_all",
            user_id=str(user_id),
            count=count,
        )

        return count

    async def cleanup_expired(self, batch_size: int = 1000) -> int:
        """
        Delete expired and revoked tokens in batches.

        Uses batch deletion to prevent long-running transactions and
        table-level locks on large datasets.

        Uses FOR UPDATE SKIP LOCKED to allow concurrent cleanup operations
        to process different batches of tokens without conflicts.

        Should be run periodically via background job.

        Args:
            batch_size: Maximum number of tokens to delete per call

        Returns:
            Number of tokens deleted in this batch
        """
        # Import here - delete is only needed for cleanup operations
        from sqlalchemy import delete  # noqa: PLC0415

        # Select IDs to delete with SKIP LOCKED to allow concurrent cleanup
        # Each concurrent call will get a different batch of rows
        select_stmt = (
            select(self._model_class.id)
            .where(
                (self._model_class.expires_at < datetime.now(UTC))
                | (self._model_class.revoked_at.is_not(None))
            )
            .limit(batch_size)
            .with_for_update(skip_locked=True)
        )
        result = await self._session.execute(select_stmt)
        ids_to_delete = [row[0] for row in result.fetchall()]

        if not ids_to_delete:
            return 0

        # Delete by IDs and get actual count
        delete_stmt = delete(self._model_class).where(self._model_class.id.in_(ids_to_delete))
        delete_result = await self._session.execute(delete_stmt)
        await self._session.flush()

        # Use rowcount from DELETE to get actual deleted count
        count = delete_result.rowcount
        logger.info(
            "refresh_tokens_cleaned",
            count=count,
            batch_size=batch_size,
            has_more=count == batch_size,
        )

        return count

    def _to_entity(self, model: M) -> E:
        """
        Convert ORM model to domain entity.

        Args:
            model: The token model instance

        Returns:
            Token entity instance
        """
        import dataclasses

        # Build base entity fields
        entity_kwargs = {
            "id": model.id,
            "user_id": model.user_id,
            "token_hash": model.token_hash,
            "expires_at": model.expires_at,
            "created_at": model.created_at,
            "revoked_at": model.revoked_at,
            "user_agent": model.user_agent,
            "ip_address": model.ip_address,
        }

        # Add extended fields if entity supports them
        if dataclasses.is_dataclass(self._entity_class):
            base_fields = {
                "id", "user_id", "token_hash", "expires_at",
                "created_at", "revoked_at", "user_agent", "ip_address",
            }
            entity_fields = {f.name for f in dataclasses.fields(self._entity_class)}
            extended_fields = entity_fields - base_fields

            for field_name in extended_fields:
                if hasattr(model, field_name):
                    entity_kwargs[field_name] = getattr(model, field_name)

        return self._entity_class(**entity_kwargs)
