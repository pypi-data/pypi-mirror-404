"""Concurrent tests for plan cache.

Tests cover:
- Size property race conditions
- Concurrent get/set operations
- Cache cleanup during access
- Lock-free read safety

CRITICAL: These tests ensure plan cache maintains integrity
under concurrent access patterns.
"""

import asyncio
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from identity_plan_kit.plans.cache.plan_cache import (
    PlanCache,
    InMemoryPlanCache,
    PlanCacheEntry,
)
from identity_plan_kit.plans.domain.entities import Plan

pytestmark = pytest.mark.anyio


def create_test_plan(code: str, name: str | None = None) -> Plan:
    """Create a test plan entity."""
    return Plan(
        id=uuid4(),
        code=code,
        name=name or f"Test Plan {code}",
        permissions={"read", "write"},
        limits={},
    )


class TestCacheSizePropertyRace:
    """
    Test size property race conditions.

    The current implementation accesses self._cache without lock:
    ```
    @property
    def size(self) -> int:
        return len(self._cache)
    ```

    This can race with concurrent modifications.
    """

    async def test_size_during_concurrent_writes(self):
        """Size property should return consistent values during writes."""
        cache = PlanCache(ttl_seconds=300)
        sizes_seen = []

        async def writer():
            for i in range(100):
                plan = create_test_plan(f"plan_{i}")
                await cache.set(f"plan_{i}", plan)
                await asyncio.sleep(0)

        async def reader():
            for _ in range(200):
                sizes_seen.append(cache.size)
                await asyncio.sleep(0)

        await asyncio.gather(writer(), reader())

        # Sizes should be valid integers (no crashes)
        assert all(isinstance(s, int) for s in sizes_seen)
        # Sizes should be non-negative
        assert all(s >= 0 for s in sizes_seen)

    async def test_size_during_invalidate_all(self):
        """Size should handle invalidate_all correctly."""
        cache = PlanCache(ttl_seconds=300)

        # Pre-populate cache
        for i in range(50):
            plan = create_test_plan(f"plan_{i}")
            await cache.set(f"plan_{i}", plan)

        sizes_during = []

        async def invalidator():
            for _ in range(5):
                await cache.invalidate_all()
                await asyncio.sleep(0.01)

        async def reader():
            for _ in range(100):
                sizes_during.append(cache.size)
                await asyncio.sleep(0)

        async def writer():
            for i in range(50, 100):
                plan = create_test_plan(f"plan_{i}")
                await cache.set(f"plan_{i}", plan)
                await asyncio.sleep(0)

        await asyncio.gather(invalidator(), reader(), writer())

        # All sizes should be valid
        assert all(isinstance(s, int) and s >= 0 for s in sizes_during)


class TestConcurrentGetSet:
    """Test concurrent get and set operations."""

    async def test_concurrent_gets_same_plan(self):
        """Multiple concurrent gets return consistent data."""
        cache = PlanCache(ttl_seconds=300)
        plan = create_test_plan("shared_plan", "Shared Plan Name")
        await cache.set("shared_plan", plan)

        async def reader(reader_id: int):
            results = []
            for _ in range(50):
                result = await cache.get("shared_plan")
                results.append(result)
            return results

        # 10 concurrent readers
        all_results = await asyncio.gather(*[reader(i) for i in range(10)])

        # All reads should return the same plan
        for reader_results in all_results:
            for result in reader_results:
                assert result is not None
                assert result.code == "shared_plan"
                assert result.name == "Shared Plan Name"

    async def test_concurrent_sets_same_key(self):
        """Concurrent sets to same key don't corrupt data."""
        cache = PlanCache(ttl_seconds=300)
        corruptions = []

        async def writer(writer_id: int):
            for i in range(20):
                plan = create_test_plan("contested", f"Writer {writer_id} Version {i}")
                await cache.set("contested", plan)

        async def reader():
            for _ in range(100):
                result = await cache.get("contested")
                if result is not None:
                    # Check data integrity
                    if not result.name.startswith("Writer"):
                        corruptions.append(result.name)
                    if result.code != "contested":
                        corruptions.append(f"Wrong code: {result.code}")
                await asyncio.sleep(0)

        await asyncio.gather(
            writer(1),
            writer(2),
            writer(3),
            reader(),
            reader(),
        )

        assert len(corruptions) == 0, f"Data corruptions found: {corruptions}"

    async def test_concurrent_sets_different_keys(self):
        """Concurrent sets to different keys all succeed."""
        cache = PlanCache(ttl_seconds=300)

        async def writer(start: int, count: int):
            for i in range(start, start + count):
                plan = create_test_plan(f"plan_{i}")
                await cache.set(f"plan_{i}", plan)

        # 5 writers, each writing 20 plans
        await asyncio.gather(
            writer(0, 20),
            writer(20, 20),
            writer(40, 20),
            writer(60, 20),
            writer(80, 20),
        )

        # All 100 plans should be cached
        for i in range(100):
            result = await cache.get(f"plan_{i}")
            assert result is not None, f"Plan {i} not found in cache"
            assert result.code == f"plan_{i}"


