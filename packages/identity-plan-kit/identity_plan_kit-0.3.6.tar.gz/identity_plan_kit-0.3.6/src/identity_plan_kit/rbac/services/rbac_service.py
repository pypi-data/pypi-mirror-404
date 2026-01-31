"""RBAC service for permission management."""

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from identity_plan_kit.config import IdentityPlanKitConfig
from identity_plan_kit.rbac.cache.permission_cache import PermissionCache
from identity_plan_kit.rbac.domain.entities import Role
from identity_plan_kit.rbac.domain.exceptions import PermissionDeniedError, RoleNotFoundError
from identity_plan_kit.rbac.uow import RBACUnitOfWork
from identity_plan_kit.shared.logging import get_logger

logger = get_logger(__name__)


class RBACService:
    """Service for RBAC operations."""

    def __init__(
        self,
        config: IdentityPlanKitConfig,
        session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        self._config = config
        self._session_factory = session_factory
        # P2 FIX: Pass require_redis to fail-fast in multi-instance deployments
        self._cache = PermissionCache(
            ttl_seconds=config.permission_cache_ttl_seconds,
            redis_url=config.redis_url,
            require_redis=config.require_redis,
        )

    def _create_uow(
        self,
        session: AsyncSession | None = None,
    ) -> RBACUnitOfWork:
        """
        Create a new Unit of Work instance.

        Args:
            session: Optional external session for transaction participation.
        """
        return RBACUnitOfWork(self._session_factory, session=session)

    async def startup(self) -> None:
        """Connect cache backend (required for Redis)."""
        await self._cache.connect()

    async def shutdown(self) -> None:
        """Disconnect cache backend."""
        await self._cache.disconnect()

    async def get_role(self, role_id: UUID) -> Role:
        """
        Get role by ID.

        Args:
            role_id: Role UUID

        Returns:
            Role entity with permissions

        Raises:
            RoleNotFoundError: If role doesn't exist
        """
        async with self._create_uow() as uow:
            role = await uow.rbac.get_role_by_id(role_id)

            if role is None:
                raise RoleNotFoundError()

            return role

    async def get_role_by_code(self, code: str) -> Role:
        """
        Get role by code.

        Args:
            code: Role code (e.g., "admin")

        Returns:
            Role entity with permissions

        Raises:
            RoleNotFoundError: If role doesn't exist
        """
        async with self._create_uow() as uow:
            role = await uow.rbac.get_role_by_code(code)

            if role is None:
                raise RoleNotFoundError(code)

            return role

    async def get_user_permissions(
        self,
        user_id: UUID,
        role_id: UUID,
    ) -> set[str]:
        """
        Get all permissions for a user.

        Args:
            user_id: User UUID
            role_id: User's role UUID

        Returns:
            Set of permission codes (cached for performance)
        """
        # Check cache first
        cached = await self._cache.get(user_id)
        if cached is not None:
            return cached

        async with self._create_uow() as uow:
            # Get role permissions
            permissions = await uow.rbac.get_role_permissions(role_id)

            # Cache result
            await self._cache.set(user_id, permissions)

            logger.debug(
                "permissions_loaded",
                user_id=str(user_id),
                count=len(permissions),
            )

            return permissions

    async def check_permission(
        self,
        user_id: UUID,
        role_id: UUID,
        permission_code: str,
    ) -> bool:
        """
        Check if user has a specific permission.

        Args:
            user_id: User UUID
            role_id: User's role UUID
            permission_code: Permission to check

        Returns:
            True if user has permission
        """
        permissions = await self.get_user_permissions(user_id, role_id)
        has_permission = permission_code in permissions

        if not has_permission:
            logger.debug(
                "permission_check_failed",
                user_id=str(user_id),
                permission=permission_code,
            )

        return has_permission

    async def require_permission(
        self,
        user_id: UUID,
        role_id: UUID,
        permission_code: str,
    ) -> None:
        """
        Require user to have a specific permission.

        Args:
            user_id: User UUID
            role_id: User's role UUID
            permission_code: Required permission

        Raises:
            PermissionDeniedError: If user doesn't have permission
        """
        has_permission = await self.check_permission(user_id, role_id, permission_code)

        if not has_permission:
            logger.warning(
                "permission_denied",
                user_id=str(user_id),
                permission=permission_code,
            )
            raise PermissionDeniedError(permission_code)

    async def require_role(
        self,
        user_role_code: str,
        required_role_code: str,
    ) -> None:
        """
        Require user to have a specific role.

        Args:
            user_role_code: User's current role code
            required_role_code: Required role code

        Raises:
            PermissionDeniedError: If user doesn't have the role
        """
        if user_role_code != required_role_code:
            logger.warning(
                "role_check_failed",
                user_role=user_role_code,
                required_role=required_role_code,
            )
            raise PermissionDeniedError(message=f"Required role: {required_role_code}")

    async def invalidate_user_cache(self, user_id: UUID) -> None:
        """
        Invalidate cached permissions for a user.

        Call this when user's role or permissions change.

        Args:
            user_id: User UUID
        """
        await self._cache.invalidate(user_id)
        logger.debug("user_cache_invalidated", user_id=str(user_id))

    async def invalidate_all_cache(self) -> None:
        """
        Invalidate all cached permissions.

        Call this when roles or permissions are modified globally.
        """
        await self._cache.invalidate_all()
