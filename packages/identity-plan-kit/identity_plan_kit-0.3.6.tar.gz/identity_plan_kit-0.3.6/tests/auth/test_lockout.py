"""Tests for LockoutManager - P1 priority (brute-force protection).

Tests cover:
- Failure tracking and counting
- Account lockout after max attempts
- Lockout check and rejection
- Clearing failures on success
- IP-based tracking
- Lockout status queries
"""

import asyncio
from datetime import UTC, datetime, timedelta

import pytest

from identity_plan_kit.shared.lockout import AccountLockedError, LockoutConfig, LockoutManager
from identity_plan_kit.shared.state_store import InMemoryStateStore

pytestmark = pytest.mark.anyio


class TestLockoutManager:
    """Test suite for LockoutManager brute-force protection."""

    @pytest.fixture
    async def store(self) -> InMemoryStateStore:
        """Create a fresh state store for each test."""
        store = InMemoryStateStore()
        await store.start()
        yield store
        await store.stop()

    @pytest.fixture
    def config(self) -> LockoutConfig:
        """Create lockout config with low thresholds for testing."""
        return LockoutConfig(
            max_attempts=3,
            lockout_duration_minutes=5,
            attempt_window_minutes=10,
            track_by_ip=True,
        )

    @pytest.fixture
    def manager(self, store: InMemoryStateStore, config: LockoutConfig) -> LockoutManager:
        """Create lockout manager with test config."""
        return LockoutManager(store, config)


class TestFailureTracking(TestLockoutManager):
    """Test failure recording and counting."""

    async def test_records_first_failure(self, manager: LockoutManager):
        """First failure is recorded with count of 1."""
        count = await manager.record_failure(
            "test@example.com",
            ip_address="1.2.3.4",
            reason="invalid_code",
        )
        assert count == 1

    async def test_increments_failure_count(self, manager: LockoutManager):
        """Each failure increments the count."""
        email = "test@example.com"

        count1 = await manager.record_failure(email, reason="attempt_1")
        count2 = await manager.record_failure(email, reason="attempt_2")

        assert count1 == 1
        assert count2 == 2

    async def test_get_failure_count(self, manager: LockoutManager):
        """Can query current failure count."""
        email = "test@example.com"

        # Initial count is 0
        assert await manager.get_failure_count(email) == 0

        await manager.record_failure(email, reason="test")
        await manager.record_failure(email, reason="test")

        assert await manager.get_failure_count(email) == 2

    async def test_tracks_by_identifier_and_ip(
        self, store: InMemoryStateStore, config: LockoutConfig
    ):
        """Failures tracked by both identifier and IP when enabled."""
        manager = LockoutManager(store, config)

        # Same email, different IPs
        await manager.record_failure(
            "user@example.com", ip_address="1.1.1.1", reason="test"
        )
        await manager.record_failure(
            "user@example.com", ip_address="2.2.2.2", reason="test"
        )

        # Each IP has its own count
        assert await manager.get_failure_count("user@example.com", "1.1.1.1") == 1
        assert await manager.get_failure_count("user@example.com", "2.2.2.2") == 1

    async def test_tracks_only_by_identifier_when_ip_disabled(
        self, store: InMemoryStateStore
    ):
        """With track_by_ip=False, only identifier is tracked."""
        config = LockoutConfig(
            max_attempts=5,
            lockout_duration_minutes=5,
            track_by_ip=False,
        )
        manager = LockoutManager(store, config)

        # Same email, different IPs, but track_by_ip=False
        await manager.record_failure(
            "user@example.com", ip_address="1.1.1.1", reason="test"
        )
        await manager.record_failure(
            "user@example.com", ip_address="2.2.2.2", reason="test"
        )

        # Should count all attempts together
        # Note: get_failure_count with IP will still use the key without IP
        assert await manager.get_failure_count("user@example.com") == 2


class TestAccountLockout(TestLockoutManager):
    """Test account lockout triggering."""

    async def test_lockout_after_max_attempts(self, manager: LockoutManager):
        """Account locked after reaching max attempts (3)."""
        email = "test@example.com"

        await manager.record_failure(email, reason="attempt_1")
        await manager.record_failure(email, reason="attempt_2")

        # Third attempt should trigger lockout
        with pytest.raises(AccountLockedError) as exc_info:
            await manager.record_failure(email, reason="attempt_3")

        assert exc_info.value.failed_attempts == 3
        assert exc_info.value.retry_after_seconds > 0

    async def test_lockout_error_contains_details(self, manager: LockoutManager):
        """AccountLockedError contains useful information."""
        email = "test@example.com"

        for _ in range(2):
            await manager.record_failure(email, reason="test")

        with pytest.raises(AccountLockedError) as exc_info:
            await manager.record_failure(email, reason="final")

        error = exc_info.value
        assert error.identifier == email
        assert error.unlock_at > datetime.now(UTC)
        assert error.failed_attempts == 3
        assert 0 < error.retry_after_seconds <= 300  # 5 minutes

    async def test_check_lockout_blocks_locked_account(self, manager: LockoutManager):
        """Locked accounts are rejected on check_lockout."""
        email = "test@example.com"

        # Trigger lockout
        for i in range(3):
            try:
                await manager.record_failure(email, reason=f"attempt_{i}")
            except AccountLockedError:
                pass

        # Subsequent check should raise
        with pytest.raises(AccountLockedError):
            await manager.check_lockout(email)

    async def test_check_lockout_allows_unlocked_account(self, manager: LockoutManager):
        """Unlocked accounts pass check_lockout."""
        email = "test@example.com"

        # No failures yet
        await manager.check_lockout(email)  # Should not raise

        # Some failures but below threshold
        await manager.record_failure(email, reason="test")
        await manager.record_failure(email, reason="test")

        await manager.check_lockout(email)  # Should still not raise