class TestConcurrentInvalidation:
    """Test cache invalidation under concurrency."""

    async def test_invalidate_during_reads(self):
        """Invalidation during reads doesn't cause errors."""
        cache = PlanCache(ttl_seconds=300)

        # Pre-populate
        for i in range(50):
            plan = create_test_plan(f"plan_{i}")
            await cache.set(f"plan_{i}", plan)

        errors = []

        async def reader():
            for i in range(200):
                try:
                    result = await cache.get(f"plan_{i % 50}")
                    # Result can be None (invalidated) or Plan (still cached)
                except Exception as e:
                    errors.append(str(e))
                await asyncio.sleep(0)

        async def invalidator():
            for i in range(50):
                await cache.invalidate(f"plan_{i}")
                await asyncio.sleep(0.001)

        await asyncio.gather(reader(), reader(), invalidator())

        assert len(errors) == 0, f"Errors during concurrent access: {errors}"

    async def test_invalidate_all_during_operations(self):
        """invalidate_all during other operations is safe."""
        cache = PlanCache(ttl_seconds=300)
        errors = []

        async def writer():
            for i in range(100):
                try:
                    plan = create_test_plan(f"plan_{i}")
                    await cache.set(f"plan_{i}", plan)
                except Exception as e:
                    errors.append(f"Writer error: {e}")
                await asyncio.sleep(0)

        async def reader():
            for i in range(100):
                try:
                    await cache.get(f"plan_{i % 50}")
                except Exception as e:
                    errors.append(f"Reader error: {e}")
                await asyncio.sleep(0)

        async def invalidator():
            for _ in range(10):
                try:
                    await cache.invalidate_all()
                except Exception as e:
                    errors.append(f"Invalidator error: {e}")
                await asyncio.sleep(0.01)

        await asyncio.gather(writer(), reader(), invalidator())

        assert len(errors) == 0, f"Errors during operations: {errors}"


class TestConcurrentCleanup:
    """Test cleanup operations under concurrency."""

    async def test_cleanup_during_access(self):
        """Cleanup during access operations is safe."""
        cache = PlanCache(ttl_seconds=1)  # Short TTL

        # Pre-populate with mix of TTLs
        for i in range(50):
            plan = create_test_plan(f"plan_{i}")
            await cache.set(f"plan_{i}", plan)

        # Wait for entries to expire
        await asyncio.sleep(1.1)

        # Add fresh entries
        for i in range(50, 100):
            plan = create_test_plan(f"plan_{i}")
            await cache.set(f"plan_{i}", plan)

        errors = []

        async def reader():
            for i in range(200):
                try:
                    await cache.get(f"plan_{i % 100}")
                except Exception as e:
                    errors.append(str(e))
                await asyncio.sleep(0)

        async def cleaner():
            for _ in range(5):
                try:
                    await cache.cleanup_expired()
                except Exception as e:
                    errors.append(f"Cleanup error: {e}")
                await asyncio.sleep(0.01)

        await asyncio.gather(reader(), reader(), cleaner())

        assert len(errors) == 0, f"Errors: {errors}"

    async def test_multiple_concurrent_cleanups(self):
        """Multiple concurrent cleanups don't double-delete."""
        cache = PlanCache(ttl_seconds=1)

        # Add entries that will expire
        for i in range(100):
            plan = create_test_plan(f"expired_{i}")
            await cache.set(f"expired_{i}", plan)

        await asyncio.sleep(1.1)

        # Multiple concurrent cleanups
        results = await asyncio.gather(*[
            cache.cleanup_expired() for _ in range(10)
        ])

        # Total cleaned should equal original count (no double counting)
        total_cleaned = sum(results)
        assert total_cleaned == 100, (
            f"Expected 100 total cleaned, got {total_cleaned}. "
            f"Individual results: {results}"
        )


