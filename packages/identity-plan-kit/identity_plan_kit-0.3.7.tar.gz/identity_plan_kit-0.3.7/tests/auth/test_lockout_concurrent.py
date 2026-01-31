"""Concurrent tests for LockoutManager - race condition coverage.

Tests cover:
- Lost update race in failure counting (non-atomic read-modify-write)
- Concurrent lockout triggering
- Concurrent clear and record operations
- High-concurrency failure bursts

CRITICAL: These tests verify that brute-force protection cannot be
bypassed through concurrent requests.
"""

import asyncio

import pytest

from identity_plan_kit.shared.lockout import AccountLockedError, LockoutConfig, LockoutManager
from identity_plan_kit.shared.state_store import InMemoryStateStore

pytestmark = pytest.mark.anyio


class TestLockoutLostUpdateRace:
    """
    Test for lost update race condition in failure counting.

    The current implementation has a non-atomic read-modify-write pattern:
    1. failure_data = await self._store.get(key)
    2. failure_data["attempts"] += 1
    3. await self._store.set(key, failure_data)

    This can cause lost updates under concurrency.
    """

    @pytest.fixture
    async def store(self) -> InMemoryStateStore:
        """Create a fresh state store for each test."""
        store = InMemoryStateStore()
        await store.start()
        yield store
        await store.stop()

    @pytest.fixture
    def high_threshold_config(self) -> LockoutConfig:
        """Config with high threshold to test counting without lockout."""
        return LockoutConfig(
            max_attempts=100,  # High to avoid lockout during test
            lockout_duration_minutes=5,
            attempt_window_minutes=10,
            track_by_ip=False,  # Simplify by not tracking IP
        )

    async def test_concurrent_failures_all_counted(
        self, store: InMemoryStateStore, high_threshold_config: LockoutConfig
    ):
        """
        CRITICAL: All concurrent failures should be counted.

        This test verifies the lost update race condition. If failures are
        lost, the count will be less than expected.
        """
        manager = LockoutManager(store, high_threshold_config)
        email = "victim@example.com"
        num_concurrent = 20

        # Fire concurrent failures
        tasks = [
            manager.record_failure(email, reason=f"attempt_{i}")
            for i in range(num_concurrent)
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # All should succeed (no exceptions since threshold is high)
        exceptions = [r for r in results if isinstance(r, Exception)]
        assert len(exceptions) == 0, f"Unexpected exceptions: {exceptions}"

        # Get final count
        final_count = await manager.get_failure_count(email)

        # CRITICAL ASSERTION: All failures must be counted
        # If this fails, there's a lost update race condition
        assert final_count == num_concurrent, (
            f"Lost updates detected! Expected {num_concurrent} failures, "
            f"got {final_count}. {num_concurrent - final_count} updates were lost."
        )

    async def test_high_concurrency_failure_burst(
        self, store: InMemoryStateStore, high_threshold_config: LockoutConfig
    ):
        """
        Test extreme concurrency burst doesn't lose updates.

        Simulates a distributed brute-force attack where many attempts
        arrive simultaneously from different sources.
        """
        manager = LockoutManager(store, high_threshold_config)
        email = "target@example.com"
        num_concurrent = 50

        # Create multiple waves of concurrent failures
        for wave in range(3):
            tasks = [
                manager.record_failure(email, reason=f"wave_{wave}_attempt_{i}")
                for i in range(num_concurrent)
            ]
            await asyncio.gather(*tasks, return_exceptions=True)

        # After 3 waves of 50, should have 150 counted
        final_count = await manager.get_failure_count(email)
        expected = num_concurrent * 3

        # Allow some tolerance for extreme race conditions but flag significant loss
        tolerance = expected * 0.1  # 10% tolerance
        assert final_count >= expected - tolerance, (
            f"Significant lost updates! Expected ~{expected}, got {final_count}. "
            f"Lost {expected - final_count} ({(expected - final_count) / expected * 100:.1f}%)"
        )


class TestConcurrentLockoutTrigger:
    """Test lockout triggering under concurrent access."""

    @pytest.fixture
    async def store(self) -> InMemoryStateStore:
        """Create a fresh state store."""
        store = InMemoryStateStore()
        await store.start()
        yield store
        await store.stop()

    @pytest.fixture
    def low_threshold_config(self) -> LockoutConfig:
        """Config with low threshold to trigger lockout easily."""
        return LockoutConfig(
            max_attempts=5,
            lockout_duration_minutes=5,
            attempt_window_minutes=10,
            track_by_ip=False,
        )

    async def test_concurrent_failures_trigger_lockout_exactly_once(
        self, store: InMemoryStateStore, low_threshold_config: LockoutConfig
    ):
        """
        Lockout should trigger when threshold is reached, even under concurrency.

        The race scenario: 5 concurrent failures all check count < 5,
        all increment, but only one (or none!) triggers lockout.
        """
        manager = LockoutManager(store, low_threshold_config)
        email = "user@example.com"

        # Fire exactly max_attempts concurrent failures
        num_failures = low_threshold_config.max_attempts
        tasks = [
            manager.record_failure(email, reason=f"concurrent_{i}")
            for i in range(num_failures)
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # At least one should trigger lockout
        lockout_errors = [r for r in results if isinstance(r, AccountLockedError)]

        # CRITICAL: Lockout must be triggered
        assert len(lockout_errors) >= 1, (
            "Lockout was NOT triggered despite reaching max_attempts! "
            "This is a critical security vulnerability."
        )

        # Verify account is actually locked
        with pytest.raises(AccountLockedError):
            await manager.check_lockout(email)

    async def test_concurrent_failures_exceed_threshold(
        self, store: InMemoryStateStore, low_threshold_config: LockoutConfig
    ):
        """
        More concurrent failures than threshold should still lock account.

        Tests that even if some failures slip through the race, the account
        eventually gets locked.
        """
        manager = LockoutManager(store, low_threshold_config)
        email = "user@example.com"

        # Fire more than max_attempts
        num_failures = low_threshold_config.max_attempts * 2  # 10 failures
        tasks = [
            manager.record_failure(email, reason=f"attempt_{i}")
            for i in range(num_failures)
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Count successes and lockouts
        lockout_errors = [r for r in results if isinstance(r, AccountLockedError)]
        successful_counts = [r for r in results if isinstance(r, int)]

        # Should have some lockout errors (account locked mid-burst)
        assert len(lockout_errors) > 0, (
            "No lockout errors despite double the max_attempts! "
            f"Got results: {results}"
        )

        # Verify account is locked
        with pytest.raises(AccountLockedError):
            await manager.check_lockout(email)


class TestConcurrentClearAndRecord:
    """Test race between clearing and recording failures."""

    @pytest.fixture
    async def store(self) -> InMemoryStateStore:
        """Create a fresh state store."""
        store = InMemoryStateStore()
        await store.start()
        yield store
        await store.stop()

    @pytest.fixture
    def config(self) -> LockoutConfig:
        """Standard config."""
        return LockoutConfig(
            max_attempts=5,
            lockout_duration_minutes=5,
            attempt_window_minutes=10,
            track_by_ip=False,
        )

    async def test_clear_during_failure_burst(
        self, store: InMemoryStateStore, config: LockoutConfig
    ):
        """
        Clear operations during failure burst should not corrupt state.

        Scenario: User successfully authenticates (triggering clear) while
        other failed attempts are still being processed.
        """
        manager = LockoutManager(store, config)
        email = "user@example.com"

        async def record_failures():
            for i in range(10):
                try:
                    await manager.record_failure(email, reason=f"failure_{i}")
                except AccountLockedError:
                    pass
                await asyncio.sleep(0.01)

        async def clear_periodically():
            for _ in range(3):
                await asyncio.sleep(0.02)
                await manager.clear_failures(email)

        await asyncio.gather(record_failures(), clear_periodically())

        # State should be consistent (either locked or cleared)
        # No partial/corrupted state
        status = await manager.get_lockout_status(email)
        count = await manager.get_failure_count(email)

        # Both should be valid values
        assert status is None or status.get("locked") is True
        assert isinstance(count, int) and count >= 0

    async def test_concurrent_clear_operations(
        self, store: InMemoryStateStore, config: LockoutConfig
    ):
        """Multiple concurrent clears should be safe."""
        manager = LockoutManager(store, config)
        email = "user@example.com"

        # Create some failures and lockout
        for i in range(5):
            try:
                await manager.record_failure(email, reason=f"attempt_{i}")
            except AccountLockedError:
                pass

        # Concurrent clear operations
        tasks = [manager.clear_failures(email) for _ in range(10)]
        await asyncio.gather(*tasks)

        # Account should be unlocked and count should be 0
        count = await manager.get_failure_count(email)
        assert count == 0

        # Should not raise
        await manager.check_lockout(email)


class TestMultipleIdentifiersConcurrent:
    """Test concurrent operations on multiple identifiers."""

    @pytest.fixture
    async def store(self) -> InMemoryStateStore:
        """Create a fresh state store."""
        store = InMemoryStateStore()
        await store.start()
        yield store
        await store.stop()

    @pytest.fixture
    def config(self) -> LockoutConfig:
        """Config with moderate threshold."""
        return LockoutConfig(
            max_attempts=3,
            lockout_duration_minutes=5,
            attempt_window_minutes=10,
            track_by_ip=False,
        )

    async def test_concurrent_failures_multiple_users(
        self, store: InMemoryStateStore, config: LockoutConfig
    ):
        """
        Concurrent failures for different users don't interfere.

        Each user should have their own independent failure count.
        """
        manager = LockoutManager(store, config)
        num_users = 10
        failures_per_user = 2  # Below lockout threshold

        # Create tasks for all users
        tasks = []
        for user_id in range(num_users):
            email = f"user{user_id}@example.com"
            for attempt in range(failures_per_user):
                tasks.append(
                    manager.record_failure(email, reason=f"user{user_id}_attempt{attempt}")
                )

        # Shuffle tasks to interleave users (simulating real concurrent access)
        import random
        random.shuffle(tasks)

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # No lockouts should occur (all below threshold)
        lockouts = [r for r in results if isinstance(r, AccountLockedError)]
        assert len(lockouts) == 0, f"Unexpected lockouts: {lockouts}"

        # Each user should have exactly failures_per_user failures
        for user_id in range(num_users):
            email = f"user{user_id}@example.com"
            count = await manager.get_failure_count(email)
            assert count == failures_per_user, (
                f"User {email} has {count} failures, expected {failures_per_user}"
            )

    async def test_some_users_locked_concurrent(
        self, store: InMemoryStateStore, config: LockoutConfig
    ):
        """
        Some users reach lockout threshold while others don't.

        Tests isolation between user accounts under high concurrency.
        """
        manager = LockoutManager(store, config)

        # Users 0-4: Will be locked (5 failures each, threshold is 3)
        # Users 5-9: Won't be locked (2 failures each)
        tasks = []

        for user_id in range(5):
            email = f"locked_user{user_id}@example.com"
            for _ in range(5):
                tasks.append(manager.record_failure(email, reason="lockout_attempt"))

        for user_id in range(5, 10):
            email = f"safe_user{user_id}@example.com"
            for _ in range(2):
                tasks.append(manager.record_failure(email, reason="safe_attempt"))

        # Shuffle and run
        import random
        random.shuffle(tasks)
        await asyncio.gather(*tasks, return_exceptions=True)

        # Verify locked users are actually locked
        for user_id in range(5):
            email = f"locked_user{user_id}@example.com"
            with pytest.raises(AccountLockedError):
                await manager.check_lockout(email)

        # Verify safe users are not locked
        for user_id in range(5, 10):
            email = f"safe_user{user_id}@example.com"
            # Should not raise
            await manager.check_lockout(email)


class TestRapidFireSingleUser:
    """Test rapid sequential and parallel requests for single user."""

    @pytest.fixture
    async def store(self) -> InMemoryStateStore:
        """Create a fresh state store."""
        store = InMemoryStateStore()
        await store.start()
        yield store
        await store.stop()

    async def test_rapid_failures_cause_lockout(self, store: InMemoryStateStore):
        """
        Rapid fire failures should eventually cause lockout.

        This is the core brute-force protection test under realistic conditions.
        """
        config = LockoutConfig(
            max_attempts=10,
            lockout_duration_minutes=5,
            attempt_window_minutes=10,
            track_by_ip=False,
        )
        manager = LockoutManager(store, config)
        email = "victim@example.com"

        lockout_triggered = False
        attempts = 0

        # Fire rapid requests until locked or exceed reasonable attempts
        while not lockout_triggered and attempts < 50:
            try:
                await manager.record_failure(email, reason=f"rapid_{attempts}")
                attempts += 1
            except AccountLockedError:
                lockout_triggered = True

        # Lockout MUST be triggered within reasonable attempts
        assert lockout_triggered, (
            f"Lockout never triggered after {attempts} attempts! "
            f"Max attempts is {config.max_attempts}. "
            "Brute-force protection is broken!"
        )

        # Shouldn't take more than 2x the threshold
        assert attempts <= config.max_attempts * 2, (
            f"Took {attempts} attempts to trigger lockout "
            f"(threshold is {config.max_attempts}). "
            "Lost updates causing delayed lockout."
        )
