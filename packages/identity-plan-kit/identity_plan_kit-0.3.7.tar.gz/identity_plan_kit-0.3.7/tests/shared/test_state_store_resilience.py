"""Tests for Redis state store resilience features.

Tests cover:
- Circuit breaker pattern
- Retry logic with exponential backoff
- Timeout handling
- Graceful degradation
"""

import asyncio
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Skip all tests in this module if redis is not available
pytest.importorskip("redis", reason="Redis package not installed")

from identity_plan_kit.shared.constants import (
    REDIS_RETRY_ATTEMPTS,
    REDIS_RETRY_BASE_DELAY,
    REDIS_SOCKET_CONNECT_TIMEOUT,
    REDIS_SOCKET_TIMEOUT,
)
from identity_plan_kit.shared.state_store import (
    RedisCircuitState,
    RedisStateStore,
)


@pytest.fixture
def redis_store():
    """Create a Redis state store for testing."""
    return RedisStateStore(
        redis_url="redis://localhost:6379/0",
        key_prefix="test:",
        socket_timeout=1.0,
        socket_connect_timeout=1.0,
    )


class TestRedisCircuitBreaker:
    """Tests for circuit breaker pattern in Redis state store."""

    async def test_circuit_starts_closed(self, redis_store: RedisStateStore):
        """Circuit breaker should start in CLOSED state."""
        assert redis_store._circuit_state == RedisCircuitState.CLOSED
        assert redis_store._circuit_failures == 0

    async def test_circuit_allows_requests_when_closed(self, redis_store: RedisStateStore):
        """Requests should be allowed when circuit is closed."""
        allowed = await redis_store._check_circuit()
        assert allowed is True

    async def test_circuit_opens_after_threshold_failures(self, redis_store: RedisStateStore):
        """Circuit should open after CIRCUIT_FAILURE_THRESHOLD failures."""
        # Record failures up to threshold
        for _ in range(redis_store.CIRCUIT_FAILURE_THRESHOLD):
            await redis_store._record_failure()

        assert redis_store._circuit_state == RedisCircuitState.OPEN
        assert redis_store._circuit_opened_at is not None

    async def test_circuit_rejects_requests_when_open(self, redis_store: RedisStateStore):
        """Requests should be rejected when circuit is open."""
        # Force circuit open
        redis_store._circuit_state = RedisCircuitState.OPEN
        redis_store._circuit_opened_at = datetime.now(UTC)

        allowed = await redis_store._check_circuit()
        assert allowed is False

    async def test_circuit_transitions_to_half_open_after_recovery_timeout(
        self, redis_store: RedisStateStore
    ):
        """Circuit should transition to HALF_OPEN after recovery timeout."""
        # Force circuit open with past timestamp
        redis_store._circuit_state = RedisCircuitState.OPEN
        redis_store._circuit_opened_at = datetime.now(UTC)

        # Simulate time passing (more than recovery timeout)
        from datetime import timedelta

        redis_store._circuit_opened_at = datetime.now(UTC) - timedelta(
            seconds=redis_store.CIRCUIT_RECOVERY_TIMEOUT + 1
        )

        # Check circuit - should transition to half-open
        allowed = await redis_store._check_circuit()
        assert allowed is True
        assert redis_store._circuit_state == RedisCircuitState.HALF_OPEN

    async def test_circuit_closes_after_successes_in_half_open(
        self, redis_store: RedisStateStore
    ):
        """Circuit should close after sufficient successes in HALF_OPEN state."""
        redis_store._circuit_state = RedisCircuitState.HALF_OPEN

        # Record enough successes to close circuit
        await redis_store._record_success()
        await redis_store._record_success()

        assert redis_store._circuit_state == RedisCircuitState.CLOSED
        assert redis_store._circuit_failures == 0

    async def test_circuit_reopens_on_failure_in_half_open(
        self, redis_store: RedisStateStore
    ):
        """Circuit should reopen on any failure in HALF_OPEN state."""
        redis_store._circuit_state = RedisCircuitState.HALF_OPEN

        await redis_store._record_failure()

        assert redis_store._circuit_state == RedisCircuitState.OPEN

    async def test_half_open_limits_concurrent_calls(self, redis_store: RedisStateStore):
        """Only limited calls should be allowed in HALF_OPEN state."""
        redis_store._circuit_state = RedisCircuitState.HALF_OPEN
        redis_store._circuit_half_open_calls = 0

        # Should allow up to CIRCUIT_HALF_OPEN_MAX_CALLS
        for i in range(redis_store.CIRCUIT_HALF_OPEN_MAX_CALLS):
            allowed = await redis_store._check_circuit()
            assert allowed is True, f"Call {i+1} should be allowed"

        # Next call should be rejected
        allowed = await redis_store._check_circuit()
        assert allowed is False


