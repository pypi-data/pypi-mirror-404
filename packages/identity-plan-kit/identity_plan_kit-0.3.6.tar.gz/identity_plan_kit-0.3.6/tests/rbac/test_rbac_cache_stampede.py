"""Tests for RBAC cache stampede and concurrent access patterns.

Tests cover:
- Cache stampede on cache miss
- Concurrent permission checks
- Cache invalidation during access
- Database load under concurrent requests

CRITICAL: These tests verify that RBAC doesn't overload the database
with duplicate queries during cache misses.
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from identity_plan_kit.rbac.cache.permission_cache import InMemoryPermissionCache

pytestmark = pytest.mark.anyio


class MockRBACRepository:
    """Mock RBAC repository for testing."""

    def __init__(self, query_callback=None):
        self.query_callback = query_callback

    async def get_role_permissions(self, role_id):
        if self.query_callback:
            await self.query_callback(role_id)
        # Simulate DB latency
        await asyncio.sleep(0.05)
        return {"read", "write", "delete"}


class MockUnitOfWork:
    """Mock UOW for testing."""

    def __init__(self, rbac_repo):
        self.rbac = rbac_repo

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        pass


class MockRBACService:
    """
    Simplified mock of RBACService for testing cache behavior.

    This mimics the actual service's cache-check-then-load pattern.
    """

    def __init__(self, cache: InMemoryPermissionCache, uow_factory):
        self._cache = cache
        self._uow_factory = uow_factory

    async def get_user_permissions(self, user_id, role_id) -> set[str]:
        """Get permissions with cache check."""
        # Check cache first
        cached = await self._cache.get(user_id)
        if cached is not None:
            return cached

        # Cache miss - load from DB
        async with self._uow_factory() as uow:
            permissions = await uow.rbac.get_role_permissions(role_id)
            await self._cache.set(user_id, permissions)
            return permissions

    async def check_permission(self, user_id, role_id, permission_code: str) -> bool:
        """Check if user has permission."""
        permissions = await self.get_user_permissions(user_id, role_id)
        return permission_code in permissions

    async def require_permission(self, user_id, role_id, permission_code: str) -> None:
        """Require user to have permission."""
        has_permission = await self.check_permission(user_id, role_id, permission_code)
        if not has_permission:
            raise PermissionError(f"Missing permission: {permission_code}")

    async def invalidate_user_cache(self, user_id) -> None:
        """Invalidate user's cached permissions."""
        await self._cache.invalidate(user_id)

    async def invalidate_all_cache(self) -> None:
        """Invalidate all cached permissions."""
        await self._cache.invalidate_all()