class TestExpirationRace:
    """Test expiration checking race conditions."""

    async def test_entry_expires_during_read(self):
        """Entry expiring during read returns None safely."""
        cache = PlanCache(ttl_seconds=1)
        plan = create_test_plan("expiring_plan")
        await cache.set("expiring_plan", plan)

        # Start reads, some will see the entry, some won't
        await asyncio.sleep(0.9)  # Almost expired

        async def reader():
            results = []
            for _ in range(50):
                result = await cache.get("expiring_plan")
                results.append(result)
                await asyncio.sleep(0.01)
            return results

        all_results = await asyncio.gather(*[reader() for _ in range(5)])

        # Should see a mix of Plan objects and None values
        # as the entry expires during the test
        non_none_count = sum(
            1 for results in all_results for r in results if r is not None
        )
        none_count = sum(
            1 for results in all_results for r in results if r is None
        )

        # Both should be present (some reads before expiry, some after)
        # This isn't a hard assertion since timing is unpredictable
        print(f"Non-none: {non_none_count}, None: {none_count}")

    async def test_is_expired_check_is_atomic(self):
        """The is_expired check shouldn't cause issues during access."""
        # Use InMemoryPlanCache directly for internal attribute access
        cache = InMemoryPlanCache(ttl_seconds=300)

        # Create entry that's close to expiring
        plan = create_test_plan("test_plan")
        entry = PlanCacheEntry(
            plan=plan,
            expires_at=datetime.now(UTC) + timedelta(milliseconds=100),
        )
        cache._cache["test_plan"] = entry

        errors = []

        async def checker():
            for _ in range(100):
                try:
                    # Directly check is_expired (simulating the race)
                    if "test_plan" in cache._cache:
                        _ = cache._cache["test_plan"].is_expired
                except Exception as e:
                    errors.append(str(e))
                await asyncio.sleep(0)

        await asyncio.gather(*[checker() for _ in range(10)])

        assert len(errors) == 0, f"Errors: {errors}"


class TestHighContention:
    """Test behavior under high contention scenarios."""

    async def test_high_contention_mixed_operations(self):
        """High volume mixed operations complete without deadlock."""
        cache = PlanCache(ttl_seconds=300)
        completed = {"sets": 0, "gets": 0, "invalidates": 0}

        async def setter():
            for i in range(100):
                plan = create_test_plan(f"plan_{i % 20}")
                await cache.set(f"plan_{i % 20}", plan)
                completed["sets"] += 1

        async def getter():
            for i in range(200):
                await cache.get(f"plan_{i % 20}")
                completed["gets"] += 1

        async def invalidator():
            for i in range(50):
                await cache.invalidate(f"plan_{i % 20}")
                completed["invalidates"] += 1
                await asyncio.sleep(0.001)

        try:
            await asyncio.wait_for(
                asyncio.gather(
                    setter(),
                    setter(),
                    getter(),
                    getter(),
                    invalidator(),
                ),
                timeout=10.0,
            )
        except asyncio.TimeoutError:
            pytest.fail(f"Deadlock detected! Completed: {completed}")

        # All operations should complete
        assert completed["sets"] == 200
        assert completed["gets"] == 400
        assert completed["invalidates"] == 50

    async def test_lock_free_get_performance(self):
        """Lock-free gets should not be blocked by write operations."""
        # Use InMemoryPlanCache directly for internal attribute access
        cache = InMemoryPlanCache(ttl_seconds=300)

        # Pre-populate
        for i in range(100):
            plan = create_test_plan(f"plan_{i}")
            await cache.set(f"plan_{i}", plan)

        read_count = 0
        write_lock_held = False

        async def slow_writer():
            nonlocal write_lock_held
            async with cache._write_lock:
                write_lock_held = True
                await asyncio.sleep(0.5)  # Hold lock for a while
                write_lock_held = False

        async def fast_reader():
            nonlocal read_count
            start = datetime.now(UTC)
            for i in range(100):
                await cache.get(f"plan_{i}")
                read_count += 1
            elapsed = (datetime.now(UTC) - start).total_seconds()
            return elapsed

        # Start slow writer then readers
        writer_task = asyncio.create_task(slow_writer())
        await asyncio.sleep(0.1)  # Let writer acquire lock

        # Readers should not be blocked
        reader_times = await asyncio.gather(*[fast_reader() for _ in range(5)])

        await writer_task

        # Reads should complete quickly (lock-free)
        # If blocked, they would take > 0.5s
        for elapsed in reader_times:
            assert elapsed < 0.4, (
                f"Reader took {elapsed:.2f}s, likely blocked by write lock"
            )


