"""
Registry system for extensible models, entities, and DTOs.

This module provides a registry pattern that allows users to extend
the library's models, entities, and DTOs without modifying library code.

Usage:
    # Create custom model extending the base
    class ExtendedUserModel(UserModel):
        organization_id: Mapped[UUID] = mapped_column(ForeignKey("organizations.id"))

    # Create custom entity
    @dataclass
    class ExtendedUser(User):
        organization_id: UUID | None = None

    # Configure the kit with custom classes
    config = IdentityPlanKitConfig(
        extension_config=ExtensionConfig(
            models=ModelRegistry(user_model=ExtendedUserModel),
            entities=EntityRegistry(user_entity=ExtendedUser),
        )
    )
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from identity_plan_kit.auth.domain.entities import (
        RefreshToken,
        User,
        UserProvider,
    )
    from identity_plan_kit.auth.dto.responses import (
        ProfileResponse,
        UserResponse,
    )
    from identity_plan_kit.auth.models.refresh_token import RefreshTokenModel
    from identity_plan_kit.auth.models.user import UserModel
    from identity_plan_kit.auth.models.user_provider import UserProviderModel
    from identity_plan_kit.plans.domain.entities import (
        Feature,
        FeatureUsage,
        Plan,
        PlanLimit,
        UserPlan,
    )
    from identity_plan_kit.plans.dto.responses import (
        FeatureResponse,
        PlanLimitResponse,
        PlanResponse,
        QuotaResponse,
    )
    from identity_plan_kit.plans.models.feature import FeatureModel
    from identity_plan_kit.plans.models.feature_usage import FeatureUsageModel
    from identity_plan_kit.plans.models.plan import PlanModel
    from identity_plan_kit.plans.models.plan_limit import PlanLimitModel
    from identity_plan_kit.plans.models.plan_permission import PlanPermissionModel
    from identity_plan_kit.plans.models.user_plan import UserPlanModel
    from identity_plan_kit.rbac.domain.entities import Permission, Role
    from identity_plan_kit.rbac.models.permission import PermissionModel
    from identity_plan_kit.rbac.models.role import RoleModel
    from identity_plan_kit.rbac.models.role_permission import RolePermissionModel


def _get_default_user_model() -> type:
    """Lazy import to avoid circular dependencies."""
    from identity_plan_kit.auth.models.user import UserModel

    return UserModel


def _get_default_user_provider_model() -> type:
    """Lazy import to avoid circular dependencies."""
    from identity_plan_kit.auth.models.user_provider import UserProviderModel

    return UserProviderModel


def _get_default_refresh_token_model() -> type:
    """Lazy import to avoid circular dependencies."""
    from identity_plan_kit.auth.models.refresh_token import RefreshTokenModel

    return RefreshTokenModel


def _get_default_role_model() -> type:
    """Lazy import to avoid circular dependencies."""
    from identity_plan_kit.rbac.models.role import RoleModel

    return RoleModel


def _get_default_permission_model() -> type:
    """Lazy import to avoid circular dependencies."""
    from identity_plan_kit.rbac.models.permission import PermissionModel

    return PermissionModel


def _get_default_role_permission_model() -> type:
    """Lazy import to avoid circular dependencies."""
    from identity_plan_kit.rbac.models.role_permission import RolePermissionModel

    return RolePermissionModel


def _get_default_plan_model() -> type:
    """Lazy import to avoid circular dependencies."""
    from identity_plan_kit.plans.models.plan import PlanModel

    return PlanModel


def _get_default_feature_model() -> type:
    """Lazy import to avoid circular dependencies."""
    from identity_plan_kit.plans.models.feature import FeatureModel

    return FeatureModel


def _get_default_plan_limit_model() -> type:
    """Lazy import to avoid circular dependencies."""
    from identity_plan_kit.plans.models.plan_limit import PlanLimitModel

    return PlanLimitModel


def _get_default_user_plan_model() -> type:
    """Lazy import to avoid circular dependencies."""
    from identity_plan_kit.plans.models.user_plan import UserPlanModel

    return UserPlanModel


def _get_default_feature_usage_model() -> type:
    """Lazy import to avoid circular dependencies."""
    from identity_plan_kit.plans.models.feature_usage import FeatureUsageModel

    return FeatureUsageModel


def _get_default_plan_permission_model() -> type:
    """Lazy import to avoid circular dependencies."""
    from identity_plan_kit.plans.models.plan_permission import PlanPermissionModel

    return PlanPermissionModel


# Entity defaults
def _get_default_user_entity() -> type:
    """Lazy import to avoid circular dependencies."""
    from identity_plan_kit.auth.domain.entities import User

    return User


def _get_default_user_provider_entity() -> type:
    """Lazy import to avoid circular dependencies."""
    from identity_plan_kit.auth.domain.entities import UserProvider

    return UserProvider


def _get_default_refresh_token_entity() -> type:
    """Lazy import to avoid circular dependencies."""
    from identity_plan_kit.auth.domain.entities import RefreshToken

    return RefreshToken


def _get_default_role_entity() -> type:
    """Lazy import to avoid circular dependencies."""
    from identity_plan_kit.rbac.domain.entities import Role

    return Role


def _get_default_permission_entity() -> type:
    """Lazy import to avoid circular dependencies."""
    from identity_plan_kit.rbac.domain.entities import Permission

    return Permission


def _get_default_plan_entity() -> type:
    """Lazy import to avoid circular dependencies."""
    from identity_plan_kit.plans.domain.entities import Plan

    return Plan


def _get_default_feature_entity() -> type:
    """Lazy import to avoid circular dependencies."""
    from identity_plan_kit.plans.domain.entities import Feature

    return Feature


def _get_default_plan_limit_entity() -> type:
    """Lazy import to avoid circular dependencies."""
    from identity_plan_kit.plans.domain.entities import PlanLimit

    return PlanLimit


def _get_default_user_plan_entity() -> type:
    """Lazy import to avoid circular dependencies."""
    from identity_plan_kit.plans.domain.entities import UserPlan

    return UserPlan


def _get_default_feature_usage_entity() -> type:
    """Lazy import to avoid circular dependencies."""
    from identity_plan_kit.plans.domain.entities import FeatureUsage

    return FeatureUsage


# DTO defaults
def _get_default_user_response() -> type:
    """Lazy import to avoid circular dependencies."""
    from identity_plan_kit.auth.dto.responses import UserResponse

    return UserResponse


def _get_default_profile_response() -> type:
    """Lazy import to avoid circular dependencies."""
    from identity_plan_kit.auth.dto.responses import ProfileResponse

    return ProfileResponse


def _get_default_plan_response() -> type:
    """Lazy import to avoid circular dependencies."""
    from identity_plan_kit.plans.dto.responses import PlanResponse

    return PlanResponse


def _get_default_feature_response() -> type:
    """Lazy import to avoid circular dependencies."""
    from identity_plan_kit.plans.dto.responses import FeatureResponse

    return FeatureResponse


def _get_default_plan_limit_response() -> type:
    """Lazy import to avoid circular dependencies."""
    from identity_plan_kit.plans.dto.responses import PlanLimitResponse

    return PlanLimitResponse


def _get_default_quota_response() -> type:
    """Lazy import to avoid circular dependencies."""
    from identity_plan_kit.plans.dto.responses import QuotaResponse

    return QuotaResponse


@dataclass
class ModelRegistry:
    """
    Registry for SQLAlchemy model classes.

    Allows customization of model classes used throughout the library.
    All fields default to the library's built-in models if not specified.

    Example:
        # Extend UserModel with custom fields
        class ExtendedUserModel(UserModel):
            organization_id: Mapped[UUID] = mapped_column(ForeignKey("organizations.id"))

        # Use in registry
        registry = ModelRegistry(user_model=ExtendedUserModel)
    """

    # Auth models
    user_model: type[Any] | None = None
    user_provider_model: type[Any] | None = None
    refresh_token_model: type[Any] | None = None

    # RBAC models
    role_model: type[Any] | None = None
    permission_model: type[Any] | None = None
    role_permission_model: type[Any] | None = None

    # Plan models
    plan_model: type[Any] | None = None
    feature_model: type[Any] | None = None
    plan_limit_model: type[Any] | None = None
    user_plan_model: type[Any] | None = None
    feature_usage_model: type[Any] | None = None
    plan_permission_model: type[Any] | None = None

    def get_user_model(self) -> type:
        """Get user model class (custom or default)."""
        return self.user_model or _get_default_user_model()

    def get_user_provider_model(self) -> type:
        """Get user provider model class (custom or default)."""
        return self.user_provider_model or _get_default_user_provider_model()

    def get_refresh_token_model(self) -> type:
        """Get refresh token model class (custom or default)."""
        return self.refresh_token_model or _get_default_refresh_token_model()

    def get_role_model(self) -> type:
        """Get role model class (custom or default)."""
        return self.role_model or _get_default_role_model()

    def get_permission_model(self) -> type:
        """Get permission model class (custom or default)."""
        return self.permission_model or _get_default_permission_model()

    def get_role_permission_model(self) -> type:
        """Get role permission model class (custom or default)."""
        return self.role_permission_model or _get_default_role_permission_model()

    def get_plan_model(self) -> type:
        """Get plan model class (custom or default)."""
        return self.plan_model or _get_default_plan_model()

    def get_feature_model(self) -> type:
        """Get feature model class (custom or default)."""
        return self.feature_model or _get_default_feature_model()

    def get_plan_limit_model(self) -> type:
        """Get plan limit model class (custom or default)."""
        return self.plan_limit_model or _get_default_plan_limit_model()

    def get_user_plan_model(self) -> type:
        """Get user plan model class (custom or default)."""
        return self.user_plan_model or _get_default_user_plan_model()

    def get_feature_usage_model(self) -> type:
        """Get feature usage model class (custom or default)."""
        return self.feature_usage_model or _get_default_feature_usage_model()

    def get_plan_permission_model(self) -> type:
        """Get plan permission model class (custom or default)."""
        return self.plan_permission_model or _get_default_plan_permission_model()


@dataclass
class EntityRegistry:
    """
    Registry for domain entity classes.

    Allows customization of entity classes used throughout the library.
    All fields default to the library's built-in entities if not specified.

    Example:
        # Extend User entity with custom fields
        @dataclass
        class ExtendedUser(User):
            organization_id: UUID | None = None
            department: str | None = None

        # Use in registry
        registry = EntityRegistry(user_entity=ExtendedUser)
    """

    # Auth entities
    user_entity: type[Any] | None = None
    user_provider_entity: type[Any] | None = None
    refresh_token_entity: type[Any] | None = None

    # RBAC entities
    role_entity: type[Any] | None = None
    permission_entity: type[Any] | None = None

    # Plan entities
    plan_entity: type[Any] | None = None
    feature_entity: type[Any] | None = None
    plan_limit_entity: type[Any] | None = None
    user_plan_entity: type[Any] | None = None
    feature_usage_entity: type[Any] | None = None

    def get_user_entity(self) -> type:
        """Get user entity class (custom or default)."""
        return self.user_entity or _get_default_user_entity()

    def get_user_provider_entity(self) -> type:
        """Get user provider entity class (custom or default)."""
        return self.user_provider_entity or _get_default_user_provider_entity()

    def get_refresh_token_entity(self) -> type:
        """Get refresh token entity class (custom or default)."""
        return self.refresh_token_entity or _get_default_refresh_token_entity()

    def get_role_entity(self) -> type:
        """Get role entity class (custom or default)."""
        return self.role_entity or _get_default_role_entity()

    def get_permission_entity(self) -> type:
        """Get permission entity class (custom or default)."""
        return self.permission_entity or _get_default_permission_entity()

    def get_plan_entity(self) -> type:
        """Get plan entity class (custom or default)."""
        return self.plan_entity or _get_default_plan_entity()

    def get_feature_entity(self) -> type:
        """Get feature entity class (custom or default)."""
        return self.feature_entity or _get_default_feature_entity()

    def get_plan_limit_entity(self) -> type:
        """Get plan limit entity class (custom or default)."""
        return self.plan_limit_entity or _get_default_plan_limit_entity()

    def get_user_plan_entity(self) -> type:
        """Get user plan entity class (custom or default)."""
        return self.user_plan_entity or _get_default_user_plan_entity()

    def get_feature_usage_entity(self) -> type:
        """Get feature usage entity class (custom or default)."""
        return self.feature_usage_entity or _get_default_feature_usage_entity()


@dataclass
class DTORegistry:
    """
    Registry for DTO (Data Transfer Object) classes.

    Allows customization of DTO classes used in API responses.
    All fields default to the library's built-in DTOs if not specified.

    Example:
        # Extend UserResponse with custom fields
        class ExtendedUserResponse(UserResponse):
            organization_id: UUID | None = None
            department: str | None = None

        # Use in registry
        registry = DTORegistry(user_response=ExtendedUserResponse)
    """

    # Auth DTOs
    user_response: type[Any] | None = None
    profile_response: type[Any] | None = None

    # Plan DTOs
    plan_response: type[Any] | None = None
    feature_response: type[Any] | None = None
    plan_limit_response: type[Any] | None = None
    quota_response: type[Any] | None = None

    def get_user_response(self) -> type:
        """Get user response class (custom or default)."""
        return self.user_response or _get_default_user_response()

    def get_profile_response(self) -> type:
        """Get profile response class (custom or default)."""
        return self.profile_response or _get_default_profile_response()

    def get_plan_response(self) -> type:
        """Get plan response class (custom or default)."""
        return self.plan_response or _get_default_plan_response()

    def get_feature_response(self) -> type:
        """Get feature response class (custom or default)."""
        return self.feature_response or _get_default_feature_response()

    def get_plan_limit_response(self) -> type:
        """Get plan limit response class (custom or default)."""
        return self.plan_limit_response or _get_default_plan_limit_response()

    def get_quota_response(self) -> type:
        """Get quota response class (custom or default)."""
        return self.quota_response or _get_default_quota_response()


@dataclass
class ExtensionConfig:
    """
    Complete extension configuration combining all registries.

    This is the main configuration object for customizing the library's
    models, entities, and DTOs.

    Example:
        config = ExtensionConfig(
            models=ModelRegistry(user_model=ExtendedUserModel),
            entities=EntityRegistry(user_entity=ExtendedUser),
            dtos=DTORegistry(user_response=ExtendedUserResponse),
        )

        kit_config = IdentityPlanKitConfig(
            # ... other config ...
            extension_config=config,
        )
    """

    models: ModelRegistry = field(default_factory=ModelRegistry)
    entities: EntityRegistry = field(default_factory=EntityRegistry)
    dtos: DTORegistry = field(default_factory=DTORegistry)


# Default singleton instance for convenience
_default_extension_config: ExtensionConfig | None = None


def get_default_extension_config() -> ExtensionConfig:
    """
    Get the default extension config with all built-in classes.

    This is used when no custom extension config is provided.
    """
    global _default_extension_config
    if _default_extension_config is None:
        _default_extension_config = ExtensionConfig()
    return _default_extension_config
