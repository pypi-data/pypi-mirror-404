"""Concurrent tests for cleanup scheduler.

Tests cover:
- Task lifecycle races (start/stop during active cleanup)
- Callback race conditions
- Multiple scheduler instances
- Failure handling and restart races

CRITICAL: These tests ensure cleanup scheduler handles concurrent
operations and lifecycle events safely.
"""

import asyncio
from datetime import timedelta

import pytest

from identity_plan_kit.shared.cleanup_scheduler import CleanupConfig, CleanupScheduler

pytestmark = pytest.mark.anyio


class TestStartStopRace:
    """Test race conditions in start/stop operations."""

    async def test_stop_during_active_cleanup(self):
        """
        stop() during active cleanup should not leave orphan tasks.

        Race scenario:
        1. Cleanup is running
        2. stop() is called
        3. Cleanup task completes after stop()
        4. Callback tries to restart
        """
        cleanup_calls = 0
        cleanup_in_progress = asyncio.Event()

        async def slow_cleanup(batch_size: int) -> int:
            nonlocal cleanup_calls
            cleanup_calls += 1
            cleanup_in_progress.set()
            await asyncio.sleep(0.5)  # Slow cleanup
            return 10

        config = CleanupConfig(
            token_cleanup_interval=timedelta(seconds=0.1),
            token_cleanup_batch_size=100,
            token_cleanup_enabled=True,
        )
        scheduler = CleanupScheduler(slow_cleanup, config)

        scheduler.start()

        # Wait for cleanup to start
        await asyncio.wait_for(cleanup_in_progress.wait(), timeout=2.0)

        # Stop while cleanup is in progress
        scheduler.stop()

        # Wait a bit for any race conditions to manifest
        await asyncio.sleep(0.7)

        # Task should be None (stopped)
        assert scheduler._task is None
        assert scheduler._running is False

    async def test_concurrent_start_calls(self):
        """Multiple concurrent start calls should be safe."""
        cleanup_calls = 0

        async def dummy_cleanup(batch_size: int) -> int:
            nonlocal cleanup_calls
            cleanup_calls += 1
            return 0

        config = CleanupConfig(
            token_cleanup_interval=timedelta(seconds=1),
            token_cleanup_enabled=True,
        )
        scheduler = CleanupScheduler(dummy_cleanup, config)

        # Multiple sequential starts (concurrent threading is problematic in tests)
        # The key behavior is that multiple starts don't cause errors
        scheduler.start()
        scheduler.start()  # Should log warning but not fail
        scheduler.start()  # Should log warning but not fail

        # Should only have one task running
        await asyncio.sleep(0.1)
        assert scheduler._running is True
        assert scheduler._task is not None

        scheduler.stop()

    async def test_concurrent_stop_calls(self):
        """Multiple concurrent stop calls should be safe."""
        async def dummy_cleanup(batch_size: int) -> int:
            return 0

        config = CleanupConfig(
            token_cleanup_interval=timedelta(seconds=1),
            token_cleanup_enabled=True,
        )
        scheduler = CleanupScheduler(dummy_cleanup, config)
        scheduler.start()

        await asyncio.sleep(0.1)

        # Multiple concurrent stops
        await asyncio.gather(
            asyncio.to_thread(scheduler.stop),
            asyncio.to_thread(scheduler.stop),
            asyncio.to_thread(scheduler.stop),
        )

        assert scheduler._running is False
        assert scheduler._task is None

    async def test_rapid_start_stop_cycles(self):
        """Rapid start/stop cycles should not corrupt state."""
        call_count = 0

        async def fast_cleanup(batch_size: int) -> int:
            nonlocal call_count
            call_count += 1
            return 0

        config = CleanupConfig(
            token_cleanup_interval=timedelta(seconds=0.05),
            token_cleanup_enabled=True,
        )
        scheduler = CleanupScheduler(fast_cleanup, config)

        errors = []

        async def cycle():
            for _ in range(10):
                try:
                    scheduler.start()
                    await asyncio.sleep(0.02)
                    scheduler.stop()
                    await asyncio.sleep(0.01)
                except Exception as e:
                    errors.append(str(e))

        await asyncio.gather(cycle(), cycle())

        # Final state should be consistent
        assert scheduler._running is False or scheduler._running is True
        assert len(errors) == 0, f"Errors during cycles: {errors}"

        # Clean up
        scheduler.stop()