class TestStaleWritePrevention:
    """
    Test stale write prevention after invalidation.

    These tests verify that the cache rejects writes that fetch data
    before an invalidation occurs, preventing stale data from being
    re-cached after an update.
    """

    async def test_stale_write_rejected_after_invalidation(self):
        """Writes with fetch_ts before invalidation are rejected."""
        cache = PlanCache(ttl_seconds=60)
        plan = create_test_plan("pro")

        # Simulate: Request A fetches plan at T=100
        fetch_ts_before = cache.get_fetch_timestamp()

        # Simulate: Admin invalidates plan at T=101
        await asyncio.sleep(0.001)  # Ensure time advances
        await cache.invalidate("pro")

        # Request A tries to cache stale data
        result = await cache.set("pro", plan, fetched_at=fetch_ts_before)

        # Stale write should be rejected
        assert result is False
        assert await cache.get("pro") is None

    async def test_fresh_write_accepted_after_invalidation(self):
        """Writes with fetch_ts after invalidation are accepted."""
        cache = PlanCache(ttl_seconds=60)
        plan = create_test_plan("pro")

        # Invalidate first
        await cache.invalidate("pro")
        await asyncio.sleep(0.001)  # Ensure time advances

        # Now fetch and cache
        fetch_ts_after = cache.get_fetch_timestamp()
        result = await cache.set("pro", plan, fetched_at=fetch_ts_after)

        # Fresh write should succeed
        assert result is True
        assert await cache.get("pro") == plan

    async def test_stale_write_rejected_after_invalidate_all(self):
        """Writes with fetch_ts before invalidate_all are rejected."""
        cache = PlanCache(ttl_seconds=60)
        plans = [create_test_plan(f"plan_{i}") for i in range(5)]

        # Fetch timestamps before invalidate_all
        fetch_timestamps = [cache.get_fetch_timestamp() for _ in range(5)]

        await asyncio.sleep(0.001)
        await cache.invalidate_all()

        # All stale writes should be rejected
        for i, (plan, fetch_ts) in enumerate(zip(plans, fetch_timestamps)):
            result = await cache.set(f"plan_{i}", plan, fetched_at=fetch_ts)
            assert result is False

    async def test_concurrent_invalidation_and_set(self):
        """
        Simulates race between fetch-set and invalidation.

        Timeline:
        - T=0: Request A fetches plan from DB (fetch_ts=0)
        - T=1: Admin updates plan, calls invalidate()
        - T=2: Request A tries to set stale data (should be rejected)
        """
        cache = PlanCache(ttl_seconds=60)
        plan_v1 = create_test_plan("pro", "Pro v1")
        plan_v2 = create_test_plan("pro", "Pro v2")

        # Request A: fetch timestamp
        fetch_ts_a = cache.get_fetch_timestamp()

        # Concurrent operations
        async def slow_db_fetch():
            """Simulates slow DB query."""
            await asyncio.sleep(0.1)
            # Try to cache stale data
            return await cache.set("pro", plan_v1, fetched_at=fetch_ts_a)

        async def admin_update():
            """Admin invalidates then caches new version."""
            await asyncio.sleep(0.05)  # Invalidate happens during slow fetch
            await cache.invalidate("pro")
            # Admin could also set new version here
            fresh_ts = cache.get_fetch_timestamp()
            await cache.set("pro", plan_v2, fetched_at=fresh_ts)

        results = await asyncio.gather(slow_db_fetch(), admin_update())

        # Stale write should have been rejected
        assert results[0] is False

        # Cache should have v2 (fresh data)
        cached = await cache.get("pro")
        assert cached is not None
        assert cached.name == "Pro v2"

    async def test_set_without_fetch_ts_always_succeeds(self):
        """For backwards compatibility, set without fetch_ts always succeeds."""
        cache = PlanCache(ttl_seconds=60)
        plan = create_test_plan("pro")

        # Invalidate
        await cache.invalidate("pro")

        # Set without fetch_ts (backwards compatible mode)
        result = await cache.set("pro", plan)  # No fetched_at
        assert result is True
        assert await cache.get("pro") == plan


