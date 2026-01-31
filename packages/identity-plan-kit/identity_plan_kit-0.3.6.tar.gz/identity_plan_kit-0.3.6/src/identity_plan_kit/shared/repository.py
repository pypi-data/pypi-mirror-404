"""
Generic base repository for extensible data access.

This module provides base repository classes that support generic model
and entity types, enabling users to extend models without rewriting repositories.

Usage:
    # Repositories automatically work with extended models
    class UserRepository(BaseRepository[UserModel, User]):
        _model_class = UserModel
        _entity_class = User
        ...

    # With custom model:
    repo = UserRepository(session, model_class=ExtendedUserModel, entity_class=ExtendedUser)
"""

from __future__ import annotations

import dataclasses
from typing import Any, Generic, TypeVar, get_type_hints

from sqlalchemy.ext.asyncio import AsyncSession

from identity_plan_kit.shared.logging import get_logger

logger = get_logger(__name__)

# Type variables for generic repository
M = TypeVar("M")  # Model type (SQLAlchemy model)
E = TypeVar("E")  # Entity type (domain entity dataclass)


class BaseRepository(Generic[M, E]):
    """
    Generic base repository with configurable model and entity classes.

    This class provides the foundation for repositories that can work with
    extended models and entities without code changes.

    Type Parameters:
        M: The SQLAlchemy model type (e.g., UserModel)
        E: The domain entity type (e.g., User dataclass)

    Class Attributes:
        _model_class: Default model class (can be overridden via constructor)
        _entity_class: Default entity class (can be overridden via constructor)

    Example:
        class UserRepository(BaseRepository[UserModel, User]):
            _model_class = UserModel
            _entity_class = User

            async def get_by_id(self, user_id: UUID) -> User | None:
                stmt = select(self._model_class).where(self._model_class.id == user_id)
                ...

        # Using with extended model:
        repo = UserRepository(
            session,
            model_class=ExtendedUserModel,
            entity_class=ExtendedUser,
        )
    """

    # Default classes - set by subclasses
    _model_class: type[M]
    _entity_class: type[E]

    def __init__(
        self,
        session: AsyncSession,
        model_class: type[M] | None = None,
        entity_class: type[E] | None = None,
    ) -> None:
        """
        Initialize the repository.

        Args:
            session: SQLAlchemy async session for database operations
            model_class: Optional custom model class (overrides _model_class)
            entity_class: Optional custom entity class (overrides _entity_class)
        """
        self._session = session

        # Use provided classes or fall back to class-level defaults
        if model_class is not None:
            self._model_class = model_class
        if entity_class is not None:
            self._entity_class = entity_class

    def _get_entity_field_names(self) -> set[str]:
        """
        Get the field names for the entity class.

        Handles both dataclasses and regular classes with __init__ type hints.

        Returns:
            Set of field names that the entity class accepts
        """
        if dataclasses.is_dataclass(self._entity_class):
            return {f.name for f in dataclasses.fields(self._entity_class)}

        # Fall back to type hints on __init__
        try:
            hints = get_type_hints(self._entity_class.__init__)
            # Remove 'return' hint if present
            hints.pop("return", None)
            return set(hints.keys())
        except (TypeError, AttributeError, NameError):
            # TypeError: if __init__ is not properly typed
            # AttributeError: if class has no __init__
            # NameError: if type hints reference undefined names
            return set()

    def _extract_model_fields(self, model: M, extra_fields: dict[str, Any] | None = None) -> dict[str, Any]:
        """
        Extract fields from a model for entity creation.

        Maps model attributes to entity field names, handling both standard
        and extended models.

        Args:
            model: The SQLAlchemy model instance
            extra_fields: Additional fields to include (e.g., loaded relationships)

        Returns:
            Dictionary of field names to values for entity construction
        """
        entity_fields = self._get_entity_field_names()
        result: dict[str, Any] = {}

        # Extract matching fields from model
        for field_name in entity_fields:
            if hasattr(model, field_name):
                result[field_name] = getattr(model, field_name)

        # Add extra fields (overrides model fields if present)
        if extra_fields:
            result.update(extra_fields)

        return result

    def _to_entity(self, model: M, extra_fields: dict[str, Any] | None = None) -> E:
        """
        Convert a model instance to an entity instance.

        This default implementation extracts all matching fields from the model.
        Override in subclasses for custom conversion logic (e.g., loading relationships).

        Args:
            model: The SQLAlchemy model instance
            extra_fields: Additional fields to pass to entity constructor

        Returns:
            Entity instance with fields populated from model
        """
        fields = self._extract_model_fields(model, extra_fields)
        return self._entity_class(**fields)

    def _create_model(self, **kwargs: Any) -> M:
        """
        Create a new model instance with the given field values.

        This is a helper method for creating models that works with
        both standard and extended model classes.

        Args:
            **kwargs: Field values for the model

        Returns:
            New model instance
        """
        return self._model_class(**kwargs)


class ExtendedFieldsMixin:
    """
    Mixin that provides utilities for handling extended fields.

    Use this mixin in repositories that need to support extended models
    with additional fields beyond the base model.

    Example:
        class UserRepository(BaseRepository[UserModel, User], ExtendedFieldsMixin):
            def _to_entity(self, model: UserModel) -> User:
                # Get extended fields from the model
                extra = self._get_extended_fields(model, User)
                return User(
                    id=model.id,
                    email=model.email,
                    **extra,
                )
    """

    def _get_extended_fields(
        self,
        model: Any,
        base_entity_class: type,
    ) -> dict[str, Any]:
        """
        Get fields from model that are not in the base entity class.

        Useful for extracting custom fields from extended models.

        Args:
            model: The SQLAlchemy model instance
            base_entity_class: The base entity class to compare against

        Returns:
            Dictionary of extended field names to values
        """
        if not dataclasses.is_dataclass(base_entity_class):
            return {}

        base_fields = {f.name for f in dataclasses.fields(base_entity_class)}
        result: dict[str, Any] = {}

        # Get all model attributes that aren't in base entity
        for attr_name in dir(model):
            if attr_name.startswith("_"):
                continue
            if attr_name in base_fields:
                continue
            # Skip SQLAlchemy internal attributes
            if attr_name in ("metadata", "registry"):
                continue

            try:
                value = getattr(model, attr_name)
                # Skip methods and SQLAlchemy relationships/columns metadata
                if callable(value):
                    continue
                result[attr_name] = value
            except (AttributeError, TypeError):
                # AttributeError: property may raise if not initialized
                # TypeError: descriptor may not be accessible
                continue

        return result

    def _model_has_field(self, field_name: str) -> bool:
        """
        Check if the model class has a specific field.

        Args:
            field_name: Name of the field to check

        Returns:
            True if field exists on model class
        """
        model_class = getattr(self, "_model_class", None)
        if model_class is None:
            return False

        # Check for SQLAlchemy column or relationship
        if hasattr(model_class, "__table__"):
            if field_name in model_class.__table__.columns:
                return True

        # Check for property or other attribute
        return hasattr(model_class, field_name)
