"""Tests for PermissionCache - P1 priority (caching layer).

Tests cover:
- Cache set and get
- Cache expiration (TTL)
- Cache invalidation
- Cache disabled mode
- Concurrent access
"""

import asyncio
from uuid import UUID

import pytest

from identity_plan_kit.rbac.cache.permission_cache import (
    CacheEntry,
    InMemoryPermissionCache,
    PermissionCache,
    RedisRequiredError,
)

pytestmark = pytest.mark.anyio


class TestCacheEntry:
    """Test suite for CacheEntry dataclass."""

    def test_entry_not_expired(self):
        """Entry with future expiration is not expired."""
        from datetime import UTC, datetime, timedelta

        entry = CacheEntry(
            permissions={"read:data"},
            expires_at=datetime.now(UTC) + timedelta(minutes=5),
        )

        assert entry.is_expired is False

    def test_entry_expired(self):
        """Entry with past expiration is expired."""
        from datetime import UTC, datetime, timedelta

        entry = CacheEntry(
            permissions={"read:data"},
            expires_at=datetime.now(UTC) - timedelta(minutes=1),
        )

        assert entry.is_expired is True


class TestInMemoryPermissionCache:
    """Test suite for InMemoryPermissionCache."""

    @pytest.fixture
    def cache(self) -> InMemoryPermissionCache:
        """Create a cache with 60s TTL."""
        return InMemoryPermissionCache(ttl_seconds=60)

    @pytest.fixture
    def short_ttl_cache(self) -> InMemoryPermissionCache:
        """Create a cache with 1s TTL for testing expiration."""
        return InMemoryPermissionCache(ttl_seconds=1)

    @pytest.fixture
    def disabled_cache(self) -> InMemoryPermissionCache:
        """Create a disabled cache (TTL=0)."""
        return InMemoryPermissionCache(ttl_seconds=0)

    async def test_set_and_get(self, cache: InMemoryPermissionCache):
        """Can set and get permissions."""
        user_id = UUID("12345678-1234-1234-1234-123456789012")
        permissions = {"read:data", "write:data"}

        await cache.set(user_id, permissions)
        result = await cache.get(user_id)

        assert result == permissions

    async def test_get_returns_none_for_missing(self, cache: InMemoryPermissionCache):
        """Get returns None for non-existent user."""
        user_id = UUID("12345678-1234-1234-1234-123456789012")

        result = await cache.get(user_id)

        assert result is None

    async def test_expiration(self, short_ttl_cache: InMemoryPermissionCache):
        """Expired entries return None."""
        user_id = UUID("12345678-1234-1234-1234-123456789012")
        permissions = {"read:data"}

        await short_ttl_cache.set(user_id, permissions)

        # Verify it's cached
        assert await short_ttl_cache.get(user_id) == permissions

        # Wait for expiration
        await asyncio.sleep(1.5)

        # Should be expired now
        assert await short_ttl_cache.get(user_id) is None

    async def test_invalidate_user(self, cache: InMemoryPermissionCache):
        """Invalidate removes user's cached permissions."""
        user_id = UUID("12345678-1234-1234-1234-123456789012")
        permissions = {"read:data"}

        await cache.set(user_id, permissions)
        assert await cache.get(user_id) == permissions

        await cache.invalidate(user_id)

        assert await cache.get(user_id) is None

    async def test_invalidate_all(self, cache: InMemoryPermissionCache):
        """Invalidate all clears entire cache."""
        user1 = UUID("12345678-1234-1234-1234-123456789012")
        user2 = UUID("12345678-1234-1234-1234-123456789013")

        await cache.set(user1, {"perm1"})
        await cache.set(user2, {"perm2"})

        assert cache.size == 2

        await cache.invalidate_all()

        assert cache.size == 0
        assert await cache.get(user1) is None
        assert await cache.get(user2) is None

    async def test_disabled_cache_does_not_store(
        self, disabled_cache: InMemoryPermissionCache
    ):
        """Disabled cache (TTL=0) doesn't store anything."""
        user_id = UUID("12345678-1234-1234-1234-123456789012")

        await disabled_cache.set(user_id, {"read:data"})

        assert await disabled_cache.get(user_id) is None
        assert disabled_cache.size == 0

    async def test_set_copies_permissions(self, cache: InMemoryPermissionCache):
        """Set creates a copy of permissions (immutable)."""
        user_id = UUID("12345678-1234-1234-1234-123456789012")
        permissions = {"read:data"}

        await cache.set(user_id, permissions)

        # Modify original
        permissions.add("write:data")

        # Cached value should be unchanged
        cached = await cache.get(user_id)
        assert cached == {"read:data"}

    async def test_cleanup_expired(self, short_ttl_cache: InMemoryPermissionCache):
        """Cleanup removes expired entries."""
        user1 = UUID("12345678-1234-1234-1234-123456789012")
        user2 = UUID("12345678-1234-1234-1234-123456789013")

        await short_ttl_cache.set(user1, {"perm1"})
        await short_ttl_cache.set(user2, {"perm2"})

        await asyncio.sleep(1.5)

        removed = await short_ttl_cache.cleanup_expired()

        assert removed == 2
        assert short_ttl_cache.size == 0

    async def test_concurrent_access(self, cache: InMemoryPermissionCache):
        """Cache handles concurrent access safely."""
        user_id = UUID("12345678-1234-1234-1234-123456789012")

        async def writer(i: int):
            await cache.set(user_id, {f"perm_{i}"})

        async def reader():
            return await cache.get(user_id)

        # Fire concurrent writes and reads
        tasks = [writer(i) for i in range(10)] + [reader() for _ in range(10)]
        await asyncio.gather(*tasks)

        # Cache should have one of the written values
        result = await cache.get(user_id)
        assert result is not None


class TestPermissionCacheWrapper:
    """Test suite for PermissionCache wrapper class."""

    async def test_uses_in_memory_by_default(self):
        """Uses in-memory cache when no Redis URL provided."""
        cache = PermissionCache(ttl_seconds=60)

        assert cache._is_redis is False
        assert isinstance(cache._backend, InMemoryPermissionCache)

    async def test_raises_when_redis_required_but_missing_url(self):
        """Raises RedisRequiredError when require_redis=True but no URL."""
        with pytest.raises(RedisRequiredError, match="redis_url is not configured"):
            PermissionCache(ttl_seconds=60, require_redis=True)

    async def test_basic_operations_with_in_memory(self):
        """Basic operations work with in-memory backend."""
        cache = PermissionCache(ttl_seconds=60)
        user_id = UUID("12345678-1234-1234-1234-123456789012")

        await cache.set(user_id, {"read:data"})
        result = await cache.get(user_id)

        assert result == {"read:data"}

        await cache.invalidate(user_id)
        assert await cache.get(user_id) is None

    async def test_size_returns_value_for_in_memory(self):
        """Size property works for in-memory backend."""
        cache = PermissionCache(ttl_seconds=60)
        user_id = UUID("12345678-1234-1234-1234-123456789012")

        assert cache.size == 0

        await cache.set(user_id, {"read:data"})

        assert cache.size == 1