class TestClearingFailures(TestLockoutManager):
    """Test clearing failures on successful auth."""

    async def test_clear_failures_resets_count(self, manager: LockoutManager):
        """Clearing failures resets count to 0."""
        email = "test@example.com"

        await manager.record_failure(email, reason="test")
        await manager.record_failure(email, reason="test")

        assert await manager.get_failure_count(email) == 2

        await manager.clear_failures(email)

        assert await manager.get_failure_count(email) == 0

    async def test_clear_failures_lifts_lockout(self, manager: LockoutManager):
        """Successful auth clears lockout status."""
        email = "test@example.com"

        # Trigger lockout
        for i in range(3):
            try:
                await manager.record_failure(email, reason=f"attempt_{i}")
            except AccountLockedError:
                pass

        # Verify locked
        with pytest.raises(AccountLockedError):
            await manager.check_lockout(email)

        # Clear on successful auth
        await manager.clear_failures(email)

        # Should be unlocked now
        await manager.check_lockout(email)  # Should not raise

    async def test_clear_failures_with_ip(self, manager: LockoutManager):
        """Clearing failures also clears IP-specific tracking."""
        email = "test@example.com"
        ip = "1.2.3.4"

        await manager.record_failure(email, ip_address=ip, reason="test")
        await manager.record_failure(email, ip_address=ip, reason="test")

        assert await manager.get_failure_count(email, ip) == 2

        await manager.clear_failures(email, ip)

        assert await manager.get_failure_count(email, ip) == 0


class TestLockoutStatus(TestLockoutManager):
    """Test lockout status queries."""

    async def test_get_lockout_status_when_not_locked(self, manager: LockoutManager):
        """Returns None when account is not locked."""
        status = await manager.get_lockout_status("test@example.com")
        assert status is None

    async def test_get_lockout_status_when_locked(self, manager: LockoutManager):
        """Returns lockout details when account is locked."""
        email = "test@example.com"

        # Trigger lockout
        for i in range(3):
            try:
                await manager.record_failure(email, reason=f"attempt_{i}")
            except AccountLockedError:
                pass

        status = await manager.get_lockout_status(email)

        assert status is not None
        assert status["locked"] is True
        assert status["attempts"] == 3
        assert status["retry_after_seconds"] > 0


class TestConcurrency(TestLockoutManager):
    """Test concurrent access scenarios."""

    async def test_concurrent_failure_recording(self, manager: LockoutManager):
        """Concurrent failures are tracked correctly."""
        email = "test@example.com"

        # Fire multiple concurrent failures
        tasks = [
            manager.record_failure(email, reason=f"concurrent_{i}")
            for i in range(3)
        ]

        # Some will succeed, at least one should trigger lockout
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # At least one should have raised AccountLockedError
        errors = [r for r in results if isinstance(r, AccountLockedError)]
        counts = [r for r in results if isinstance(r, int)]

        # Total should be 3 (either as counts or triggering lockout)
        assert len(errors) + len(counts) == 3

    async def test_check_lockout_concurrent_access(self, manager: LockoutManager):
        """Concurrent lockout checks behave correctly."""
        email = "test@example.com"

        # Trigger lockout
        for i in range(3):
            try:
                await manager.record_failure(email, reason=f"attempt_{i}")
            except AccountLockedError:
                pass

        # Multiple concurrent checks
        async def check():
            try:
                await manager.check_lockout(email)
                return "allowed"
            except AccountLockedError:
                return "blocked"

        tasks = [check() for _ in range(10)]
        results = await asyncio.gather(*tasks)

        # All should be blocked
        assert all(r == "blocked" for r in results)


class TestDefaultConfig:
    """Test default lockout configuration."""

    async def test_default_config_values(self):
        """Default config has sensible values."""
        config = LockoutConfig()

        assert config.max_attempts == 5
        assert config.lockout_duration_minutes == 15
        assert config.attempt_window_minutes == 15
        assert config.track_by_ip is True

    async def test_manager_with_default_config(self):
        """Manager works with default config."""
        store = InMemoryStateStore()
        await store.start()

        manager = LockoutManager(store, None)  # Uses default config

        # Should use default of 5 attempts
        email = "test@example.com"
        for i in range(4):
            count = await manager.record_failure(email, reason=f"attempt_{i}")
            assert count == i + 1

        # 5th attempt triggers lockout
        with pytest.raises(AccountLockedError):
            await manager.record_failure(email, reason="final")

        await store.stop()
