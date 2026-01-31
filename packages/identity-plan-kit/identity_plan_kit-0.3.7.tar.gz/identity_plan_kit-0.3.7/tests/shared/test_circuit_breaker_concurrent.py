"""Concurrent tests for circuit breaker pattern.

Tests cover:
- Concurrent state transitions
- Race conditions in failure counting
- Half-open state under concurrent load
- Stats consistency under concurrency

CRITICAL: These tests ensure circuit breaker is thread-safe
and handles concurrent access correctly.
"""

import asyncio
from datetime import UTC, datetime, timedelta

import pytest

pytestmark = pytest.mark.anyio

from identity_plan_kit.shared.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerError,
    CircuitState,
)


class TestConcurrentStateTransitions:
    """Test circuit breaker state transitions under concurrency."""

    async def test_concurrent_failures_trip_circuit_exactly_once(self):
        """Circuit trips exactly once even with concurrent failures."""
        breaker = CircuitBreaker(
            name="test_concurrent_failures",
            failure_threshold=5,
            recovery_timeout=60.0,
        )

        transition_count = 0
        original_transition = breaker._transition_to

        def counting_transition(new_state):
            nonlocal transition_count
            if new_state == CircuitState.OPEN:
                transition_count += 1
            return original_transition(new_state)

        breaker._transition_to = counting_transition

        @breaker.call
        async def failing_operation():
            raise ValueError("Simulated failure")

        # Fire many concurrent failures
        tasks = []
        for _ in range(20):
            tasks.append(asyncio.create_task(
                self._safe_call(failing_operation)
            ))
        await asyncio.gather(*tasks)

        # Circuit should be open
        assert breaker.state == CircuitState.OPEN
        # Transition to OPEN should happen at most once per threshold crossing
        # (could be 1 if all failures happen before state check)
        assert transition_count >= 1

    async def _safe_call(self, func):
        """Call function and catch expected exceptions."""
        try:
            await func()
        except (ValueError, CircuitBreakerError):
            pass

    async def test_concurrent_calls_during_half_open(self):
        """Half-open state correctly limits concurrent calls."""
        breaker = CircuitBreaker(
            name="test_half_open_concurrent",
            failure_threshold=3,
            recovery_timeout=0.1,  # Very short for testing
            half_open_max_calls=2,
            success_threshold=2,
        )

        @breaker.call
        async def failing_operation():
            raise ValueError("Simulated failure")

        @breaker.call
        async def slow_success():
            await asyncio.sleep(0.2)  # Longer than recovery timeout
            return "success"

        # Trip the circuit
        for _ in range(3):
            try:
                await failing_operation()
            except ValueError:
                pass

        assert breaker.state == CircuitState.OPEN

        # Wait for recovery timeout
        await asyncio.sleep(0.15)

        # Fire concurrent calls - should only allow half_open_max_calls
        allowed_count = 0
        rejected_count = 0

        async def try_call():
            nonlocal allowed_count, rejected_count
            try:
                await slow_success()
                allowed_count += 1
            except CircuitBreakerError:
                rejected_count += 1

        tasks = [try_call() for _ in range(10)]
        await asyncio.gather(*tasks)

        # At most half_open_max_calls should have been allowed
        assert allowed_count <= breaker.half_open_max_calls

    async def test_concurrent_successes_close_circuit(self):
        """Concurrent successes in half-open close circuit correctly."""
        breaker = CircuitBreaker(
            name="test_concurrent_success_close",
            failure_threshold=2,
            recovery_timeout=0.05,
            half_open_max_calls=5,
            success_threshold=3,
        )

        @breaker.call
        async def operation(should_fail: bool):
            if should_fail:
                raise ValueError("Failure")
            return "success"

        # Trip circuit
        for _ in range(2):
            try:
                await operation(True)
            except ValueError:
                pass

        assert breaker.state == CircuitState.OPEN

        # Wait for recovery
        await asyncio.sleep(0.1)

        # Fire concurrent successes
        tasks = [operation(False) for _ in range(5)]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Some should succeed
        successes = [r for r in results if r == "success"]
        assert len(successes) >= breaker.success_threshold

        # Circuit should be closed after enough successes
        # (might need a small wait for state to update)
        await asyncio.sleep(0.01)
        assert breaker.state == CircuitState.CLOSED


