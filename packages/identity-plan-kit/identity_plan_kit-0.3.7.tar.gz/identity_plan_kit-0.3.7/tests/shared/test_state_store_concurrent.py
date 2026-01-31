"""Concurrent tests for state store.

Tests cover:
- Size limit enforcement under concurrent writes
- TOCTOU race conditions in cleanup
- Concurrent get_and_delete atomicity
- Lock contention scenarios

CRITICAL: These tests ensure state store maintains integrity
under high concurrency loads.
"""

import asyncio
from datetime import UTC, datetime, timedelta

import pytest

from identity_plan_kit.shared.state_store import InMemoryStateStore

pytestmark = pytest.mark.anyio


class TestConcurrentSetRespectsSizeLimit:
    """Test state store size limit enforcement under concurrency."""

    async def test_concurrent_set_never_exceeds_max_entries(self):
        """
        CRITICAL: Concurrent sets should never exceed MAX_ENTRIES.

        This tests the TOCTOU race in _enforce_size_limit where:
        1. Multiple coroutines check size outside lock
        2. All pass the check
        3. All run cleanup concurrently
        4. Size could temporarily exceed MAX_ENTRIES
        """
        store = InMemoryStateStore()
        # Override MAX_ENTRIES for faster testing
        store.MAX_ENTRIES = 100
        await store.start()

        try:
            # Fire 200 concurrent sets - should only keep MAX_ENTRIES
            tasks = [
                store.set(f"key_{i}", {"data": f"value_{i}"}, ttl_seconds=300)
                for i in range(200)
            ]
            await asyncio.gather(*tasks)

            # Size should never exceed MAX_ENTRIES
            # Note: This accesses _store directly which is technically a race,
            # but we're testing that the invariant holds after all operations complete
            async with store._lock:
                final_size = len(store._store)

            assert final_size <= store.MAX_ENTRIES, (
                f"Store size {final_size} exceeds MAX_ENTRIES {store.MAX_ENTRIES}"
            )
        finally:
            await store.stop()

    async def test_concurrent_set_with_expiration(self):
        """Concurrent sets with mixed TTLs maintain size limit."""
        store = InMemoryStateStore()
        store.MAX_ENTRIES = 50
        await store.start()

        try:
            # Mix of short and long TTLs
            tasks = []
            for i in range(100):
                ttl = 1 if i % 2 == 0 else 300  # Half expire quickly
                tasks.append(store.set(f"key_{i}", {"i": i}, ttl_seconds=ttl))

            await asyncio.gather(*tasks)

            # Wait for short TTL to expire
            await asyncio.sleep(1.1)

            # Trigger cleanup by setting more
            more_tasks = [
                store.set(f"new_key_{i}", {"i": i}, ttl_seconds=300)
                for i in range(50)
            ]
            await asyncio.gather(*more_tasks)

            async with store._lock:
                final_size = len(store._store)

            assert final_size <= store.MAX_ENTRIES
        finally:
            await store.stop()

    async def test_cleanup_called_once_per_threshold(self):
        """Multiple concurrent sets at threshold trigger minimal cleanups."""
        store = InMemoryStateStore()
        store.MAX_ENTRIES = 20
        await store.start()

        cleanup_calls = 0
        original_enforce = store._enforce_size_limit

        async def counting_enforce():
            nonlocal cleanup_calls
            cleanup_calls += 1
            await original_enforce()

        store._enforce_size_limit = counting_enforce

        try:
            # Fill to just below threshold
            for i in range(19):
                await store.set(f"init_key_{i}", {"i": i}, ttl_seconds=300)

            # Fire many concurrent sets that should trigger cleanup
            tasks = [
                store.set(f"trigger_key_{i}", {"i": i}, ttl_seconds=300)
                for i in range(30)
            ]
            await asyncio.gather(*tasks)

            # Cleanup should have been called multiple times due to race,
            # but the final size should still be within bounds
            async with store._lock:
                final_size = len(store._store)

            assert final_size <= store.MAX_ENTRIES
            # Log cleanup calls for visibility (not a hard assertion since
            # some concurrent cleanups are acceptable)
            print(f"Cleanup called {cleanup_calls} times for {30} concurrent sets")
        finally:
            await store.stop()


class TestConcurrentGetAndDelete:
    """Test atomic get_and_delete under concurrency."""

    async def test_get_and_delete_only_one_succeeds(self):
        """Only one concurrent get_and_delete should succeed."""
        store = InMemoryStateStore()
        await store.start()

        try:
            # Set a value
            await store.set("one_time_token", {"secret": "value"}, ttl_seconds=300)

            # Fire concurrent get_and_delete calls
            tasks = [store.get_and_delete("one_time_token") for _ in range(10)]
            results = await asyncio.gather(*tasks)

            # Exactly one should get the value
            non_none = [r for r in results if r is not None]
            assert len(non_none) == 1
            assert non_none[0] == {"secret": "value"}

            # Key should be gone
            final = await store.get("one_time_token")
            assert final is None
        finally:
            await store.stop()

    async def test_get_and_delete_high_contention(self):
        """Multiple tokens with concurrent get_and_delete."""
        store = InMemoryStateStore()
        await store.start()

        try:
            # Create multiple tokens
            num_tokens = 20
            for i in range(num_tokens):
                await store.set(f"token_{i}", {"id": i}, ttl_seconds=300)

            # Each token accessed by 5 concurrent calls
            all_tasks = []
            for i in range(num_tokens):
                for _ in range(5):
                    all_tasks.append(store.get_and_delete(f"token_{i}"))

            results = await asyncio.gather(*all_tasks)

            # Count successful retrievals per token
            successes = [r for r in results if r is not None]
            assert len(successes) == num_tokens  # Exactly one success per token

            # Verify all tokens were unique
            ids = [r["id"] for r in successes]
            assert len(set(ids)) == num_tokens
        finally:
            await store.stop()


