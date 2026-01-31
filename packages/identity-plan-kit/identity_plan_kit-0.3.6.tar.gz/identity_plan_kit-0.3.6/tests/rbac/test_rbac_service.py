"""Tests for RBACService - P1 priority (permission caching).

Tests cover:
- Permission fetching and caching
- Cache hits and misses
- Cache invalidation
- Permission checking
- Role requirements
"""

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID

import pytest

from identity_plan_kit.auth.domain.entities import User
from identity_plan_kit.config import IdentityPlanKitConfig
from identity_plan_kit.rbac.domain.entities import Role
from identity_plan_kit.rbac.domain.exceptions import PermissionDeniedError, RoleNotFoundError
from identity_plan_kit.rbac.services.rbac_service import RBACService

pytestmark = pytest.mark.anyio


class TestGetUserPermissions:
    """Test suite for get_user_permissions method."""

    async def test_fetches_permissions_on_cache_miss(
        self,
        mock_config: IdentityPlanKitConfig,
        mock_user: User,
    ):
        """Permissions fetched from DB on cache miss."""
        expected_permissions = {"read:data", "write:data", "delete:data"}

        mock_uow = AsyncMock()
        mock_uow.__aenter__ = AsyncMock(return_value=mock_uow)
        mock_uow.__aexit__ = AsyncMock(return_value=None)
        mock_uow.rbac.get_role_permissions = AsyncMock(return_value=expected_permissions)

        mock_cache = AsyncMock()
        mock_cache.get = AsyncMock(return_value=None)  # Cache miss
        mock_cache.set = AsyncMock()

        mock_session_factory = MagicMock()
        service = RBACService(mock_config, mock_session_factory)

        with (
            patch.object(service, "_create_uow", return_value=mock_uow),
            patch.object(service, "_cache", mock_cache),
        ):
            result = await service.get_user_permissions(mock_user.id, mock_user.role_id)

        assert result == expected_permissions
        mock_uow.rbac.get_role_permissions.assert_called_once_with(mock_user.role_id)
        mock_cache.set.assert_called_once_with(mock_user.id, expected_permissions)

    async def test_returns_cached_permissions_on_hit(
        self,
        mock_config: IdentityPlanKitConfig,
        mock_user: User,
    ):
        """Cached permissions returned without DB query."""
        cached_permissions = {"cached:permission1", "cached:permission2"}

        mock_cache = AsyncMock()
        mock_cache.get = AsyncMock(return_value=cached_permissions)  # Cache hit!

        mock_session_factory = MagicMock()
        service = RBACService(mock_config, mock_session_factory)

        with patch.object(service, "_cache", mock_cache):
            result = await service.get_user_permissions(mock_user.id, mock_user.role_id)

        assert result == cached_permissions
        # Should not have called create_uow since cache hit

    async def test_caches_permissions_after_fetch(
        self,
        mock_config: IdentityPlanKitConfig,
        mock_user: User,
    ):
        """Fetched permissions are cached."""
        permissions = {"admin:access", "admin:manage"}

        mock_uow = AsyncMock()
        mock_uow.__aenter__ = AsyncMock(return_value=mock_uow)
        mock_uow.__aexit__ = AsyncMock(return_value=None)
        mock_uow.rbac.get_role_permissions = AsyncMock(return_value=permissions)

        mock_cache = AsyncMock()
        mock_cache.get = AsyncMock(return_value=None)
        mock_cache.set = AsyncMock()

        mock_session_factory = MagicMock()
        service = RBACService(mock_config, mock_session_factory)

        with (
            patch.object(service, "_create_uow", return_value=mock_uow),
            patch.object(service, "_cache", mock_cache),
        ):
            await service.get_user_permissions(mock_user.id, mock_user.role_id)

        mock_cache.set.assert_called_once_with(mock_user.id, permissions)


