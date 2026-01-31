"""User repository for data access."""

from __future__ import annotations

from typing import TYPE_CHECKING, Generic, TypeVar
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from identity_plan_kit.auth.domain.entities import User
from identity_plan_kit.auth.models.user import UserModel
from identity_plan_kit.auth.models.user_provider import UserProviderModel
from identity_plan_kit.shared.audit import mask_email
from identity_plan_kit.shared.logging import get_logger

if TYPE_CHECKING:
    from identity_plan_kit.shared.registry import ModelRegistry, EntityRegistry

logger = get_logger(__name__)

# Type variables for generic repository
M = TypeVar("M", bound=UserModel)  # Model type
E = TypeVar("E", bound=User)  # Entity type


class UserRepository(Generic[M, E]):
    """
    Repository for user data access.

    Supports generic model and entity types for extensibility.
    By default uses UserModel and User, but can be configured
    to use extended versions.

    Type Parameters:
        M: The user model type (default: UserModel)
        E: The user entity type (default: User)

    Example with custom model:
        repo = UserRepository(
            session,
            model_class=ExtendedUserModel,
            entity_class=ExtendedUser,
        )
    """

    # Default classes - can be overridden via constructor
    _model_class: type[M] = UserModel  # type: ignore[assignment]
    _entity_class: type[E] = User  # type: ignore[assignment]
    _provider_model_class: type = UserProviderModel

    def __init__(
        self,
        session: AsyncSession,
        model_class: type[M] | None = None,
        entity_class: type[E] | None = None,
        provider_model_class: type | None = None,
    ) -> None:
        """
        Initialize the user repository.

        Args:
            session: SQLAlchemy async session
            model_class: Optional custom user model class
            entity_class: Optional custom user entity class
            provider_model_class: Optional custom provider model class
        """
        self._session = session

        # Use provided classes or fall back to defaults
        if model_class is not None:
            self._model_class = model_class
        if entity_class is not None:
            self._entity_class = entity_class
        if provider_model_class is not None:
            self._provider_model_class = provider_model_class

    @classmethod
    def from_registry(
        cls,
        session: AsyncSession,
        models: ModelRegistry,
        entities: EntityRegistry,
    ) -> UserRepository:
        """
        Create repository from registries.

        Args:
            session: SQLAlchemy async session
            models: Model registry with model classes
            entities: Entity registry with entity classes

        Returns:
            Configured UserRepository instance
        """
        return cls(
            session=session,
            model_class=models.get_user_model(),
            entity_class=entities.get_user_entity(),
            provider_model_class=models.get_user_provider_model(),
        )

    async def get_by_id(
        self,
        user_id: UUID,
        for_update: bool = False,
        include_role: bool = True,
    ) -> E | None:
        """
        Get user by ID.

        Args:
            user_id: User UUID
            for_update: If True, lock the row for update (prevents race conditions
                in operations that depend on current user state like is_active)
            include_role: If True, eagerly load the user's role (default: True).
                Set to False to skip the role query when role info is not needed.

        Returns:
            User entity or None if not found
        """
        stmt = select(self._model_class).where(self._model_class.id == user_id)

        if include_role:
            stmt = stmt.options(selectinload(self._model_class.role))

        if for_update:
            stmt = stmt.with_for_update()

        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()

        if model is None:
            return None

        return self._to_entity(model)

    async def get_by_email(
        self,
        email: str,
        for_update: bool = False,
        include_role: bool = True,
    ) -> E | None:
        """
        Get user by email address.

        Args:
            email: User email
            for_update: If True, lock the row for update
            include_role: If True, eagerly load the user's role (default: True).
                Set to False to skip the role query when role info is not needed.

        Returns:
            User entity or None if not found
        """
        stmt = select(self._model_class).where(self._model_class.email == email)

        if include_role:
            stmt = stmt.options(selectinload(self._model_class.role))

        if for_update:
            stmt = stmt.with_for_update()

        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()

        if model is None:
            return None

        return self._to_entity(model)

    async def get_by_provider(
        self,
        provider_code: str,
        external_user_id: str,
    ) -> E | None:
        """
        Get user by OAuth provider.

        Args:
            provider_code: Provider code (e.g., "google")
            external_user_id: User ID from the provider

        Returns:
            User entity or None if not found
        """
        stmt = (
            select(self._model_class)
            .join(self._provider_model_class)
            .options(selectinload(self._model_class.role))
            .where(
                self._provider_model_class.code == provider_code,
                self._provider_model_class.external_user_id == external_user_id,
            )
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()

        if model is None:
            return None

        return self._to_entity(model)

    async def create(
        self,
        email: str,
        role_id: UUID,
        display_name: str | None = None,
        picture_url: str | None = None,
        is_verified: bool = False,
        **extra_fields,
    ) -> E:
        """
        Create a new user.

        Args:
            email: User email
            role_id: Role UUID to assign
            display_name: Display name (defaults to email prefix if not provided)
            picture_url: Profile picture URL (optional)
            is_verified: Whether email is verified
            **extra_fields: Additional fields for extended models

        Returns:
            Created user entity
        """
        # Default display_name to email prefix if not provided
        if display_name is None:
            display_name = email.split("@")[0]

        model = self._model_class(
            email=email,
            role_id=role_id,
            display_name=display_name,
            picture_url=picture_url,
            is_verified=is_verified,
            **extra_fields,
        )
        self._session.add(model)
        await self._session.flush()

        # Reload with relationships
        await self._session.refresh(model, ["role"])

        return self._to_entity(model)

    async def create_with_provider(
        self,
        email: str,
        role_id: UUID,
        provider_code: str,
        external_user_id: str,
        display_name: str | None = None,
        picture_url: str | None = None,
        is_verified: bool = True,
        **extra_fields,
    ) -> E:
        """
        Create a new user with OAuth provider link.

        Handles race conditions by catching unique constraint violations.

        Args:
            email: User email
            role_id: Role UUID to assign
            provider_code: OAuth provider code
            external_user_id: Provider's user ID
            display_name: Display name (defaults to email prefix if not provided)
            picture_url: Profile picture URL (optional)
            is_verified: Whether email is verified
            **extra_fields: Additional fields for extended models

        Returns:
            Created user entity

        Raises:
            IntegrityError: If user with email already exists (race condition)
        """
        # Default display_name to email prefix if not provided
        if display_name is None:
            display_name = email.split("@")[0]

        # Create user (IntegrityError raised if email already exists - race condition)
        user_model = self._model_class(
            email=email,
            role_id=role_id,
            display_name=display_name,
            picture_url=picture_url,
            is_verified=is_verified,
            **extra_fields,
        )
        self._session.add(user_model)
        await self._session.flush()

        # Create provider link
        provider_model = self._provider_model_class(
            user_id=user_model.id,
            code=provider_code,
            external_user_id=external_user_id,
        )
        self._session.add(provider_model)
        await self._session.flush()

        # Reload with relationships
        await self._session.refresh(user_model, ["role", "providers"])

        return self._to_entity(user_model)

    async def get_or_create_with_provider(
        self,
        email: str,
        role_id: UUID,
        provider_code: str,
        external_user_id: str,
        display_name: str | None = None,
        picture_url: str | None = None,
        is_verified: bool = True,
        **extra_fields,
    ) -> tuple[E, bool]:
        """
        Get existing user or create new one with provider (race-condition safe).

        Uses database-level locking and savepoints to prevent duplicate user creation
        while maintaining transaction integrity.

        Args:
            email: User email
            role_id: Role UUID for new users
            provider_code: OAuth provider code
            external_user_id: Provider's user ID
            display_name: Display name for new users (defaults to email prefix)
            picture_url: Profile picture URL for new users (optional)
            is_verified: Whether email is verified
            **extra_fields: Additional fields for extended models

        Returns:
            Tuple of (user, created) where created is True if user was created
        """
        # First, try to get existing user by provider
        user = await self.get_by_provider(provider_code, external_user_id)
        if user:
            return user, False

        # Try to get by email with lock
        user = await self.get_by_email(email, for_update=True)
        if user:
            # User exists, link provider (don't overwrite their profile data)
            await self.add_provider(user.id, provider_code, external_user_id)
            return user, False

        # No existing user, create new one using savepoint for safe rollback
        try:
            # Use nested transaction (savepoint) so we can rollback without
            # corrupting the outer transaction managed by UoW
            async with self._session.begin_nested():
                user = await self.create_with_provider(
                    email=email,
                    role_id=role_id,
                    provider_code=provider_code,
                    external_user_id=external_user_id,
                    display_name=display_name,
                    picture_url=picture_url,
                    is_verified=is_verified,
                    **extra_fields,
                )
                return user, True
        except IntegrityError as e:
            # Race condition - another request created the user
            # Savepoint was automatically rolled back, session is still valid
            logger.warning(
                "user_create_race_condition_handled",
                email=mask_email(email),
                provider=provider_code,
            )
            # Fetch the existing user (created by concurrent request)
            user = await self.get_by_email(email)
            if user:
                # Link provider if not already linked
                # P1 FIX: Use try/except to handle race condition where another
                # request links the same provider between our check and add
                existing_provider = await self.get_by_provider(provider_code, external_user_id)
                if not existing_provider:
                    try:
                        await self.add_provider(user.id, provider_code, external_user_id)
                    except IntegrityError:
                        # Another request linked the provider - that's fine
                        logger.debug(
                            "provider_link_race_condition_handled",
                            email=mask_email(email),
                            provider=provider_code,
                        )
                return user, False
            # This should not happen - raise to surface the issue
            raise RuntimeError(f"User creation race condition but user not found: {email}") from e

    async def add_provider(
        self,
        user_id: UUID,
        provider_code: str,
        external_user_id: str,
    ) -> None:
        """
        Add OAuth provider to existing user.

        Args:
            user_id: User UUID
            provider_code: OAuth provider code
            external_user_id: Provider's user ID
        """
        provider_model = self._provider_model_class(
            user_id=user_id,
            code=provider_code,
            external_user_id=external_user_id,
        )
        self._session.add(provider_model)
        await self._session.flush()

    async def update(self, user: E) -> E:
        """
        Update user data.

        Uses SELECT FOR UPDATE to prevent lost update race conditions.

        Args:
            user: User entity with updated data

        Returns:
            Updated user entity
        """
        # P1 fix: Use SELECT FOR UPDATE to prevent lost updates
        stmt = select(self._model_class).where(self._model_class.id == user.id).with_for_update()
        result = await self._session.execute(stmt)
        model = result.scalar_one()

        model.email = user.email
        model.role_id = user.role_id
        model.display_name = user.display_name
        model.picture_url = user.picture_url
        model.is_active = user.is_active
        model.is_verified = user.is_verified

        # Copy any extended fields from entity to model
        self._copy_extended_fields(user, model)

        await self._session.flush()
        await self._session.refresh(model, ["role"])

        return self._to_entity(model)

    async def deactivate(
        self,
        user_id: UUID,
        reason: str | None = None,
    ) -> bool:
        """
        Deactivate a user account.

        P1 SECURITY FIX: Used when token theft is detected to secure the account.
        User must contact support to reactivate.

        Args:
            user_id: User UUID to deactivate
            reason: Reason for deactivation (for logging)

        Returns:
            True if user was deactivated, False if already inactive or not found
        """
        # Import here - update is only needed for bulk operations
        from sqlalchemy import update  # noqa: PLC0415

        stmt = (
            update(self._model_class)
            .where(
                self._model_class.id == user_id,
                self._model_class.is_active == True,  # noqa: E712
            )
            .values(is_active=False)
        )
        result = await self._session.execute(stmt)
        await self._session.flush()

        deactivated = result.rowcount > 0

        if deactivated:
            logger.warning(
                "user_deactivated",
                user_id=str(user_id),
                reason=reason,
            )

        return deactivated

    async def reactivate(
        self,
        user_id: UUID,
        reason: str | None = None,
    ) -> bool:
        """
        Reactivate a user account.

        Args:
            user_id: User UUID to reactivate
            reason: Reason for reactivation (for logging)

        Returns:
            True if user was reactivated, False if already active or not found
        """
        # Import here - update is only needed for bulk operations
        from sqlalchemy import update  # noqa: PLC0415

        stmt = (
            update(self._model_class)
            .where(
                self._model_class.id == user_id,
                self._model_class.is_active == False,  # noqa: E712
            )
            .values(is_active=True)
        )
        result = await self._session.execute(stmt)
        await self._session.flush()

        reactivated = result.rowcount > 0

        if reactivated:
            logger.info(
                "user_reactivated",
                user_id=str(user_id),
                reason=reason,
            )

        return reactivated

    async def update_profile(
        self,
        user_id: UUID,
        display_name: str | None = None,
        picture_url: str | None = ...,  # Use ... as sentinel to distinguish None from "not provided"
        **extra_fields,
    ) -> E | None:
        """
        Update user profile fields (display_name, picture_url).

        Only updates fields that are explicitly provided.
        Uses SELECT FOR UPDATE to prevent race conditions.

        Args:
            user_id: User UUID
            display_name: New display name (if provided)
            picture_url: New picture URL (if provided, use None to clear)
            **extra_fields: Additional fields for extended models

        Returns:
            Updated user entity, or None if user not found
        """
        stmt = select(self._model_class).where(self._model_class.id == user_id).with_for_update()
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()

        if model is None:
            return None

        # Only update fields that were explicitly provided
        if display_name is not None:
            model.display_name = display_name

        if picture_url is not ...:  # Explicitly provided (including None to clear)
            model.picture_url = picture_url

        # Update any extended fields
        for field_name, value in extra_fields.items():
            if hasattr(model, field_name):
                setattr(model, field_name, value)

        await self._session.flush()
        await self._session.refresh(model, ["role"])

        logger.info(
            "user_profile_updated",
            user_id=str(user_id),
        )

        return self._to_entity(model)

    async def set_password_hash(
        self,
        user_id: UUID,
        password_hash: str,
    ) -> bool:
        """
        Set password hash for a user (race-condition safe).

        Uses SELECT FOR UPDATE to prevent lost updates when multiple
        requests try to set password simultaneously.

        SECURITY NOTES:
        - password_hash must be pre-hashed using bcrypt (via shared.security.hash_password)
        - Never log or store plain passwords
        - This method only accepts already-hashed passwords

        Args:
            user_id: User UUID
            password_hash: Pre-hashed password (bcrypt hash, ~60 chars)

        Returns:
            True if password was set, False if user not found
        """
        # Use SELECT FOR UPDATE to prevent race conditions
        stmt = select(self._model_class).where(self._model_class.id == user_id).with_for_update()
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()

        if model is None:
            return False

        model.password_hash = password_hash
        await self._session.flush()

        # Log without exposing any password data
        logger.info(
            "user_password_hash_set",
            user_id=str(user_id),
        )

        return True

    async def clear_password_hash(
        self,
        user_id: UUID,
    ) -> bool:
        """
        Remove password hash from user (e.g., when switching to OAuth-only).

        Args:
            user_id: User UUID

        Returns:
            True if password was cleared, False if user not found
        """
        stmt = select(self._model_class).where(self._model_class.id == user_id).with_for_update()
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()

        if model is None:
            return False

        model.password_hash = None
        await self._session.flush()

        logger.info(
            "user_password_hash_cleared",
            user_id=str(user_id),
        )

        return True

    def _to_entity(self, model: M) -> E:
        """
        Convert ORM model to domain entity.

        Override in subclasses to handle extended fields.

        Args:
            model: The user model instance

        Returns:
            User entity instance
        """
        # Build base entity fields
        entity_kwargs = {
            "id": model.id,
            "email": model.email,
            "role_id": model.role_id,
            "display_name": model.display_name,
            "picture_url": model.picture_url,
            "is_active": model.is_active,
            "is_verified": model.is_verified,
            "created_at": model.created_at,
            "updated_at": model.updated_at,
            "role_code": model.role.code if model.role else None,
        }

        # Add extended fields if entity supports them
        self._add_extended_entity_fields(model, entity_kwargs)

        return self._entity_class(**entity_kwargs)

    def _add_extended_entity_fields(self, model: M, entity_kwargs: dict) -> None:
        """
        Add extended fields from model to entity kwargs.

        This method checks for additional fields that exist on both the
        model and entity classes beyond the base User fields.

        Args:
            model: The model instance
            entity_kwargs: Dictionary to add fields to
        """
        import dataclasses

        # Get base User field names
        base_fields = {
            "id", "email", "role_id", "display_name", "picture_url",
            "is_active", "is_verified", "created_at", "updated_at",
            "role_code", "permissions",
        }

        # Check if entity is a dataclass
        if not dataclasses.is_dataclass(self._entity_class):
            return

        # Get entity's additional fields
        entity_fields = {f.name for f in dataclasses.fields(self._entity_class)}
        extended_fields = entity_fields - base_fields

        # Copy matching extended fields from model
        for field_name in extended_fields:
            if hasattr(model, field_name):
                entity_kwargs[field_name] = getattr(model, field_name)

    def _copy_extended_fields(self, entity: E, model: M) -> None:
        """
        Copy extended fields from entity to model.

        Used during update operations to preserve custom fields.

        Args:
            entity: The entity with potentially extended fields
            model: The model to update
        """
        import dataclasses

        # Get base User field names (already handled explicitly)
        base_fields = {
            "id", "email", "role_id", "display_name", "picture_url",
            "is_active", "is_verified", "created_at", "updated_at",
            "role_code", "permissions",
        }

        # Check if entity is a dataclass
        if not dataclasses.is_dataclass(entity):
            return

        # Get entity's additional fields
        entity_fields = {f.name for f in dataclasses.fields(entity)}
        extended_fields = entity_fields - base_fields

        # Copy matching extended fields to model
        for field_name in extended_fields:
            if hasattr(model, field_name) and hasattr(entity, field_name):
                setattr(model, field_name, getattr(entity, field_name))