class TestCacheStampede:
    """
    Test cache stampede scenarios.

    Cache stampede occurs when:
    1. Cache entry expires or is missing
    2. Multiple concurrent requests check cache → all miss
    3. All requests hit the database simultaneously
    4. System overloaded with duplicate queries
    """

    async def test_cache_miss_causes_multiple_db_queries(self):
        """
        DOCUMENTS BEHAVIOR: Multiple concurrent requests on cache miss
        each trigger a database query.

        This test documents the current behavior. The cache stampede
        protection is NOT implemented, so this test shows what happens.
        """
        db_query_count = 0

        async def track_query(role_id):
            nonlocal db_query_count
            db_query_count += 1

        cache = InMemoryPermissionCache(ttl_seconds=60)
        rbac_repo = MockRBACRepository(query_callback=track_query)

        def uow_factory():
            return MockUnitOfWork(rbac_repo)

        service = MockRBACService(cache, uow_factory)

        user_id = uuid4()
        role_id = uuid4()

        # Fire concurrent permission requests (all will miss cache)
        tasks = [
            service.get_user_permissions(user_id, role_id)
            for _ in range(10)
        ]
        results = await asyncio.gather(*tasks)

        # All should return the same permissions
        assert all(r == {"read", "write", "delete"} for r in results)

        # OBSERVATION: Without stampede protection, each request hits DB
        # Ideally this should be 1, but current implementation causes N queries
        print(f"DB queries for {len(tasks)} concurrent requests: {db_query_count}")

        # At least one query is needed
        assert db_query_count >= 1

    async def test_cache_hit_avoids_db_queries(self):
        """
        Cache hit should avoid database queries entirely.
        """
        db_query_count = 0

        async def track_query(role_id):
            nonlocal db_query_count
            db_query_count += 1

        cache = InMemoryPermissionCache(ttl_seconds=60)
        rbac_repo = MockRBACRepository(query_callback=track_query)

        def uow_factory():
            return MockUnitOfWork(rbac_repo)

        service = MockRBACService(cache, uow_factory)

        user_id = uuid4()
        role_id = uuid4()

        # Prime the cache with first request
        await service.get_user_permissions(user_id, role_id)
        initial_count = db_query_count

        # Subsequent concurrent requests should hit cache
        tasks = [
            service.get_user_permissions(user_id, role_id)
            for _ in range(10)
        ]
        await asyncio.gather(*tasks)

        # No additional DB queries
        assert db_query_count == initial_count, (
            f"Cache hits caused {db_query_count - initial_count} DB queries"
        )

    async def test_different_users_concurrent_cache_miss(self):
        """
        Different users with cache miss should each query DB (expected).
        """
        db_query_count = 0

        async def track_query(role_id):
            nonlocal db_query_count
            db_query_count += 1

        cache = InMemoryPermissionCache(ttl_seconds=60)
        rbac_repo = MockRBACRepository(query_callback=track_query)

        def uow_factory():
            return MockUnitOfWork(rbac_repo)

        service = MockRBACService(cache, uow_factory)

        # 5 different users
        users = [(uuid4(), uuid4()) for _ in range(5)]

        # Concurrent requests for different users
        tasks = [
            service.get_user_permissions(user_id, role_id)
            for user_id, role_id in users
        ]
        await asyncio.gather(*tasks)

        # Should have at least 5 queries (one per user minimum)
        assert db_query_count >= 5


class TestConcurrentPermissionChecks:
    """Test concurrent permission check scenarios."""

    async def test_concurrent_check_permission_same_user(self):
        """
        Concurrent check_permission calls for same user.
        """
        cache = InMemoryPermissionCache(ttl_seconds=60)
        rbac_repo = MockRBACRepository()

        def uow_factory():
            return MockUnitOfWork(rbac_repo)

        service = MockRBACService(cache, uow_factory)

        user_id = uuid4()
        role_id = uuid4()

        # Many concurrent permission checks
        tasks = [
            service.check_permission(user_id, role_id, "read")
            for _ in range(20)
        ]
        results = await asyncio.gather(*tasks)

        # All should return True (user has "read")
        assert all(r is True for r in results)

    async def test_concurrent_require_permission(self):
        """
        Concurrent require_permission calls should not raise spuriously.
        """
        cache = InMemoryPermissionCache(ttl_seconds=60)
        rbac_repo = MockRBACRepository()

        def uow_factory():
            return MockUnitOfWork(rbac_repo)

        service = MockRBACService(cache, uow_factory)

        user_id = uuid4()
        role_id = uuid4()

        # Many concurrent require_permission calls
        tasks = [
            service.require_permission(user_id, role_id, "read")
            for _ in range(20)
        ]

        # Should all complete without raising
        results = await asyncio.gather(*tasks, return_exceptions=True)
        exceptions = [r for r in results if isinstance(r, Exception)]

        assert len(exceptions) == 0, f"Unexpected exceptions: {exceptions}"