class TestRedisRetryLogic:
    """Tests for retry logic with exponential backoff."""

    async def test_successful_operation_returns_immediately(self, redis_store: RedisStateStore):
        """Successful operation should return without retries."""
        mock_func = AsyncMock(return_value="success")

        result = await redis_store._execute_with_retry("test_op", mock_func)

        assert result == "success"
        assert mock_func.call_count == 1

    async def test_retries_on_connection_error(self, redis_store: RedisStateStore):
        """Should retry on Redis connection errors."""
        # Import redis for exception types
        try:
            import redis.asyncio as redis_lib

            mock_func = AsyncMock(
                side_effect=[
                    redis_lib.ConnectionError("Connection refused"),
                    redis_lib.ConnectionError("Connection refused"),
                    "success",
                ]
            )

            result = await redis_store._execute_with_retry("test_op", mock_func)

            assert result == "success"
            assert mock_func.call_count == 3
        except ImportError:
            pytest.skip("Redis not installed")

    async def test_gives_up_after_max_retries(self, redis_store: RedisStateStore):
        """Should give up after REDIS_RETRY_ATTEMPTS retries."""
        try:
            import redis.asyncio as redis_lib

            mock_func = AsyncMock(side_effect=redis_lib.ConnectionError("Connection refused"))

            with pytest.raises(redis_lib.ConnectionError):
                await redis_store._execute_with_retry("test_op", mock_func)

            assert mock_func.call_count == REDIS_RETRY_ATTEMPTS
        except ImportError:
            pytest.skip("Redis not installed")

    async def test_records_failure_on_each_retry(self, redis_store: RedisStateStore):
        """Should record circuit breaker failure on each retry."""
        try:
            import redis.asyncio as redis_lib

            mock_func = AsyncMock(side_effect=redis_lib.ConnectionError("Connection refused"))

            try:
                await redis_store._execute_with_retry("test_op", mock_func)
            except redis_lib.ConnectionError:
                pass

            # Should have recorded REDIS_RETRY_ATTEMPTS failures
            assert redis_store._circuit_failures == REDIS_RETRY_ATTEMPTS
        except ImportError:
            pytest.skip("Redis not installed")

    async def test_records_success_on_successful_operation(self, redis_store: RedisStateStore):
        """Should record circuit breaker success on successful operation."""
        redis_store._circuit_state = RedisCircuitState.HALF_OPEN

        mock_func = AsyncMock(return_value="success")

        await redis_store._execute_with_retry("test_op", mock_func)

        assert redis_store._circuit_successes >= 1

    async def test_circuit_breaker_rejects_during_open(self, redis_store: RedisStateStore):
        """Should reject operations when circuit is open."""
        redis_store._circuit_state = RedisCircuitState.OPEN
        redis_store._circuit_opened_at = datetime.now(UTC)

        mock_func = AsyncMock(return_value="success")

        with pytest.raises(RuntimeError, match="circuit breaker is open"):
            await redis_store._execute_with_retry("test_op", mock_func)

        # Function should never be called
        mock_func.assert_not_called()


class TestRedisGracefulDegradation:
    """Tests for graceful degradation when Redis is unavailable."""

    async def test_get_returns_none_when_circuit_open(self, redis_store: RedisStateStore):
        """get() should return None when circuit is open."""
        redis_store._circuit_state = RedisCircuitState.OPEN
        redis_store._circuit_opened_at = datetime.now(UTC)
        redis_store._client = MagicMock()  # Simulate connected client

        result = await redis_store.get("test_key")

        assert result is None

    async def test_delete_returns_false_when_circuit_open(self, redis_store: RedisStateStore):
        """delete() should return False when circuit is open."""
        redis_store._circuit_state = RedisCircuitState.OPEN
        redis_store._circuit_opened_at = datetime.now(UTC)
        redis_store._client = MagicMock()

        result = await redis_store.delete("test_key")

        assert result is False

    async def test_exists_returns_false_when_circuit_open(self, redis_store: RedisStateStore):
        """exists() should return False when circuit is open."""
        redis_store._circuit_state = RedisCircuitState.OPEN
        redis_store._circuit_opened_at = datetime.now(UTC)
        redis_store._client = MagicMock()

        result = await redis_store.exists("test_key")

        assert result is False

    async def test_get_and_delete_returns_none_when_circuit_open(
        self, redis_store: RedisStateStore
    ):
        """get_and_delete() should return None when circuit is open."""
        redis_store._circuit_state = RedisCircuitState.OPEN
        redis_store._circuit_opened_at = datetime.now(UTC)
        redis_store._client = MagicMock()

        result = await redis_store.get_and_delete("test_key")

        assert result is None


class TestRedisTimeoutConfiguration:
    """Tests for Redis timeout configuration."""

    def test_default_timeouts(self):
        """Should have default timeout values."""
        store = RedisStateStore(redis_url="redis://localhost:6379/0")

        assert store._socket_timeout == REDIS_SOCKET_TIMEOUT
        assert store._socket_connect_timeout == REDIS_SOCKET_CONNECT_TIMEOUT

    def test_custom_timeouts(self):
        """Should accept custom timeout values."""
        store = RedisStateStore(
            redis_url="redis://localhost:6379/0",
            socket_timeout=10.0,
            socket_connect_timeout=15.0,
        )

        assert store._socket_timeout == 10.0
        assert store._socket_connect_timeout == 15.0


class TestConcurrentCircuitBreakerAccess:
    """Tests for concurrent access to circuit breaker."""

    async def test_concurrent_failure_recording(self, redis_store: RedisStateStore):
        """Multiple concurrent failures should be recorded correctly."""

        async def record_failure():
            await redis_store._record_failure()

        # Record failures concurrently
        await asyncio.gather(*[record_failure() for _ in range(10)])

        # All failures should be recorded
        assert redis_store._circuit_failures == 10

    async def test_concurrent_success_recording(self, redis_store: RedisStateStore):
        """Multiple concurrent successes should be recorded correctly."""
        redis_store._circuit_state = RedisCircuitState.HALF_OPEN

        async def record_success():
            await redis_store._record_success()

        # Record successes concurrently
        await asyncio.gather(*[record_success() for _ in range(5)])

        # All successes should be recorded
        assert redis_store._circuit_successes == 5

    async def test_concurrent_circuit_checks(self, redis_store: RedisStateStore):
        """Multiple concurrent circuit checks should be thread-safe."""

        async def check_circuit():
            return await redis_store._check_circuit()

        # Check circuit concurrently
        results = await asyncio.gather(*[check_circuit() for _ in range(20)])

        # All should return True (circuit is closed)
        assert all(results)