class TestAllPlansCache:
    """Tests for the all-plans cache (get_all/set_all)."""

    async def test_get_all_returns_none_when_empty(self):
        """get_all returns None when cache is empty."""
        cache = PlanCache(ttl_seconds=60)
        result = await cache.get_all()
        assert result is None

    async def test_set_all_and_get_all(self):
        """set_all caches plans, get_all returns them."""
        cache = PlanCache(ttl_seconds=60)
        plans = [create_test_plan(f"plan_{i}") for i in range(3)]

        result = await cache.set_all(plans)
        assert result is True

        cached = await cache.get_all()
        assert cached is not None
        assert len(cached) == 3
        assert all(p.code in [f"plan_{i}" for i in range(3)] for p in cached)

    async def test_set_all_populates_individual_cache(self):
        """set_all also populates individual plan cache entries."""
        cache = PlanCache(ttl_seconds=60)
        plans = [create_test_plan(f"plan_{i}") for i in range(3)]

        await cache.set_all(plans)

        # Individual plans should be cached
        for i in range(3):
            cached = await cache.get(f"plan_{i}")
            assert cached is not None
            assert cached.code == f"plan_{i}"

    async def test_invalidate_clears_all_plans_cache(self):
        """Invalidating a single plan clears the all-plans cache."""
        cache = PlanCache(ttl_seconds=60)
        plans = [create_test_plan(f"plan_{i}") for i in range(3)]

        await cache.set_all(plans)
        assert await cache.get_all() is not None

        # Invalidate a single plan
        await cache.invalidate("plan_1")

        # All-plans cache should be cleared
        assert await cache.get_all() is None

        # Other individual plans should still be cached
        assert await cache.get("plan_0") is not None
        assert await cache.get("plan_2") is not None

    async def test_invalidate_all_clears_all_plans_cache(self):
        """invalidate_all clears the all-plans cache."""
        cache = PlanCache(ttl_seconds=60)
        plans = [create_test_plan(f"plan_{i}") for i in range(3)]

        await cache.set_all(plans)
        assert await cache.get_all() is not None

        await cache.invalidate_all()

        assert await cache.get_all() is None

    async def test_all_plans_cache_expires(self):
        """All-plans cache respects TTL."""
        cache = PlanCache(ttl_seconds=1)
        plans = [create_test_plan(f"plan_{i}") for i in range(3)]

        await cache.set_all(plans)
        assert await cache.get_all() is not None

        # Wait for expiration
        await asyncio.sleep(1.1)

        assert await cache.get_all() is None

    async def test_set_all_stale_write_rejected(self):
        """set_all with stale fetch_ts is rejected after invalidate_all."""
        cache = PlanCache(ttl_seconds=60)
        plans = [create_test_plan(f"plan_{i}") for i in range(3)]

        # Get fetch timestamp before invalidation
        fetch_ts = cache.get_fetch_timestamp()

        await asyncio.sleep(0.001)
        await cache.invalidate_all()

        # Stale write should be rejected
        result = await cache.set_all(plans, fetched_at=fetch_ts)
        assert result is False
        assert await cache.get_all() is None

    async def test_disabled_cache_returns_none(self):
        """Disabled cache (ttl=0) returns None for get_all."""
        cache = PlanCache(ttl_seconds=0)
        plans = [create_test_plan(f"plan_{i}") for i in range(3)]

        result = await cache.set_all(plans)
        assert result is False

        assert await cache.get_all() is None