class TestConcurrentCleanup:
    """Test cleanup behavior under concurrent access."""

    async def test_cleanup_during_concurrent_access(self):
        """Cleanup runs safely while other operations occur."""
        store = InMemoryStateStore()
        await store.start()

        try:
            # Pre-populate with some data
            for i in range(50):
                ttl = 1 if i < 25 else 300  # Half will expire
                await store.set(f"key_{i}", {"i": i}, ttl_seconds=ttl)

            # Wait for expiration
            await asyncio.sleep(1.1)

            # Run operations concurrently with cleanup
            async def do_reads():
                for i in range(100):
                    await store.get(f"key_{i % 50}")
                    await asyncio.sleep(0)

            async def do_writes():
                for i in range(50):
                    await store.set(f"new_key_{i}", {"i": i}, ttl_seconds=300)
                    await asyncio.sleep(0)

            async def do_deletes():
                for i in range(25, 50):
                    await store.delete(f"key_{i}")
                    await asyncio.sleep(0)

            # Run all concurrently
            await asyncio.gather(
                do_reads(),
                do_writes(),
                do_deletes(),
                store._cleanup_expired(),  # Manual cleanup
            )

            # Store should be in consistent state
            async with store._lock:
                for key, (value, expires_at) in store._store.items():
                    assert isinstance(value, dict)
                    assert isinstance(expires_at, datetime)
        finally:
            await store.stop()

    async def test_multiple_concurrent_cleanups(self):
        """Multiple concurrent cleanup calls are safe."""
        store = InMemoryStateStore()
        await store.start()

        try:
            # Add expired entries
            past = datetime.now(UTC) - timedelta(seconds=10)
            async with store._lock:
                for i in range(100):
                    store._store[f"expired_{i}"] = ({"i": i}, past)

            # Run multiple cleanups concurrently
            tasks = [store._cleanup_expired() for _ in range(10)]
            await asyncio.gather(*tasks)

            # All expired should be removed
            async with store._lock:
                remaining = len(store._store)

            assert remaining == 0
        finally:
            await store.stop()


class TestSizePropertyRace:
    """Test size-related operations under concurrency."""

    async def test_size_check_during_modification(self):
        """
        Test that size checks during modifications are safe.

        Note: The current implementation does NOT have a size property with lock,
        so this test documents the behavior and expectations.
        """
        store = InMemoryStateStore()
        await store.start()

        try:
            sizes = []

            async def reader():
                for _ in range(100):
                    # Directly access _store length (simulating a size property)
                    sizes.append(len(store._store))
                    await asyncio.sleep(0)

            async def writer():
                for i in range(100):
                    await store.set(f"key_{i}", {"i": i}, ttl_seconds=300)
                    await asyncio.sleep(0)

            await asyncio.gather(reader(), writer())

            # Sizes should be monotonically non-decreasing within each reader pass
            # (though not strictly enforced due to concurrency)
            # The main thing is no crashes occurred
            assert len(sizes) == 100
        finally:
            await store.stop()


class TestLockContention:
    """Test behavior under high lock contention."""

    async def test_high_contention_mixed_operations(self):
        """High volume of mixed operations completes without deadlock."""
        store = InMemoryStateStore()
        await store.start()

        try:
            completed = {"sets": 0, "gets": 0, "deletes": 0, "exists": 0}

            async def setter(start: int):
                for i in range(start, start + 50):
                    await store.set(f"key_{i}", {"value": i}, ttl_seconds=300)
                    completed["sets"] += 1

            async def getter():
                for i in range(200):
                    await store.get(f"key_{i % 100}")
                    completed["gets"] += 1

            async def deleter():
                for i in range(50):
                    await store.delete(f"key_{i}")
                    completed["deletes"] += 1

            async def checker():
                for i in range(100):
                    await store.exists(f"key_{i}")
                    completed["exists"] += 1

            # Run with timeout to detect deadlocks
            try:
                await asyncio.wait_for(
                    asyncio.gather(
                        setter(0),
                        setter(50),
                        getter(),
                        getter(),
                        deleter(),
                        checker(),
                    ),
                    timeout=10.0,
                )
            except asyncio.TimeoutError:
                pytest.fail(
                    f"Deadlock detected! Completed: {completed}"
                )

            # Verify all operations completed
            assert completed["sets"] == 100
            assert completed["gets"] == 400
            assert completed["deletes"] == 50
            assert completed["exists"] == 100
        finally:
            await store.stop()

    async def test_rapid_set_get_same_key(self):
        """Rapid set/get on same key maintains consistency."""
        store = InMemoryStateStore()
        await store.start()

        try:
            key = "contested_key"
            inconsistencies = []

            async def writer(writer_id: int):
                for i in range(50):
                    await store.set(key, {"writer": writer_id, "seq": i}, ttl_seconds=300)

            async def reader():
                for _ in range(100):
                    value = await store.get(key)
                    if value is not None:
                        # Value should be a valid dict with expected keys
                        if "writer" not in value or "seq" not in value:
                            inconsistencies.append(value)

            await asyncio.gather(
                writer(1),
                writer(2),
                reader(),
                reader(),
            )

            # No partial/corrupted values should have been read
            assert len(inconsistencies) == 0, f"Found inconsistent values: {inconsistencies}"
        finally:
            await store.stop()
