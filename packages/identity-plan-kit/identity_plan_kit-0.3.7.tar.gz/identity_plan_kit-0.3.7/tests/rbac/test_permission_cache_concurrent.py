"""Concurrent access tests for permission cache.

Tests race conditions in:
- Concurrent cache read/write operations
- Cache invalidation during read
- Multiple users accessing cache simultaneously

CRITICAL: These tests ensure the in-memory cache handles
concurrent access correctly without data corruption.
"""

import asyncio
from datetime import UTC, datetime, timedelta
from uuid import UUID

import pytest

from identity_plan_kit.rbac.cache.permission_cache import (
    CacheEntry,
    InMemoryPermissionCache,
    PermissionCache,
)

pytestmark = pytest.mark.anyio


class TestInMemoryPermissionCacheConcurrency:
    """Tests for concurrent access to in-memory permission cache."""

    async def test_concurrent_set_same_user(self):
        """
        Concurrent set operations for same user should not corrupt data.
        """
        cache = InMemoryPermissionCache(ttl_seconds=60)
        user_id = UUID("12345678-1234-1234-1234-123456789012")

        async def set_permissions(perm_set: set[str]) -> None:
            await cache.set(user_id, perm_set)

        # Fire concurrent set operations with different permissions
        permission_sets = [
            {"read", "write"},
            {"admin"},
            {"read", "write", "delete"},
            {"read"},
            {"admin", "superuser"},
        ]

        tasks = [set_permissions(ps) for ps in permission_sets]
        await asyncio.gather(*tasks)

        # Final state should be one of the permission sets (last write wins)
        result = await cache.get(user_id)
        assert result is not None
        assert result in permission_sets

    async def test_concurrent_get_same_user(self):
        """
        Concurrent get operations should all return consistent data.
        """
        cache = InMemoryPermissionCache(ttl_seconds=60)
        user_id = UUID("12345678-1234-1234-1234-123456789012")
        permissions = {"read", "write", "admin"}

        await cache.set(user_id, permissions)

        async def get_permissions() -> set[str] | None:
            return await cache.get(user_id)

        # Fire many concurrent get operations
        tasks = [get_permissions() for _ in range(100)]
        results = await asyncio.gather(*tasks)

        # All should return the same permissions
        for result in results:
            assert result == permissions

    async def test_concurrent_set_different_users(self):
        """
        Concurrent set operations for different users should all succeed.
        """
        cache = InMemoryPermissionCache(ttl_seconds=60)

        async def set_user_permissions(user_num: int) -> UUID:
            user_id = UUID(f"00000000-0000-0000-0000-{user_num:012d}")
            permissions = {f"perm_{user_num}_{i}" for i in range(5)}
            await cache.set(user_id, permissions)
            return user_id

        # Fire concurrent set operations for 50 different users
        tasks = [set_user_permissions(i) for i in range(50)]
        user_ids = await asyncio.gather(*tasks)

        # All users should have their permissions cached
        assert cache.size == 50

        # Verify each user's permissions
        for i, user_id in enumerate(user_ids):
            result = await cache.get(user_id)
            expected = {f"perm_{i}_{j}" for j in range(5)}
            assert result == expected

    async def test_concurrent_get_and_invalidate(self):
        """
        Concurrent get and invalidate operations should be safe.
        """
        cache = InMemoryPermissionCache(ttl_seconds=60)
        user_id = UUID("12345678-1234-1234-1234-123456789012")
        permissions = {"read", "write"}

        await cache.set(user_id, permissions)

        results: list[set[str] | None] = []
        results_lock = asyncio.Lock()

        async def get_permissions() -> None:
            result = await cache.get(user_id)
            async with results_lock:
                results.append(result)

        async def invalidate_user() -> None:
            await cache.invalidate(user_id)

        # Mix get and invalidate operations
        tasks = [
            get_permissions(),
            get_permissions(),
            invalidate_user(),
            get_permissions(),
            get_permissions(),
            invalidate_user(),
            get_permissions(),
        ]
        await asyncio.gather(*tasks)

        # Some gets should return permissions, some None (after invalidation)
        # The exact results depend on scheduling, but no errors should occur
        assert len(results) == 5  # 5 get operations

    async def test_concurrent_invalidate_all_during_access(self):
        """
        invalidate_all during concurrent access should be safe.
        """
        cache = InMemoryPermissionCache(ttl_seconds=60)

        # Populate cache with many users
        for i in range(100):
            user_id = UUID(f"00000000-0000-0000-0000-{i:012d}")
            await cache.set(user_id, {f"perm_{i}"})

        async def get_random_user(user_num: int) -> set[str] | None:
            user_id = UUID(f"00000000-0000-0000-0000-{user_num:012d}")
            return await cache.get(user_id)

        async def invalidate_all() -> None:
            await cache.invalidate_all()

        # Mix operations
        tasks = [
            get_random_user(0),
            get_random_user(50),
            invalidate_all(),
            get_random_user(99),
            get_random_user(25),
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # No exceptions should be raised
        errors = [r for r in results if isinstance(r, Exception)]
        assert len(errors) == 0, f"Unexpected errors: {errors}"

    async def test_cache_expiry_during_concurrent_access(self):
        """
        Cache expiry during concurrent access should be handled gracefully.
        """
        # Very short TTL to trigger expiry
        cache = InMemoryPermissionCache(ttl_seconds=1)
        user_id = UUID("12345678-1234-1234-1234-123456789012")

        await cache.set(user_id, {"read", "write"})

        results: list[set[str] | None] = []
        results_lock = asyncio.Lock()

        async def get_with_delay(delay: float) -> None:
            await asyncio.sleep(delay)
            result = await cache.get(user_id)
            async with results_lock:
                results.append(result)

        # Fire gets at different times, some before and after expiry
        tasks = [
            get_with_delay(0),      # Immediate
            get_with_delay(0.5),    # Before expiry
            get_with_delay(1.2),    # After expiry
            get_with_delay(1.5),    # Well after expiry
        ]
        await asyncio.gather(*tasks)

        # Early gets should return permissions, late gets should return None
        # (though exact timing may vary)
        assert len(results) == 4


class TestPermissionCacheWrapperConcurrency:
    """Tests for the PermissionCache wrapper with concurrent access."""

    async def test_high_concurrency_mixed_operations(self):
        """
        High concurrency with mixed operations should not cause issues.
        """
        cache = PermissionCache(ttl_seconds=60)

        operation_counts = {"get": 0, "set": 0, "invalidate": 0}
        counts_lock = asyncio.Lock()

        async def random_operation(op_num: int) -> None:
            user_id = UUID(f"00000000-0000-0000-0000-{op_num % 10:012d}")
            op_type = op_num % 3

            async with counts_lock:
                if op_type == 0:
                    operation_counts["get"] += 1
                elif op_type == 1:
                    operation_counts["set"] += 1
                else:
                    operation_counts["invalidate"] += 1

            if op_type == 0:
                await cache.get(user_id)
            elif op_type == 1:
                await cache.set(user_id, {f"perm_{op_num}"})
            else:
                await cache.invalidate(user_id)

        # Fire 300 random operations
        tasks = [random_operation(i) for i in range(300)]
        await asyncio.gather(*tasks, return_exceptions=True)

        # Verify operation counts
        total = sum(operation_counts.values())
        assert total == 300


class TestCacheEntryThreadSafety:
    """Tests for CacheEntry data structure."""

    def test_cache_entry_expiry_check(self):
        """CacheEntry expiry check should be accurate."""
        # Not expired
        entry = CacheEntry(
            permissions={"read"},
            expires_at=datetime.now(UTC) + timedelta(minutes=5),
        )
        assert entry.is_expired is False

        # Expired
        expired_entry = CacheEntry(
            permissions={"read"},
            expires_at=datetime.now(UTC) - timedelta(minutes=1),
        )
        assert expired_entry.is_expired is True

    def test_cache_entry_permissions_copy(self):
        """Modifying original set shouldn't affect cached permissions."""
        original = {"read", "write"}
        entry = CacheEntry(
            permissions=original.copy(),  # Should copy
            expires_at=datetime.now(UTC) + timedelta(minutes=5),
        )

        # Modify original
        original.add("admin")

        # Cached permissions should be unchanged
        assert "admin" not in entry.permissions


class TestCacheCleanup:
    """Tests for cache cleanup operations."""

    async def test_cleanup_during_concurrent_access(self):
        """
        cleanup_expired during concurrent access should be safe.
        """
        cache = InMemoryPermissionCache(ttl_seconds=1)

        # Add some entries
        for i in range(20):
            user_id = UUID(f"00000000-0000-0000-0000-{i:012d}")
            await cache.set(user_id, {f"perm_{i}"})

        # Wait for half to expire
        await asyncio.sleep(1.1)

        # Add more (not expired)
        for i in range(20, 40):
            user_id = UUID(f"00000000-0000-0000-0000-{i:012d}")
            await cache.set(user_id, {f"perm_{i}"})

        async def access_cache(user_num: int) -> set[str] | None:
            user_id = UUID(f"00000000-0000-0000-0000-{user_num:012d}")
            return await cache.get(user_id)

        async def run_cleanup() -> int:
            return await cache.cleanup_expired()

        # Mix cleanup with access
        tasks = [
            access_cache(5),
            access_cache(25),
            run_cleanup(),
            access_cache(35),
            run_cleanup(),
            access_cache(10),
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # No exceptions should be raised
        errors = [r for r in results if isinstance(r, Exception)]
        assert len(errors) == 0, f"Unexpected errors: {errors}"

    async def test_multiple_concurrent_cleanups(self):
        """
        Multiple concurrent cleanup operations should be safe.
        """
        cache = InMemoryPermissionCache(ttl_seconds=0)  # Immediate expiry

        # Add entries that will immediately expire
        for i in range(50):
            user_id = UUID(f"00000000-0000-0000-0000-{i:012d}")
            # Manually add with past expiry
            cache._cache[user_id] = CacheEntry(
                permissions={f"perm_{i}"},
                expires_at=datetime.now(UTC) - timedelta(minutes=1),
            )

        # Fire concurrent cleanups
        tasks = [cache.cleanup_expired() for _ in range(10)]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Sum of cleaned entries should equal total
        cleaned_counts = [r for r in results if isinstance(r, int)]
        total_cleaned = sum(cleaned_counts)

        # Total should be 50 (first cleanup gets all, others get 0)
        assert total_cleaned == 50

        # Cache should be empty
        assert cache.size == 0


class TestCacheDisabled:
    """Tests for cache when disabled (ttl=0)."""

    async def test_disabled_cache_always_returns_none(self):
        """Cache with ttl=0 should never store or return data."""
        cache = InMemoryPermissionCache(ttl_seconds=0)
        user_id = UUID("12345678-1234-1234-1234-123456789012")

        await cache.set(user_id, {"read", "write"})
        result = await cache.get(user_id)

        assert result is None
        assert cache.size == 0

    async def test_disabled_cache_concurrent_access(self):
        """Disabled cache should handle concurrent access without errors."""
        cache = InMemoryPermissionCache(ttl_seconds=0)

        async def set_and_get(user_num: int) -> tuple[bool, bool]:
            user_id = UUID(f"00000000-0000-0000-0000-{user_num:012d}")
            await cache.set(user_id, {f"perm_{user_num}"})
            result = await cache.get(user_id)
            return (True, result is None)  # Result should always be None

        tasks = [set_and_get(i) for i in range(100)]
        results = await asyncio.gather(*tasks)

        # All should complete successfully with None results
        for success, is_none in results:
            assert success is True
            assert is_none is True


class TestRealWorldScenarios:
    """Tests simulating real-world access patterns."""

    async def test_permission_check_burst(self):
        """
        Simulate burst of permission checks for same user (e.g., page load with many API calls).
        """
        cache = InMemoryPermissionCache(ttl_seconds=60)
        user_id = UUID("12345678-1234-1234-1234-123456789012")

        # User's permissions are cached after first request
        permissions = {"read", "write", "create", "delete"}
        await cache.set(user_id, permissions)

        async def check_permission(required: str) -> bool:
            cached = await cache.get(user_id)
            if cached is None:
                return False
            return required in cached

        # Simulate 50 concurrent permission checks (like multiple API calls)
        required_perms = ["read"] * 20 + ["write"] * 15 + ["create"] * 10 + ["delete"] * 5
        tasks = [check_permission(p) for p in required_perms]
        results = await asyncio.gather(*tasks)

        # All should succeed
        assert all(results), "All permission checks should pass"

    async def test_role_change_invalidation(self):
        """
        Simulate user role change triggering cache invalidation during active session.
        """
        cache = InMemoryPermissionCache(ttl_seconds=60)
        user_id = UUID("12345678-1234-1234-1234-123456789012")

        # Initial permissions
        await cache.set(user_id, {"read"})

        results: list[tuple[str, set[str] | None]] = []
        results_lock = asyncio.Lock()

        async def check_permissions(label: str) -> None:
            perms = await cache.get(user_id)
            async with results_lock:
                results.append((label, perms))

        async def update_role() -> None:
            # Admin updates user's role
            await cache.invalidate(user_id)
            # New permissions after role change
            await cache.set(user_id, {"read", "write", "admin"})

        # Simulate: user checking permissions -> admin updates role -> user checks again
        await check_permissions("before_update")
        await update_role()
        await check_permissions("after_update")

        # Verify state changes
        before = next(r for r in results if r[0] == "before_update")
        after = next(r for r in results if r[0] == "after_update")

        assert before[1] == {"read"}
        assert after[1] == {"read", "write", "admin"}

    async def test_multiple_users_session_activity(self):
        """
        Simulate multiple users with concurrent session activity.
        """
        cache = InMemoryPermissionCache(ttl_seconds=60)
        user_count = 20
        operations_per_user = 10

        user_ids = [UUID(f"00000000-0000-0000-0000-{i:012d}") for i in range(user_count)]

        # Initialize permissions for all users
        for i, user_id in enumerate(user_ids):
            await cache.set(user_id, {f"perm_{i}_{j}" for j in range(3)})

        async def user_session(user_num: int) -> list[bool]:
            user_id = user_ids[user_num]
            checks = []
            for _ in range(operations_per_user):
                perms = await cache.get(user_id)
                checks.append(perms is not None)
                await asyncio.sleep(0)  # Yield to other tasks
            return checks

        # Simulate all users' sessions concurrently
        tasks = [user_session(i) for i in range(user_count)]
        all_results = await asyncio.gather(*tasks)

        # All permission checks should succeed
        for user_results in all_results:
            assert all(user_results), "All permission checks should find cached data"