class TestCheckPermission:
    """Test suite for check_permission method."""

    async def test_returns_true_when_user_has_permission(
        self,
        mock_config: IdentityPlanKitConfig,
        mock_user: User,
    ):
        """Returns True when user has the required permission."""
        permissions = {"read:data", "write:data"}

        mock_cache = AsyncMock()
        mock_cache.get = AsyncMock(return_value=permissions)

        mock_session_factory = MagicMock()
        service = RBACService(mock_config, mock_session_factory)

        with patch.object(service, "_cache", mock_cache):
            result = await service.check_permission(
                mock_user.id, mock_user.role_id, "read:data"
            )

        assert result is True

    async def test_returns_false_when_user_lacks_permission(
        self,
        mock_config: IdentityPlanKitConfig,
        mock_user: User,
    ):
        """Returns False when user doesn't have the required permission."""
        permissions = {"read:data"}

        mock_cache = AsyncMock()
        mock_cache.get = AsyncMock(return_value=permissions)

        mock_session_factory = MagicMock()
        service = RBACService(mock_config, mock_session_factory)

        with patch.object(service, "_cache", mock_cache):
            result = await service.check_permission(
                mock_user.id, mock_user.role_id, "admin:access"
            )

        assert result is False


class TestRequirePermission:
    """Test suite for require_permission method."""

    async def test_passes_when_user_has_permission(
        self,
        mock_config: IdentityPlanKitConfig,
        mock_user: User,
    ):
        """No exception when user has required permission."""
        permissions = {"admin:access"}

        mock_cache = AsyncMock()
        mock_cache.get = AsyncMock(return_value=permissions)

        mock_session_factory = MagicMock()
        service = RBACService(mock_config, mock_session_factory)

        with patch.object(service, "_cache", mock_cache):
            # Should not raise
            await service.require_permission(
                mock_user.id, mock_user.role_id, "admin:access"
            )

    async def test_raises_when_user_lacks_permission(
        self,
        mock_config: IdentityPlanKitConfig,
        mock_user: User,
    ):
        """PermissionDeniedError when user lacks permission."""
        permissions = {"read:data"}

        mock_cache = AsyncMock()
        mock_cache.get = AsyncMock(return_value=permissions)

        mock_session_factory = MagicMock()
        service = RBACService(mock_config, mock_session_factory)

        with patch.object(service, "_cache", mock_cache):
            with pytest.raises(PermissionDeniedError) as exc_info:
                await service.require_permission(
                    mock_user.id, mock_user.role_id, "admin:delete"
                )

        assert "admin:delete" in str(exc_info.value)


class TestRequireRole:
    """Test suite for require_role method."""

    async def test_passes_when_role_matches(
        self,
        mock_config: IdentityPlanKitConfig,
    ):
        """No exception when user has required role."""
        mock_session_factory = MagicMock()
        service = RBACService(mock_config, mock_session_factory)

        # Should not raise
        await service.require_role("admin", "admin")

    async def test_raises_when_role_mismatch(
        self,
        mock_config: IdentityPlanKitConfig,
    ):
        """PermissionDeniedError when role doesn't match."""
        mock_session_factory = MagicMock()
        service = RBACService(mock_config, mock_session_factory)

        with pytest.raises(PermissionDeniedError) as exc_info:
            await service.require_role("user", "admin")

        assert "admin" in str(exc_info.value)


class TestCacheInvalidation:
    """Test suite for cache invalidation."""

    async def test_invalidate_user_cache(
        self,
        mock_config: IdentityPlanKitConfig,
        mock_user: User,
    ):
        """User cache is invalidated."""
        mock_cache = AsyncMock()
        mock_cache.invalidate = AsyncMock()

        mock_session_factory = MagicMock()
        service = RBACService(mock_config, mock_session_factory)

        with patch.object(service, "_cache", mock_cache):
            await service.invalidate_user_cache(mock_user.id)

        mock_cache.invalidate.assert_called_once_with(mock_user.id)

    async def test_invalidate_all_cache(
        self,
        mock_config: IdentityPlanKitConfig,
    ):
        """All cache is invalidated."""
        mock_cache = AsyncMock()
        mock_cache.invalidate_all = AsyncMock()

        mock_session_factory = MagicMock()
        service = RBACService(mock_config, mock_session_factory)

        with patch.object(service, "_cache", mock_cache):
            await service.invalidate_all_cache()

        mock_cache.invalidate_all.assert_called_once()