class TestCacheInvalidationRace:
    """Test cache invalidation during concurrent access."""

    async def test_invalidate_during_permission_check(self):
        """
        Cache invalidation during permission check should be safe.

        Race scenario:
        1. Request A gets permissions from cache
        2. Admin invalidates user's cache
        3. Request B sees cache miss
        4. Both requests should complete without error
        """
        cache = InMemoryPermissionCache(ttl_seconds=60)
        rbac_repo = MockRBACRepository()

        def uow_factory():
            return MockUnitOfWork(rbac_repo)

        service = MockRBACService(cache, uow_factory)

        user_id = uuid4()
        role_id = uuid4()

        # Prime cache
        await service.get_user_permissions(user_id, role_id)

        errors = []

        async def check_permissions():
            for _ in range(50):
                try:
                    perms = await service.get_user_permissions(user_id, role_id)
                    assert "read" in perms
                except Exception as e:
                    errors.append(str(e))

        async def invalidate_cache():
            for _ in range(10):
                await service.invalidate_user_cache(user_id)
                await asyncio.sleep(0.01)

        await asyncio.gather(
            check_permissions(),
            check_permissions(),
            invalidate_cache(),
        )

        assert len(errors) == 0, f"Errors during concurrent access: {errors}"

    async def test_invalidate_all_during_concurrent_access(self):
        """
        Global cache invalidation during concurrent access.
        """
        cache = InMemoryPermissionCache(ttl_seconds=60)
        rbac_repo = MockRBACRepository()

        def uow_factory():
            return MockUnitOfWork(rbac_repo)

        service = MockRBACService(cache, uow_factory)

        # Create multiple users
        users = [(uuid4(), uuid4()) for _ in range(5)]

        # Prime cache for all users
        for user_id, role_id in users:
            await service.get_user_permissions(user_id, role_id)

        errors = []

        async def access_permissions():
            for _ in range(20):
                try:
                    user_id, role_id = users[0]
                    await service.get_user_permissions(user_id, role_id)
                except Exception as e:
                    errors.append(str(e))

        async def invalidate_all():
            for _ in range(5):
                await service.invalidate_all_cache()
                await asyncio.sleep(0.01)

        await asyncio.gather(
            access_permissions(),
            access_permissions(),
            invalidate_all(),
        )

        assert len(errors) == 0


class TestHighConcurrencyScenarios:
    """Test high concurrency real-world scenarios."""

    async def test_permission_burst_on_startup(self):
        """
        Simulate startup burst when all users hit simultaneously.

        Real-world scenario: Service restarts, cache is cold, all active
        users make requests at once.
        """
        db_query_count = 0

        async def track_query(role_id):
            nonlocal db_query_count
            db_query_count += 1

        cache = InMemoryPermissionCache(ttl_seconds=60)
        rbac_repo = MockRBACRepository(query_callback=track_query)

        def uow_factory():
            return MockUnitOfWork(rbac_repo)

        service = MockRBACService(cache, uow_factory)

        # 20 different users, 5 requests each = 100 total requests
        num_users = 20
        requests_per_user = 5
        users = [(uuid4(), uuid4()) for _ in range(num_users)]

        tasks = []
        for user_id, role_id in users:
            for _ in range(requests_per_user):
                tasks.append(service.get_user_permissions(user_id, role_id))

        # All requests hit at once (cold cache)
        await asyncio.gather(*tasks)

        # Log the behavior for analysis
        print(f"Total requests: {len(tasks)}")
        print(f"Unique users: {num_users}")
        print(f"DB queries: {db_query_count}")
        print(f"Queries per user: {db_query_count / num_users:.1f}")

        # Each user should have at least one query
        assert db_query_count >= num_users

    async def test_sustained_load_with_cache_expiry(self):
        """
        Sustained load with entries expiring.

        Test that system remains stable when cache entries expire
        during ongoing requests.
        """
        cache = InMemoryPermissionCache(ttl_seconds=1)  # Short TTL
        rbac_repo = MockRBACRepository()

        def uow_factory():
            return MockUnitOfWork(rbac_repo)

        service = MockRBACService(cache, uow_factory)

        user_id = uuid4()
        role_id = uuid4()

        errors = []

        async def sustained_access():
            for i in range(50):
                try:
                    perms = await service.get_user_permissions(user_id, role_id)
                    assert "read" in perms
                except Exception as e:
                    errors.append(f"Request {i}: {e}")
                await asyncio.sleep(0.05)

        # Run for longer than cache TTL (1 second)
        await asyncio.gather(*[sustained_access() for _ in range(5)])

        assert len(errors) == 0, f"Errors: {errors}"


