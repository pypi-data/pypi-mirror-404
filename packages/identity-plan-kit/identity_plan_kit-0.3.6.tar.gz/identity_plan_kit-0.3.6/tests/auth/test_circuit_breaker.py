"""Tests for circuit breaker (P3 resilience fix)."""

import asyncio

import pytest

from identity_plan_kit.shared.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerError,
    CircuitState,
)

pytestmark = pytest.mark.anyio


class TestCircuitBreaker:
    """Test suite for circuit breaker pattern."""

    @pytest.fixture
    def breaker(self) -> CircuitBreaker:
        """Create a circuit breaker for testing."""
        return CircuitBreaker(
            name="test_breaker",
            failure_threshold=3,
            recovery_timeout=1.0,  # Short timeout for tests
            half_open_max_calls=2,
            success_threshold=2,
        )

    async def test_initial_state_is_closed(self, breaker: CircuitBreaker):
        """Test that circuit starts in closed state."""
        assert breaker.state == CircuitState.CLOSED

    async def test_successful_calls_keep_circuit_closed(self, breaker: CircuitBreaker):
        """Test that successful calls don't trip the circuit."""

        @breaker.call
        async def successful_operation():
            return "success"

        for _ in range(5):
            result = await successful_operation()
            assert result == "success"

        assert breaker.state == CircuitState.CLOSED
        assert breaker.stats.successes >= 5

    async def test_failures_trip_circuit(self, breaker: CircuitBreaker):
        """Test that failures above threshold open the circuit."""

        @breaker.call
        async def failing_operation():
            raise ValueError("Simulated failure")

        # Trigger failures up to threshold
        for _ in range(3):
            with pytest.raises(ValueError):
                await failing_operation()

        # Circuit should be open after 3 failures
        assert breaker.state == CircuitState.OPEN

    async def test_open_circuit_rejects_requests(self, breaker: CircuitBreaker):
        """Test that open circuit rejects requests immediately."""

        @breaker.call
        async def failing_operation():
            raise ValueError("Simulated failure")

        # Trip the circuit
        for _ in range(3):
            with pytest.raises(ValueError):
                await failing_operation()

        # Now requests should be rejected
        with pytest.raises(CircuitBreakerError) as exc_info:
            await failing_operation()

        assert "test_breaker" in str(exc_info.value)
        assert exc_info.value.retry_after > 0

    async def test_circuit_transitions_to_half_open(self, breaker: CircuitBreaker):
        """Test that circuit goes to half-open after recovery timeout."""

        @breaker.call
        async def failing_operation():
            raise ValueError("Simulated failure")

        # Trip the circuit
        for _ in range(3):
            with pytest.raises(ValueError):
                await failing_operation()

        assert breaker.state == CircuitState.OPEN

        # Wait for recovery timeout
        await asyncio.sleep(1.5)

        # Next call should be allowed (half-open)
        # The call itself will fail, but it should be attempted
        with pytest.raises(ValueError):
            await failing_operation()

        # After failure in half-open, goes back to open
        assert breaker.state == CircuitState.OPEN

    async def test_half_open_success_closes_circuit(self, breaker: CircuitBreaker):
        """Test that successful calls in half-open close the circuit."""
        call_count = 0

        @breaker.call
        async def flaky_operation():
            nonlocal call_count
            call_count += 1
            # Fail first 3 times, then succeed
            if call_count <= 3:
                raise ValueError("Simulated failure")
            return "success"

        # Trip the circuit with 3 failures
        for _ in range(3):
            with pytest.raises(ValueError):
                await flaky_operation()

        assert breaker.state == CircuitState.OPEN

        # Wait for recovery timeout
        await asyncio.sleep(1.5)

        # Now calls succeed
        result1 = await flaky_operation()
        assert result1 == "success"

        result2 = await flaky_operation()
        assert result2 == "success"

        # After 2 successes, circuit should be closed
        assert breaker.state == CircuitState.CLOSED

    async def test_excluded_exceptions_dont_count(self, breaker: CircuitBreaker):
        """Test that excluded exceptions don't count as failures."""
        # Create breaker that excludes ValueError
        breaker_with_exclusion = CircuitBreaker(
            name="test_exclusion",
            failure_threshold=3,
            recovery_timeout=1.0,
            exclude_exceptions=(ValueError,),
        )

        @breaker_with_exclusion.call
        async def operation_with_excluded_error():
            raise ValueError("Expected error")

        # These shouldn't trip the circuit
        for _ in range(5):
            with pytest.raises(ValueError):
                await operation_with_excluded_error()

        # Circuit should still be closed
        assert breaker_with_exclusion.state == CircuitState.CLOSED
        assert breaker_with_exclusion.stats.failures == 0