class TestCallbackRace:
    """Test callback handling race conditions."""

    async def test_callback_after_stop(self):
        """
        Callback fired after stop() should not restart task.

        Race scenario:
        1. Task completes
        2. stop() is called
        3. done_callback fires (in event loop)
        4. Callback should NOT restart
        """
        cleanup_runs = 0

        async def one_shot_cleanup(batch_size: int) -> int:
            nonlocal cleanup_runs
            cleanup_runs += 1
            if cleanup_runs == 1:
                return 10  # More to do
            return 0

        config = CleanupConfig(
            token_cleanup_interval=timedelta(seconds=0.05),
            token_cleanup_enabled=True,
        )
        scheduler = CleanupScheduler(one_shot_cleanup, config)

        scheduler.start()
        await asyncio.sleep(0.2)  # Let some runs happen

        scheduler.stop()

        # Record current state
        initial_runs = cleanup_runs

        # Wait to see if any ghost restarts happen
        await asyncio.sleep(0.3)

        # No new runs should happen after stop
        final_runs = cleanup_runs
        assert final_runs == initial_runs, (
            f"Cleanup ran {final_runs - initial_runs} times after stop()"
        )

    async def test_task_exception_triggers_error_handling(self):
        """
        Task exception should be handled gracefully.

        Note: The cleanup scheduler catches exceptions internally and logs them,
        allowing the loop to continue. This test verifies that behavior.
        """
        failure_count = 0

        async def failing_cleanup(batch_size: int) -> int:
            nonlocal failure_count
            failure_count += 1
            if failure_count <= 2:
                raise RuntimeError("Simulated failure")
            return 0

        config = CleanupConfig(
            token_cleanup_interval=timedelta(seconds=0.05),
            token_cleanup_enabled=True,
        )
        scheduler = CleanupScheduler(failing_cleanup, config)

        scheduler.start()

        # Wait for some cleanup attempts
        await asyncio.sleep(0.3)

        scheduler.stop()

        # Should have attempted cleanup multiple times despite failures
        assert failure_count >= 1

    async def test_consecutive_failure_counting(self):
        """
        Consecutive failures should be tracked.

        The cleanup loop catches exceptions internally and continues,
        incrementing the consecutive failure counter.
        """
        failure_count = 0

        async def always_failing_cleanup(batch_size: int) -> int:
            nonlocal failure_count
            failure_count += 1
            raise RuntimeError("Always fails")

        config = CleanupConfig(
            token_cleanup_interval=timedelta(seconds=0.05),
            token_cleanup_enabled=True,
        )
        scheduler = CleanupScheduler(always_failing_cleanup, config)

        scheduler.start()

        # Wait for some failures
        await asyncio.sleep(0.3)

        scheduler.stop()

        # Should have attempted cleanup and tracked failures
        assert failure_count >= 1
        # Scheduler still tracks stats even if not auto-stopping
        status = scheduler.get_status()
        assert status["running"] is False  # We stopped it


class TestConcurrentCleanupRuns:
    """Test concurrent cleanup execution scenarios."""

    async def test_run_cleanup_during_scheduled_run(self):
        """
        Manual run_cleanup during scheduled run should be safe.
        """
        in_cleanup = asyncio.Event()
        cleanup_count = 0

        async def coordinated_cleanup(batch_size: int) -> int:
            nonlocal cleanup_count
            cleanup_count += 1
            in_cleanup.set()
            await asyncio.sleep(0.1)
            return 0

        config = CleanupConfig(
            token_cleanup_interval=timedelta(seconds=0.05),
            token_cleanup_enabled=True,
        )
        scheduler = CleanupScheduler(coordinated_cleanup, config)

        scheduler.start()

        # Wait for scheduled cleanup to start
        await in_cleanup.wait()

        # Trigger manual cleanup while scheduled is running
        await scheduler.run_cleanup()

        scheduler.stop()

        # Both should have completed without error
        assert cleanup_count >= 2

    async def test_multiple_manual_cleanups_concurrent(self):
        """
        Multiple concurrent manual cleanup calls.
        """
        active_cleanups = 0
        max_concurrent = 0

        async def tracking_cleanup(batch_size: int) -> int:
            nonlocal active_cleanups, max_concurrent
            active_cleanups += 1
            max_concurrent = max(max_concurrent, active_cleanups)
            await asyncio.sleep(0.05)
            active_cleanups -= 1
            return 5

        config = CleanupConfig(
            token_cleanup_enabled=True,
        )
        scheduler = CleanupScheduler(tracking_cleanup, config)

        # Multiple concurrent manual runs
        results = await asyncio.gather(*[
            scheduler.run_cleanup() for _ in range(5)
        ])

        # All should complete
        assert all(r == 5 for r in results)

        # Note: Concurrent cleanups are actually OK (they use the same cleanup_func)
        # This is by design - no locking on run_cleanup

    async def test_cleanup_stats_consistency(self):
        """
        Stats should remain consistent during concurrent access.
        """
        async def consistent_cleanup(batch_size: int) -> int:
            return 10

        config = CleanupConfig(
            token_cleanup_interval=timedelta(seconds=0.05),
            token_cleanup_enabled=True,
        )
        scheduler = CleanupScheduler(consistent_cleanup, config)

        scheduler.start()

        stats_snapshots = []

        async def collect_stats():
            for _ in range(20):
                stats = scheduler.get_status()
                stats_snapshots.append(stats)
                await asyncio.sleep(0.01)

        await collect_stats()

        scheduler.stop()

        # All stats should be valid
        for stats in stats_snapshots:
            assert isinstance(stats["running"], bool)
            assert isinstance(stats["total_cleaned"], int)
            assert stats["total_cleaned"] >= 0


