"""Tests for model/entity extension functionality."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID

import pytest
from sqlalchemy import ForeignKey, String
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column

from identity_plan_kit.auth.domain.entities import User
from identity_plan_kit.auth.models.user import UserModel
from identity_plan_kit.auth.repositories.user_repo import UserRepository
from identity_plan_kit.auth.uow import AuthUnitOfWork
from identity_plan_kit.shared.registry import (
    DTORegistry,
    EntityRegistry,
    ExtensionConfig,
    ModelRegistry,
)


# =============================================================================
# Extended Model Definition
# =============================================================================


class ExtendedUserModel(UserModel):
    """
    Extended user model with custom organization field.

    Demonstrates how users can extend the base UserModel with additional columns.
    """

    # Custom fields
    organization_id: Mapped[UUID | None] = mapped_column(
        # ForeignKey would go here if organizations table exists
        nullable=True,
        default=None,
    )
    department: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        default=None,
    )
    employee_id: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        default=None,
    )


# =============================================================================
# Extended Entity Definition
# =============================================================================


@dataclass
class ExtendedUser(User):
    """
    Extended user entity with custom organization fields.

    Demonstrates how users can extend the base User entity with additional fields.
    """

    # Custom fields (defaults must be provided for dataclass inheritance)
    organization_id: UUID | None = None
    department: str | None = None
    employee_id: str | None = None


# =============================================================================
# Tests
# =============================================================================


class TestRegistryCreation:
    """Test registry creation and configuration."""

    def test_create_default_model_registry(self):
        """Default registry should use built-in model classes."""
        registry = ModelRegistry()

        # Should return default classes
        assert registry.get_user_model() == UserModel

    def test_create_custom_model_registry(self):
        """Custom registry should use provided model classes."""
        registry = ModelRegistry(user_model=ExtendedUserModel)

        # Should return custom class
        assert registry.get_user_model() == ExtendedUserModel

    def test_create_default_entity_registry(self):
        """Default registry should use built-in entity classes."""
        registry = EntityRegistry()

        # Should return default classes
        assert registry.get_user_entity() == User

    def test_create_custom_entity_registry(self):
        """Custom registry should use provided entity classes."""
        registry = EntityRegistry(user_entity=ExtendedUser)

        # Should return custom class
        assert registry.get_user_entity() == ExtendedUser

    def test_create_extension_config(self):
        """Extension config should combine all registries."""
        models = ModelRegistry(user_model=ExtendedUserModel)
        entities = EntityRegistry(user_entity=ExtendedUser)
        dtos = DTORegistry()

        config = ExtensionConfig(
            models=models,
            entities=entities,
            dtos=dtos,
        )

        assert config.models.get_user_model() == ExtendedUserModel
        assert config.entities.get_user_entity() == ExtendedUser


class TestUserRepositoryGenericTypes:
    """Test UserRepository with generic type support."""

    def test_repository_default_classes(self, async_session: AsyncSession):
        """Repository should use default classes when not configured."""
        repo = UserRepository(async_session)

        assert repo._model_class == UserModel
        assert repo._entity_class == User

    def test_repository_custom_classes(self, async_session: AsyncSession):
        """Repository should use custom classes when configured."""
        repo = UserRepository(
            async_session,
            model_class=ExtendedUserModel,
            entity_class=ExtendedUser,
        )

        assert repo._model_class == ExtendedUserModel
        assert repo._entity_class == ExtendedUser

    def test_repository_from_registry(self, async_session: AsyncSession):
        """Repository should be creatable from registry."""
        models = ModelRegistry(user_model=ExtendedUserModel)
        entities = EntityRegistry(user_entity=ExtendedUser)

        repo = UserRepository.from_registry(
            async_session,
            models=models,
            entities=entities,
        )

        assert repo._model_class == ExtendedUserModel
        assert repo._entity_class == ExtendedUser


class TestAuthUnitOfWorkExtension:
    """Test AuthUnitOfWork with extension config."""

    @pytest.mark.asyncio
    async def test_uow_default_repositories(self, async_session_factory):
        """UoW should create repositories with default classes."""
        async with AuthUnitOfWork(async_session_factory) as uow:
            assert uow.users._model_class == UserModel
            assert uow.users._entity_class == User

    @pytest.mark.asyncio
    async def test_uow_with_extension_config(self, async_session_factory):
        """UoW should create repositories with custom classes from extension config."""
        extension_config = ExtensionConfig(
            models=ModelRegistry(user_model=ExtendedUserModel),
            entities=EntityRegistry(user_entity=ExtendedUser),
        )

        async with AuthUnitOfWork(
            async_session_factory,
            extension_config=extension_config,
        ) as uow:
            assert uow.users._model_class == ExtendedUserModel
            assert uow.users._entity_class == ExtendedUser


class TestBackwardCompatibility:
    """Test that existing code continues to work without changes."""

    @pytest.mark.asyncio
    async def test_uow_works_without_extension_config(self, async_session_factory):
        """UoW should work exactly as before when no extension config provided."""
        async with AuthUnitOfWork(async_session_factory) as uow:
            # Repositories should be initialized
            assert uow.users is not None
            assert uow.tokens is not None
            assert uow.plans is not None
            assert uow.rbac is not None

    def test_repository_works_with_session_only(self, async_session: AsyncSession):
        """Repository should work with just session parameter (original API)."""
        repo = UserRepository(async_session)

        # Should work with defaults
        assert repo._model_class == UserModel
        assert repo._entity_class == User

    def test_model_registry_getters_work_without_custom_values(self):
        """Registry getters should return defaults when no custom values set."""
        registry = ModelRegistry()

        # All getters should work and return defaults
        assert registry.get_user_model() is not None
        assert registry.get_role_model() is not None
        assert registry.get_plan_model() is not None

    def test_entity_registry_getters_work_without_custom_values(self):
        """Registry getters should return defaults when no custom values set."""
        registry = EntityRegistry()

        # All getters should work and return defaults
        assert registry.get_user_entity() is not None
        assert registry.get_role_entity() is not None
        assert registry.get_plan_entity() is not None


class TestExtendedEntityConversion:
    """Test conversion from extended model to extended entity."""

    def test_extended_entity_has_all_base_fields(self):
        """Extended entity should have all base User fields."""
        # Create extended entity
        entity = ExtendedUser(
            id=UUID("12345678-1234-5678-1234-567812345678"),
            email="test@example.com",
            role_id=UUID("12345678-1234-5678-1234-567812345679"),
            display_name="Test User",
            organization_id=UUID("12345678-1234-5678-1234-56781234567a"),
            department="Engineering",
            employee_id="EMP001",
        )

        # Base fields should be accessible
        assert entity.id == UUID("12345678-1234-5678-1234-567812345678")
        assert entity.email == "test@example.com"
        assert entity.role_id == UUID("12345678-1234-5678-1234-567812345679")
        assert entity.display_name == "Test User"
        assert entity.is_active is True  # default
        assert entity.is_verified is False  # default

        # Extended fields should be accessible
        assert entity.organization_id == UUID("12345678-1234-5678-1234-56781234567a")
        assert entity.department == "Engineering"
        assert entity.employee_id == "EMP001"

    def test_extended_entity_inherits_methods(self):
        """Extended entity should inherit methods from base User."""
        entity = ExtendedUser(
            id=UUID("12345678-1234-5678-1234-567812345678"),
            email="test@example.com",
            role_id=UUID("12345678-1234-5678-1234-567812345679"),
            display_name="Test User",
        )

        # Should be able to call inherited methods
        entity.deactivate()
        assert entity.is_active is False

        entity.activate()
        assert entity.is_active is True


class TestExtendedModelFields:
    """Test extended model has correct field definitions."""

    def test_extended_model_has_base_tablename(self):
        """Extended model should use same table as base model."""
        # Both should use "users" table
        assert ExtendedUserModel.__tablename__ == UserModel.__tablename__ == "users"

    def test_extended_model_has_custom_columns(self):
        """Extended model should have custom columns defined."""
        # Check that custom columns exist
        columns = ExtendedUserModel.__table__.columns

        assert "organization_id" in columns
        assert "department" in columns
        assert "employee_id" in columns

    def test_extended_model_has_base_columns(self):
        """Extended model should have all base columns."""
        columns = ExtendedUserModel.__table__.columns

        # Base columns should exist
        assert "id" in columns
        assert "email" in columns
        assert "role_id" in columns
        assert "display_name" in columns
        assert "is_active" in columns
        assert "is_verified" in columns
        assert "created_at" in columns
        assert "updated_at" in columns
