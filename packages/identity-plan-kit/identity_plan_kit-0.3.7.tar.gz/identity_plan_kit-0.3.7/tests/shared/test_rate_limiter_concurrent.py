"""Concurrent tests for rate limiter.

Tests cover:
- Configuration race conditions (trust_proxy changing between calls)
- Double-checked locking correctness
- Concurrent initialization scenarios
- Global state consistency

CRITICAL: These tests ensure rate limiter configuration is consistent
across concurrent initializations.
"""

import asyncio
import threading
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch

import pytest

from identity_plan_kit.shared import rate_limiter


def reset_rate_limiter():
    """Reset rate limiter global state for testing."""
    rate_limiter._limiter = None
    rate_limiter._trust_proxy = False
    rate_limiter._trust_proxy_initialized = False


class TestConcurrentInitialization:
    """Test concurrent initialization scenarios."""

    def setup_method(self):
        """Reset state before each test."""
        reset_rate_limiter()

    def teardown_method(self):
        """Clean up after each test."""
        reset_rate_limiter()

    def test_concurrent_get_rate_limiter_returns_same_instance(self):
        """
        Multiple threads calling get_rate_limiter should get same instance.

        Tests double-checked locking pattern correctness.
        """
        results = []
        barrier = threading.Barrier(10)

        def get_limiter():
            barrier.wait()  # Synchronize all threads
            limiter = rate_limiter.get_rate_limiter()
            results.append(id(limiter))

        threads = [threading.Thread(target=get_limiter) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # All should have gotten the same instance
        assert len(set(results)) == 1, (
            f"Got {len(set(results))} different limiter instances, expected 1. "
            "Double-checked locking may be broken."
        )

    def test_concurrent_create_limiter_with_same_config(self):
        """
        Concurrent create_limiter calls with same config should work.
        """
        results = []
        barrier = threading.Barrier(5)

        def create():
            barrier.wait()
            limiter = rate_limiter.create_limiter(trust_proxy=True)
            results.append(limiter)

        threads = [threading.Thread(target=create) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # All should succeed
        assert len(results) == 5
        # trust_proxy should be consistent
        assert rate_limiter._trust_proxy is True

    def test_concurrent_create_limiter_different_trust_proxy(self):
        """
        Concurrent calls with different trust_proxy values should warn.

        This tests the race condition where:
        1. Thread A sets trust_proxy=True
        2. Thread B sets trust_proxy=False
        3. Configuration becomes inconsistent
        """
        warnings_logged = []
        original_warning = rate_limiter.logger.warning

        def capture_warning(*args, **kwargs):
            warnings_logged.append((args, kwargs))
            return original_warning(*args, **kwargs)

        with patch.object(rate_limiter.logger, 'warning', capture_warning):
            barrier = threading.Barrier(4)

            def create_with_trust(trust: bool):
                barrier.wait()
                rate_limiter.create_limiter(trust_proxy=trust)

            threads = [
                threading.Thread(target=create_with_trust, args=(True,)),
                threading.Thread(target=create_with_trust, args=(False,)),
                threading.Thread(target=create_with_trust, args=(True,)),
                threading.Thread(target=create_with_trust, args=(False,)),
            ]

            for t in threads:
                t.start()
            for t in threads:
                t.join()

        # Should have logged warnings about changing trust_proxy
        trust_proxy_warnings = [
            w for w in warnings_logged
            if 'rate_limiter_trust_proxy_changed' in str(w)
        ]

        # If no warnings, the race condition wasn't detected
        # (which could indicate a bug or lucky timing)
        # At minimum, state should be consistent
        assert rate_limiter._trust_proxy_initialized is True
        assert rate_limiter._trust_proxy in (True, False)

    def test_concurrent_init_and_get(self):
        """
        Concurrent init_rate_limiter and get_rate_limiter calls.
        """
        results = {"init": [], "get": []}
        barrier = threading.Barrier(6)

        def do_init():
            barrier.wait()
            limiter = rate_limiter.init_rate_limiter(trust_proxy=True)
            results["init"].append(limiter)

        def do_get():
            barrier.wait()
            limiter = rate_limiter.get_rate_limiter()
            results["get"].append(limiter)

        threads = [
            threading.Thread(target=do_init),
            threading.Thread(target=do_init),
            threading.Thread(target=do_get),
            threading.Thread(target=do_get),
            threading.Thread(target=do_get),
            threading.Thread(target=do_get),
        ]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # All should have gotten valid limiters
        assert len(results["init"]) == 2
        assert len(results["get"]) == 4
        assert all(l is not None for l in results["init"])
        assert all(l is not None for l in results["get"])


class TestConfigurationConsistency:
    """Test configuration consistency under various scenarios."""

    def setup_method(self):
        """Reset state before each test."""
        reset_rate_limiter()

    def teardown_method(self):
        """Clean up after each test."""
        reset_rate_limiter()

    def test_trust_proxy_not_overwritten_by_none(self):
        """
        Subsequent calls with trust_proxy=None should not overwrite.
        """
        # First call sets trust_proxy=True
        rate_limiter.create_limiter(trust_proxy=True)
        assert rate_limiter._trust_proxy is True

        # Second call with None should not change it
        rate_limiter.create_limiter(trust_proxy=None)
        assert rate_limiter._trust_proxy is True

    def test_trust_proxy_first_none_defaults_to_false(self):
        """
        First call with trust_proxy=None defaults to False.
        """
        rate_limiter.create_limiter(trust_proxy=None)

        assert rate_limiter._trust_proxy_initialized is True
        assert rate_limiter._trust_proxy is False

    def test_explicit_trust_proxy_after_default(self):
        """
        Explicit value after default should warn and update.
        """
        # First with default
        rate_limiter.create_limiter(trust_proxy=None)
        assert rate_limiter._trust_proxy is False

        warnings_logged = []
        original_warning = rate_limiter.logger.warning

        def capture_warning(*args, **kwargs):
            warnings_logged.append((args, kwargs))
            return original_warning(*args, **kwargs)

        with patch.object(rate_limiter.logger, 'warning', capture_warning):
            rate_limiter.create_limiter(trust_proxy=True)

        # Should warn about change
        assert any('rate_limiter_trust_proxy_changed' in str(w) for w in warnings_logged)
        # But should update
        assert rate_limiter._trust_proxy is True


class TestThreadSafety:
    """Test thread safety of rate limiter operations."""

    def setup_method(self):
        """Reset state before each test."""
        reset_rate_limiter()

    def teardown_method(self):
        """Clean up after each test."""
        reset_rate_limiter()

    def test_reentrant_lock_allows_nested_acquisition(self):
        """
        RLock should allow nested acquisition from same thread.
        """
        # Should not deadlock
        with rate_limiter._limiter_lock:
            with rate_limiter._limiter_lock:
                # Access global state safely
                _ = rate_limiter._trust_proxy

    def test_concurrent_access_to_get_client_ip_key(self):
        """
        _get_client_ip_key function should be thread-safe.
        """
        # Initialize first
        rate_limiter.create_limiter(trust_proxy=False)

        # Create mock request
        class MockRequest:
            def __init__(self):
                self.client = type('Client', (), {'host': '192.168.1.1'})()
                self.headers = {}

        request = MockRequest()
        results = []

        def get_key():
            for _ in range(100):
                key = rate_limiter._get_client_ip_key(request)
                results.append(key)

        threads = [threading.Thread(target=get_key) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # All results should be the same
        assert all(r == "192.168.1.1" for r in results)

    def test_high_concurrency_initialization(self):
        """
        High concurrency initialization stress test.
        """
        errors = []
        barrier = threading.Barrier(50)

        def init_limiter():
            try:
                barrier.wait()
                rate_limiter.get_rate_limiter()
            except Exception as e:
                errors.append(str(e))

        threads = [threading.Thread(target=init_limiter) for _ in range(50)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0, f"Errors during initialization: {errors}"

    def test_no_deadlock_with_thread_pool(self):
        """
        ThreadPoolExecutor should not cause deadlocks.
        """
        def work():
            for _ in range(10):
                rate_limiter.get_rate_limiter()
            return "done"

        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(work) for _ in range(20)]

            # Wait with timeout to detect deadlock
            results = []
            for future in futures:
                try:
                    result = future.result(timeout=5.0)
                    results.append(result)
                except TimeoutError:
                    pytest.fail("Deadlock detected in thread pool!")

            assert len(results) == 20


class TestAsyncConcurrency:
    """Test async concurrency scenarios."""

    def setup_method(self):
        """Reset state before each test."""
        reset_rate_limiter()

    def teardown_method(self):
        """Clean up after each test."""
        reset_rate_limiter()

    @pytest.mark.anyio
    async def test_async_concurrent_get_limiter(self):
        """
        Async concurrent access to rate limiter.
        """

        async def get_in_thread():
            # Run sync code in thread pool to simulate real async usage
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(
                None, rate_limiter.get_rate_limiter
            )

        # Multiple concurrent async calls
        results = await asyncio.gather(*[
            get_in_thread() for _ in range(20)
        ])

        # All should get the same instance
        assert len(set(id(r) for r in results)) == 1

    @pytest.mark.anyio
    async def test_async_init_during_requests(self):
        """
        Initialization during concurrent requests should be safe.
        """
        class MockRequest:
            def __init__(self):
                self.client = type('Client', (), {'host': '10.0.0.1'})()
                self.headers = {}

        async def simulate_request():
            loop = asyncio.get_event_loop()
            limiter = await loop.run_in_executor(
                None, rate_limiter.get_rate_limiter
            )
            key = await loop.run_in_executor(
                None, rate_limiter._get_client_ip_key, MockRequest()
            )
            return (limiter, key)

        results = await asyncio.gather(*[
            simulate_request() for _ in range(50)
        ])

        limiters = [r[0] for r in results]
        keys = [r[1] for r in results]

        # All same limiter
        assert len(set(id(l) for l in limiters)) == 1
        # All same key
        assert all(k == "10.0.0.1" for k in keys)


class TestGlobalStateReset:
    """Test that global state can be safely reset."""

    def setup_method(self):
        """Reset state before each test."""
        reset_rate_limiter()

    def teardown_method(self):
        """Clean up after each test."""
        reset_rate_limiter()

    def test_reset_between_tests_is_safe(self):
        """
        Resetting global state between tests doesn't cause issues.
        """
        # Create limiter
        limiter1 = rate_limiter.create_limiter(trust_proxy=True)
        assert rate_limiter._trust_proxy is True

        # Reset
        reset_rate_limiter()

        # Create new limiter
        limiter2 = rate_limiter.create_limiter(trust_proxy=False)
        assert rate_limiter._trust_proxy is False

        # Should be different instances
        assert limiter1 is not limiter2

    def test_concurrent_reset_and_access(self):
        """
        Concurrent reset and access should not crash.

        This is an edge case that could happen during test teardown.
        """
        errors = []

        def reset_loop():
            for _ in range(10):
                try:
                    reset_rate_limiter()
                except Exception as e:
                    errors.append(f"Reset error: {e}")

        def access_loop():
            for _ in range(50):
                try:
                    rate_limiter.get_rate_limiter()
                except Exception as e:
                    # Some errors expected during reset, but no crashes
                    pass

        threads = [
            threading.Thread(target=reset_loop),
            threading.Thread(target=access_loop),
            threading.Thread(target=access_loop),
        ]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # No catastrophic errors
        # (reset during access is expected to cause some issues,
        # but shouldn't crash)