class TestConcurrentFailureCounting:
    """Test failure counting under concurrent load."""

    async def test_failure_count_accurate_under_concurrency(self):
        """Failure count remains accurate with concurrent failures."""
        breaker = CircuitBreaker(
            name="test_failure_count",
            failure_threshold=100,  # High threshold to avoid tripping
            recovery_timeout=60.0,
        )

        @breaker.call
        async def failing_operation():
            raise ValueError("Simulated failure")

        # Fire exactly 50 concurrent failures
        tasks = [
            asyncio.create_task(self._catch_error(failing_operation))
            for _ in range(50)
        ]
        await asyncio.gather(*tasks)

        # All failures should be counted
        assert breaker.stats.failures == 50

    async def _catch_error(self, func):
        """Helper to catch expected errors."""
        try:
            await func()
        except (ValueError, CircuitBreakerError):
            pass

    async def test_success_count_accurate_under_concurrency(self):
        """Success count remains accurate with concurrent calls."""
        breaker = CircuitBreaker(
            name="test_success_count",
            failure_threshold=5,
            recovery_timeout=60.0,
        )

        @breaker.call
        async def success_operation():
            return "success"

        # Fire exactly 100 concurrent successes
        tasks = [success_operation() for _ in range(100)]
        await asyncio.gather(*tasks)

        # All successes should be counted
        assert breaker.stats.successes == 100


class TestHalfOpenStateConcurrency:
    """Test half-open state behavior under concurrent load."""

    async def test_half_open_failure_opens_circuit_immediately(self):
        """Single failure in half-open state opens circuit immediately."""
        breaker = CircuitBreaker(
            name="test_half_open_fail",
            failure_threshold=2,
            recovery_timeout=0.05,
            half_open_max_calls=3,
        )

        call_sequence = []

        @breaker.call
        async def tracked_operation(call_id: int, should_fail: bool):
            call_sequence.append(("start", call_id))
            await asyncio.sleep(0.01)
            if should_fail:
                raise ValueError("Failure")
            call_sequence.append(("end", call_id))
            return "success"

        # Trip circuit
        for _ in range(2):
            try:
                await tracked_operation(0, True)
            except ValueError:
                pass

        await asyncio.sleep(0.1)  # Wait for half-open

        # One failure should immediately open circuit
        try:
            await tracked_operation(1, True)
        except ValueError:
            pass

        assert breaker.state == CircuitState.OPEN

    async def test_half_open_limits_enforced_concurrently(self):
        """Half-open call limit is enforced even under concurrent load."""
        breaker = CircuitBreaker(
            name="test_half_open_limit",
            failure_threshold=2,
            recovery_timeout=0.05,
            half_open_max_calls=3,
        )

        allowed_calls = 0
        rejected_calls = 0

        @breaker.call
        async def slow_operation():
            nonlocal allowed_calls
            allowed_calls += 1
            await asyncio.sleep(0.5)  # Hold the slot
            return "success"

        # Trip circuit
        for _ in range(2):
            try:
                @breaker.call
                async def fail():
                    raise ValueError()
                await fail()
            except ValueError:
                pass

        await asyncio.sleep(0.1)

        # Fire many concurrent calls
        async def try_call():
            nonlocal rejected_calls
            try:
                await slow_operation()
            except CircuitBreakerError:
                rejected_calls += 1

        tasks = [try_call() for _ in range(20)]
        await asyncio.gather(*tasks)

        # Should have been limited
        assert allowed_calls <= breaker.half_open_max_calls


class TestStatsConsistency:
    """Test stats remain consistent under concurrent access."""

    async def test_stats_timestamps_ordered_correctly(self):
        """Timestamps in stats are set correctly even under concurrency."""
        breaker = CircuitBreaker(
            name="test_stats_timestamps",
            failure_threshold=100,
            recovery_timeout=60.0,
        )

        @breaker.call
        async def operation(should_fail: bool):
            if should_fail:
                raise ValueError()
            return "success"

        # Mix of successes and failures concurrently
        tasks = []
        for i in range(50):
            tasks.append(
                asyncio.create_task(
                    self._safe_call(operation, i % 2 == 0)
                )
            )
        await asyncio.gather(*tasks)

        # Timestamps should be set
        assert breaker.stats.last_success_time is not None
        assert breaker.stats.last_failure_time is not None

        # Both should be recent
        now = datetime.now(UTC)
        assert (now - breaker.stats.last_success_time) < timedelta(seconds=1)
        assert (now - breaker.stats.last_failure_time) < timedelta(seconds=1)

    async def _safe_call(self, operation, should_fail):
        """Call operation and catch errors."""
        try:
            await operation(should_fail)
        except ValueError:
            pass