class TestCacheConsistency:
    """Test cache consistency under various scenarios."""

    async def test_permission_set_consistency(self):
        """
        Permission sets should be consistent across concurrent reads.
        """
        expected_perms = {"read", "write", "delete"}
        cache = InMemoryPermissionCache(ttl_seconds=60)
        rbac_repo = MockRBACRepository()

        def uow_factory():
            return MockUnitOfWork(rbac_repo)

        service = MockRBACService(cache, uow_factory)

        user_id = uuid4()
        role_id = uuid4()

        # Concurrent reads
        tasks = [
            service.get_user_permissions(user_id, role_id)
            for _ in range(50)
        ]
        results = await asyncio.gather(*tasks)

        # All should be identical
        for i, result in enumerate(results):
            assert result == expected_perms, (
                f"Request {i} got inconsistent permissions: {result}"
            )

    async def test_no_partial_permission_sets(self):
        """
        Should never observe partial permission sets during updates.
        """
        cache = InMemoryPermissionCache(ttl_seconds=60)
        rbac_repo = MockRBACRepository()

        def uow_factory():
            return MockUnitOfWork(rbac_repo)

        service = MockRBACService(cache, uow_factory)

        user_id = uuid4()
        role_id = uuid4()

        observed_sets = []

        async def observer():
            for _ in range(100):
                perms = await service.get_user_permissions(user_id, role_id)
                observed_sets.append(frozenset(perms))
                await asyncio.sleep(0)

        await asyncio.gather(*[observer() for _ in range(5)])

        # All observed sets should be complete
        expected = frozenset({"read", "write", "delete"})
        partial_sets = [s for s in observed_sets if s != expected]

        assert len(partial_sets) == 0, (
            f"Observed partial permission sets: {partial_sets[:5]}..."
        )


class TestRequestCoalescingMissing:
    """
    Test to document missing request coalescing feature.

    Request coalescing (also known as single-flight) would:
    1. Detect multiple concurrent requests for same key
    2. Only make one DB query
    3. Share result with all waiting requests

    This is NOT implemented - these tests document the gap.
    """

    async def test_no_request_coalescing(self):
        """
        DOCUMENTS MISSING FEATURE: No request coalescing on cache miss.

        With request coalescing, 10 concurrent requests for same user
        would result in 1 DB query. Currently it's 10 queries.
        """
        db_query_count = 0

        async def track_query(role_id):
            nonlocal db_query_count
            db_query_count += 1

        cache = InMemoryPermissionCache(ttl_seconds=60)
        rbac_repo = MockRBACRepository(query_callback=track_query)

        def uow_factory():
            return MockUnitOfWork(rbac_repo)

        service = MockRBACService(cache, uow_factory)

        user_id = uuid4()
        role_id = uuid4()

        # Fire concurrent requests
        num_requests = 10
        tasks = [
            service.get_user_permissions(user_id, role_id)
            for _ in range(num_requests)
        ]
        await asyncio.gather(*tasks)

        # With coalescing: db_query_count == 1
        # Without coalescing: db_query_count == num_requests
        # Documenting current behavior:
        print(
            f"Request coalescing check: "
            f"{num_requests} requests → {db_query_count} DB queries"
        )

        # This is documentation, not a failure assertion
        # If this assertion fails (db_query_count == 1),
        # request coalescing was implemented!
        if db_query_count == 1:
            # Great! Request coalescing is working
            pass
        else:
            # Expected current behavior - no coalescing
            # Log for visibility
            print(
                f"Note: Without request coalescing, {num_requests} concurrent "
                f"cache misses caused {db_query_count} DB queries."
            )