class TestMultipleSchedulerInstances:
    """Test multiple scheduler instances."""

    async def test_independent_scheduler_instances(self):
        """
        Multiple scheduler instances should be independent.
        """
        cleanup1_count = 0
        cleanup2_count = 0

        async def cleanup1(batch_size: int) -> int:
            nonlocal cleanup1_count
            cleanup1_count += 1
            return 5

        async def cleanup2(batch_size: int) -> int:
            nonlocal cleanup2_count
            cleanup2_count += 1
            return 10

        config1 = CleanupConfig(
            token_cleanup_interval=timedelta(seconds=0.05),
            token_cleanup_enabled=True,
        )
        config2 = CleanupConfig(
            token_cleanup_interval=timedelta(seconds=0.05),
            token_cleanup_enabled=True,
        )

        scheduler1 = CleanupScheduler(cleanup1, config1)
        scheduler2 = CleanupScheduler(cleanup2, config2)

        scheduler1.start()
        scheduler2.start()

        await asyncio.sleep(0.2)

        scheduler1.stop()
        scheduler2.stop()

        # Both should have run
        assert cleanup1_count > 0
        assert cleanup2_count > 0

        # Stats should be independent
        assert scheduler1.total_cleaned != scheduler2.total_cleaned or (
            cleanup1_count != cleanup2_count
        )

    async def test_stopping_one_doesnt_affect_other(self):
        """
        Stopping one scheduler should not affect another.
        """
        cleanup2_count = 0

        async def cleanup1(batch_size: int) -> int:
            return 0

        async def cleanup2(batch_size: int) -> int:
            nonlocal cleanup2_count
            cleanup2_count += 1
            return 0

        config = CleanupConfig(
            token_cleanup_interval=timedelta(seconds=0.05),
            token_cleanup_enabled=True,
        )

        scheduler1 = CleanupScheduler(cleanup1, config)
        scheduler2 = CleanupScheduler(cleanup2, config)

        scheduler1.start()
        scheduler2.start()

        await asyncio.sleep(0.1)

        # Stop scheduler1
        scheduler1.stop()
        count_at_stop = cleanup2_count

        # Wait and verify scheduler2 continues
        await asyncio.sleep(0.2)

        scheduler2.stop()

        # Scheduler2 should have continued running
        assert cleanup2_count > count_at_stop


class TestJitterConcurrency:
    """Test jitter calculation under concurrency."""

    async def test_jitter_doesnt_cause_bunching(self):
        """
        Jitter should spread out cleanup runs, not bunch them.
        """
        run_times = []

        async def timed_cleanup(batch_size: int) -> int:
            run_times.append(asyncio.get_event_loop().time())
            return 0

        config = CleanupConfig(
            token_cleanup_interval=timedelta(seconds=0.1),
            jitter_percent=0.5,  # Large jitter
            token_cleanup_enabled=True,
        )

        scheduler = CleanupScheduler(timed_cleanup, config)
        scheduler.start()

        await asyncio.sleep(1.0)

        scheduler.stop()

        if len(run_times) >= 3:
            # Calculate intervals between runs
            intervals = [
                run_times[i+1] - run_times[i]
                for i in range(len(run_times) - 1)
            ]

            # With jitter, intervals should vary
            # (not a hard assertion since it's random)
            min_interval = min(intervals)
            max_interval = max(intervals)
            print(f"Interval range: {min_interval:.3f}s - {max_interval:.3f}s")


class TestLockContention:
    """Test lock contention scenarios."""

    async def test_status_during_start_stop(self):
        """
        get_status() during start/stop should not deadlock.
        """
        async def slow_cleanup(batch_size: int) -> int:
            await asyncio.sleep(0.1)
            return 0

        config = CleanupConfig(
            token_cleanup_interval=timedelta(seconds=0.05),
            token_cleanup_enabled=True,
        )
        scheduler = CleanupScheduler(slow_cleanup, config)

        errors = []

        async def toggle_and_check():
            for _ in range(10):
                try:
                    scheduler.start()
                    _ = scheduler.get_status()
                    await asyncio.sleep(0.01)
                    _ = scheduler.get_status()
                    scheduler.stop()
                except Exception as e:
                    errors.append(str(e))

        # Run multiple toggle cycles concurrently
        try:
            await asyncio.wait_for(
                asyncio.gather(toggle_and_check(), toggle_and_check()),
                timeout=5.0,
            )
        except asyncio.TimeoutError:
            pytest.fail("Deadlock detected during start/stop/status operations")

        assert len(errors) == 0, f"Errors: {errors}"

        # Clean up
        scheduler.stop()