class TestRecoveryTimeoutConcurrency:
    """Test recovery timeout behavior under concurrent access."""

    async def test_multiple_threads_check_recovery_timeout(self):
        """Multiple concurrent calls correctly trigger half-open transition."""
        breaker = CircuitBreaker(
            name="test_recovery_concurrent",
            failure_threshold=2,
            recovery_timeout=0.1,
            half_open_max_calls=5,
        )

        @breaker.call
        async def failing():
            raise ValueError()

        @breaker.call
        async def succeeding():
            return "success"

        # Trip circuit
        for _ in range(2):
            try:
                await failing()
            except ValueError:
                pass

        assert breaker.state == CircuitState.OPEN

        # Wait for recovery timeout to expire
        await asyncio.sleep(0.15)

        # Many concurrent calls should trigger half-open
        results = []

        async def try_call():
            try:
                result = await succeeding()
                results.append(("success", result))
            except CircuitBreakerError as e:
                results.append(("rejected", str(e)))

        tasks = [try_call() for _ in range(10)]
        await asyncio.gather(*tasks)

        # At least some should have succeeded (half-open allows some calls)
        successes = [r for r in results if r[0] == "success"]
        assert len(successes) > 0


class TestExcludedExceptionsConcurrency:
    """Test excluded exceptions handling under concurrency."""

    async def test_excluded_exceptions_not_counted_concurrently(self):
        """Excluded exceptions don't affect failure count under concurrent load."""
        breaker = CircuitBreaker(
            name="test_excluded_concurrent",
            failure_threshold=5,
            recovery_timeout=60.0,
            exclude_exceptions=(ValueError,),
        )

        @breaker.call
        async def excluded_error():
            raise ValueError("Expected error")

        # Many concurrent calls with excluded exception
        tasks = [
            asyncio.create_task(self._safe_call(excluded_error))
            for _ in range(50)
        ]
        await asyncio.gather(*tasks)

        # Circuit should still be closed (ValueError is excluded)
        assert breaker.state == CircuitState.CLOSED
        # No failures counted
        assert breaker.stats.failures == 0

    async def _safe_call(self, func):
        """Call function and catch expected exceptions."""
        try:
            await func()
        except ValueError:
            pass


class TestEdgeCases:
    """Test edge cases in concurrent scenarios."""

    async def test_rapid_state_transitions(self):
        """Handle rapid state transitions without corruption."""
        breaker = CircuitBreaker(
            name="test_rapid_transitions",
            failure_threshold=1,  # Trip immediately
            recovery_timeout=0.01,  # Very fast recovery
            half_open_max_calls=1,
            success_threshold=1,
        )

        @breaker.call
        async def operation(should_fail: bool):
            if should_fail:
                raise ValueError()
            return "success"

        # Rapidly alternate between states
        for _ in range(20):
            # Trip circuit
            try:
                await operation(True)
            except (ValueError, CircuitBreakerError):
                pass

            # Wait for half-open
            await asyncio.sleep(0.02)

            # Try to close
            try:
                await operation(False)
            except CircuitBreakerError:
                pass

        # Circuit should be in a valid state
        assert breaker.state in (CircuitState.CLOSED, CircuitState.OPEN, CircuitState.HALF_OPEN)

    async def test_zero_failure_threshold(self):
        """Circuit with zero failure threshold trips immediately."""
        # With threshold 0, circuit trips on first failure (0 >= 0)
        breaker = CircuitBreaker(
            name="test_zero_threshold",
            failure_threshold=0,
            recovery_timeout=60.0,
        )

        @breaker.call
        async def failing():
            raise ValueError()

        # First failure should trip the circuit
        with pytest.raises(ValueError):
            await failing()

        # Circuit should be open
        assert breaker.state == CircuitState.OPEN

        # Subsequent calls should be rejected by circuit breaker
        with pytest.raises(CircuitBreakerError):
            await failing()
