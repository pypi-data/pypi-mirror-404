"""RBAC repository for data access."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from identity_plan_kit.rbac.domain.entities import Permission, PermissionType, Role
from identity_plan_kit.rbac.models.permission import PermissionModel
from identity_plan_kit.rbac.models.role import RoleModel
from identity_plan_kit.rbac.models.role_permission import RolePermissionModel
from identity_plan_kit.shared.logging import get_logger

logger = get_logger(__name__)


class RBACRepository:
    """Repository for RBAC data access."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_role_by_id(self, role_id: UUID) -> Role | None:
        """
        Get role by ID with permissions.

        Args:
            role_id: Role UUID

        Returns:
            Role entity with permissions or None
        """
        stmt = (
            select(RoleModel)
            .options(
                selectinload(RoleModel.permissions).selectinload(RolePermissionModel.permission)
            )
            .where(RoleModel.id == role_id)
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()

        if model is None:
            return None

        return self._role_to_entity(model)

    async def get_role_by_code(self, code: str) -> Role | None:
        """
        Get role by code with permissions.

        Args:
            code: Role code (e.g., "admin")

        Returns:
            Role entity with permissions or None
        """
        stmt = (
            select(RoleModel)
            .options(
                selectinload(RoleModel.permissions).selectinload(RolePermissionModel.permission)
            )
            .where(RoleModel.code == code)
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()

        if model is None:
            return None

        return self._role_to_entity(model)

    async def get_role_permissions(self, role_id: UUID) -> set[str]:
        """
        Get all permission codes for a role.

        Args:
            role_id: Role UUID

        Returns:
            Set of permission codes
        """
        stmt = (
            select(PermissionModel.code)
            .join(RolePermissionModel)
            .where(RolePermissionModel.role_id == role_id)
        )
        result = await self._session.execute(stmt)
        return {row[0] for row in result.fetchall()}

    async def get_permission_by_code(self, code: str) -> Permission | None:
        """
        Get permission by code.

        Args:
            code: Permission code (e.g., "users:read")

        Returns:
            Permission entity or None
        """
        stmt = select(PermissionModel).where(PermissionModel.code == code)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()

        if model is None:
            return None

        return self._permission_to_entity(model)

    async def get_all_roles(self) -> list[Role]:
        """
        Get all roles with permissions.

        Returns:
            List of role entities
        """
        stmt = (
            select(RoleModel)
            .options(
                selectinload(RoleModel.permissions).selectinload(RolePermissionModel.permission)
            )
            .order_by(RoleModel.id)
        )
        result = await self._session.execute(stmt)
        models = result.scalars().all()

        return [self._role_to_entity(m) for m in models]

    async def create_role(self, code: str, name: str) -> Role:
        """
        Create a new role.

        Args:
            code: Role code
            name: Role display name

        Returns:
            Created role entity
        """
        model = RoleModel(code=code, name=name)
        self._session.add(model)
        await self._session.flush()

        logger.info("role_created", role_id=str(model.id), code=code)

        return Role(id=model.id, code=model.code, name=model.name)

    async def create_permission(self, code: str, type: PermissionType) -> Permission:
        """
        Create a new permission.

        Args:
            code: Permission code
            type: Permission type (role or plan)

        Returns:
            Created permission entity
        """
        model = PermissionModel(code=code, type=type.value)
        self._session.add(model)
        await self._session.flush()

        logger.info("permission_created", permission_id=str(model.id), code=code)

        return Permission(id=model.id, code=model.code, type=type)

    async def assign_permission_to_role(
        self,
        role_id: UUID,
        permission_id: UUID,
    ) -> None:
        """
        Assign a permission to a role.

        Args:
            role_id: Role UUID
            permission_id: Permission UUID
        """
        model = RolePermissionModel(role_id=role_id, permission_id=permission_id)
        self._session.add(model)
        await self._session.flush()

        logger.info(
            "permission_assigned",
            role_id=str(role_id),
            permission_id=str(permission_id),
        )

    def _role_to_entity(self, model: RoleModel) -> Role:
        """Convert role model to entity."""
        permissions = {rp.permission.code for rp in model.permissions if rp.permission is not None}
        return Role(
            id=model.id,
            code=model.code,
            name=model.name,
            permissions=permissions,
        )

    def _permission_to_entity(self, model: PermissionModel) -> Permission:
        """Convert permission model to entity."""
        return Permission(
            id=model.id,
            code=model.code,
            type=PermissionType(model.type),
        )