class TestGetRole:
    """Test suite for get_role methods."""

    async def test_get_role_by_id(
        self,
        mock_config: IdentityPlanKitConfig,
    ):
        """Role retrieved by ID."""
        expected_role = Role(
            id=1,
            code="admin",
            name="Administrator",
            permissions={"admin:access", "admin:manage"},
        )

        mock_uow = AsyncMock()
        mock_uow.__aenter__ = AsyncMock(return_value=mock_uow)
        mock_uow.__aexit__ = AsyncMock(return_value=None)
        mock_uow.rbac.get_role_by_id = AsyncMock(return_value=expected_role)

        mock_session_factory = MagicMock()
        service = RBACService(mock_config, mock_session_factory)

        with patch.object(service, "_create_uow", return_value=mock_uow):
            result = await service.get_role(1)

        assert result == expected_role
        assert result.code == "admin"

    async def test_get_role_by_id_not_found(
        self,
        mock_config: IdentityPlanKitConfig,
    ):
        """RoleNotFoundError when role doesn't exist."""
        mock_uow = AsyncMock()
        mock_uow.__aenter__ = AsyncMock(return_value=mock_uow)
        mock_uow.__aexit__ = AsyncMock(return_value=None)
        mock_uow.rbac.get_role_by_id = AsyncMock(return_value=None)

        mock_session_factory = MagicMock()
        service = RBACService(mock_config, mock_session_factory)

        with patch.object(service, "_create_uow", return_value=mock_uow):
            with pytest.raises(RoleNotFoundError):
                await service.get_role(999)

    async def test_get_role_by_code(
        self,
        mock_config: IdentityPlanKitConfig,
    ):
        """Role retrieved by code."""
        expected_role = Role(
            id=2,
            code="user",
            name="Regular User",
            permissions={"read:data"},
        )

        mock_uow = AsyncMock()
        mock_uow.__aenter__ = AsyncMock(return_value=mock_uow)
        mock_uow.__aexit__ = AsyncMock(return_value=None)
        mock_uow.rbac.get_role_by_code = AsyncMock(return_value=expected_role)

        mock_session_factory = MagicMock()
        service = RBACService(mock_config, mock_session_factory)

        with patch.object(service, "_create_uow", return_value=mock_uow):
            result = await service.get_role_by_code("user")

        assert result == expected_role

    async def test_get_role_by_code_not_found(
        self,
        mock_config: IdentityPlanKitConfig,
    ):
        """RoleNotFoundError when role code doesn't exist."""
        mock_uow = AsyncMock()
        mock_uow.__aenter__ = AsyncMock(return_value=mock_uow)
        mock_uow.__aexit__ = AsyncMock(return_value=None)
        mock_uow.rbac.get_role_by_code = AsyncMock(return_value=None)

        mock_session_factory = MagicMock()
        service = RBACService(mock_config, mock_session_factory)

        with patch.object(service, "_create_uow", return_value=mock_uow):
            with pytest.raises(RoleNotFoundError) as exc_info:
                await service.get_role_by_code("nonexistent")

        assert "nonexistent" in str(exc_info.value)


class TestServiceLifecycle:
    """Test suite for service startup/shutdown."""

    async def test_startup_connects_cache(
        self,
        mock_config: IdentityPlanKitConfig,
    ):
        """Startup connects cache backend."""
        mock_cache = AsyncMock()
        mock_cache.connect = AsyncMock()

        mock_session_factory = MagicMock()
        service = RBACService(mock_config, mock_session_factory)

        with patch.object(service, "_cache", mock_cache):
            await service.startup()

        mock_cache.connect.assert_called_once()

    async def test_shutdown_disconnects_cache(
        self,
        mock_config: IdentityPlanKitConfig,
    ):
        """Shutdown disconnects cache backend."""
        mock_cache = AsyncMock()
        mock_cache.disconnect = AsyncMock()

        mock_session_factory = MagicMock()
        service = RBACService(mock_config, mock_session_factory)

        with patch.object(service, "_cache", mock_cache):
            await service.shutdown()

        mock_cache.disconnect.assert_called_once()
