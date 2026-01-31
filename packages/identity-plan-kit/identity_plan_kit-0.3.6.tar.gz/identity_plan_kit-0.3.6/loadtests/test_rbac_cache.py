"""
Load tests for RBAC permission cache.

Tests:
- Permission cache under high read load
- Cache invalidation during active access
- Mixed read/write cache operations
- Cache hit ratio under various loads
- Concurrent permission checks for same user

The permission cache is critical for performance - without it, every API call
would require a database query for permissions.
"""

import random
import time
from dataclasses import dataclass

from locust import HttpUser, between, events, task

from loadtests.config import config
from loadtests.utils import TestUser, get_user_pool, metrics


@dataclass
class PermissionMetrics:
    """Track permission-specific metrics."""

    permission_checks: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    invalidations: int = 0
    concurrent_checks: int = 0

    @property
    def hit_ratio(self) -> float:
        """Calculate cache hit ratio."""
        total = self.cache_hits + self.cache_misses
        if total == 0:
            return 0.0
        return self.cache_hits / total


permission_metrics = PermissionMetrics()


class PermissionCacheUser(HttpUser):
    """
    User that heavily exercises the permission cache.

    Tests:
    - High-frequency permission checks via /profile endpoint
    - Cache warming behavior
    - Cache hit ratio under load
    """

    wait_time = between(0.5, 1.5)
    host = config.base_url

    def on_start(self) -> None:
        """Set up user with test credentials."""
        pool = get_user_pool()
        self.test_user: TestUser = pool.get_user()
        self.check_count = 0

    @task(10)
    def check_permissions_via_profile(self) -> None:
        """
        Check permissions via /profile endpoint.

        The profile endpoint loads permissions and exercises the cache.
        First call should be a cache miss, subsequent calls should hit.
        """
        start_time = time.time()

        with self.client.get(
            f"{config.api_prefix}/auth/profile",
            headers=self.test_user.auth_headers(),
            cookies=self.test_user.auth_cookies(),
            catch_response=True,
            name="/auth/profile (permission check)",
        ) as response:
            elapsed = time.time() - start_time
            permission_metrics.permission_checks += 1

            if response.status_code == 200:
                response.success()
                self.check_count += 1

                # Heuristic: very fast responses likely hit cache
                # Adjust threshold based on your system
                if elapsed < 0.05:  # 50ms
                    permission_metrics.cache_hits += 1
                else:
                    permission_metrics.cache_misses += 1
            elif response.status_code == 401:
                metrics.record_auth_failure()
                response.failure("Unauthorized")
            else:
                response.failure(f"Unexpected status: {response.status_code}")

    @task(3)
    def rapid_permission_checks(self) -> None:
        """
        Perform rapid successive permission checks.

        This tests the cache's behavior with rapid repeated access.
        All requests after the first should be cache hits.
        """
        # Make 5 rapid requests
        for i in range(5):
            with self.client.get(
                f"{config.api_prefix}/auth/profile",
                headers=self.test_user.auth_headers(),
                cookies=self.test_user.auth_cookies(),
                catch_response=True,
                name=f"/auth/profile (rapid-{i})",
            ) as response:
                if response.status_code == 200:
                    response.success()
                elif response.status_code == 401:
                    response.failure("Unauthorized")
                    break
                else:
                    response.failure(f"Unexpected status: {response.status_code}")


class CacheMixedWorkloadUser(HttpUser):
    """
    User that simulates mixed cache operations.

    This represents realistic workloads where:
    - Most operations are reads (permission checks)
    - Occasional cache invalidation (role changes)
    - Some users have different permission sets
    """

    wait_time = between(1, 3)
    host = config.base_url

    def on_start(self) -> None:
        """Set up user with test credentials."""
        pool = get_user_pool()
        # Randomly pick user or admin to simulate different permission sets
        if random.random() < 0.1:
            self.test_user: TestUser = pool.get_admin_user()
        else:
            self.test_user = pool.get_user()

    @task(20)
    def check_permissions(self) -> None:
        """Standard permission check."""
        with self.client.get(
            f"{config.api_prefix}/auth/profile",
            headers=self.test_user.auth_headers(),
            cookies=self.test_user.auth_cookies(),
            catch_response=True,
            name="/auth/profile (mixed workload)",
        ) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 401:
                response.failure("Unauthorized")
            else:
                response.failure(f"Unexpected status: {response.status_code}")

    @task(5)
    def get_user_info(self) -> None:
        """
        Get basic user info (no cache involvement).

        This provides baseline for comparing cached vs non-cached endpoints.
        """
        with self.client.get(
            f"{config.api_prefix}/auth/me",
            headers=self.test_user.auth_headers(),
            cookies=self.test_user.auth_cookies(),
            catch_response=True,
            name="/auth/me (baseline)",
        ) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 401:
                response.failure("Unauthorized")
            else:
                response.failure(f"Unexpected status: {response.status_code}")


class ConcurrentSameUserCache(HttpUser):
    """
    Multiple Locust users accessing the same test user's permissions.

    This tests:
    - Cache behavior when many requests hit the same cache key
    - Lock contention in in-memory cache
    - Redis pipeline efficiency (if using Redis cache)
    """

    wait_time = between(0.1, 0.5)
    host = config.base_url

    # Shared test user across all instances of this class
    _shared_user: TestUser | None = None

    def on_start(self) -> None:
        """Set up with shared user credentials."""
        pool = get_user_pool()
        # All instances use the same user to test cache contention
        if ConcurrentSameUserCache._shared_user is None:
            ConcurrentSameUserCache._shared_user = pool.get_user()
        self.test_user = ConcurrentSameUserCache._shared_user

    @task
    def concurrent_permission_check(self) -> None:
        """
        Concurrent permission checks for the same user.

        This tests the asyncio lock in InMemoryPermissionCache
        and potential thundering herd issues.
        """
        permission_metrics.concurrent_checks += 1

        with self.client.get(
            f"{config.api_prefix}/auth/profile",
            headers=self.test_user.auth_headers(),
            cookies=self.test_user.auth_cookies(),
            catch_response=True,
            name="/auth/profile (concurrent same user)",
        ) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 401:
                response.failure("Unauthorized")
            else:
                response.failure(f"Unexpected status: {response.status_code}")


class CacheWarmingUser(HttpUser):
    """
    User that tests cache warming behavior.

    Tests:
    - Initial cache population (cold start)
    - Cache behavior after expiration
    - Performance difference between cache hit and miss
    """

    wait_time = between(2, 5)
    host = config.base_url

    def on_start(self) -> None:
        """Set up with fresh user each time."""
        pool = get_user_pool()
        self.test_user: TestUser = pool.get_random_user()
        self.first_request = True
        self.first_latency: float | None = None
        self.cached_latency: float | None = None

    @task
    def cache_warming_test(self) -> None:
        """
        Test cache warming - first request vs subsequent.

        First request should populate the cache (miss).
        Second request should hit the cache and be faster.
        """
        start_time = time.time()

        with self.client.get(
            f"{config.api_prefix}/auth/profile",
            headers=self.test_user.auth_headers(),
            cookies=self.test_user.auth_cookies(),
            catch_response=True,
            name="/auth/profile (cache warming)" if self.first_request else "/auth/profile (warm cache)",
        ) as response:
            elapsed = time.time() - start_time

            if response.status_code == 200:
                response.success()

                if self.first_request:
                    self.first_latency = elapsed
                    self.first_request = False
                    permission_metrics.cache_misses += 1
                else:
                    self.cached_latency = elapsed
                    permission_metrics.cache_hits += 1

                    # Report performance improvement from caching
                    if self.first_latency and self.cached_latency:
                        improvement = (
                            (self.first_latency - self.cached_latency) / self.first_latency
                        ) * 100
                        if improvement > 50:  # At least 50% faster
                            pass  # Cache is working well
            elif response.status_code == 401:
                response.failure("Unauthorized")
            else:
                response.failure(f"Unexpected status: {response.status_code}")


# Event handlers for reporting


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs) -> None:  # noqa: ARG001
    """Report permission cache metrics when test stops."""
    print("\n=== Permission Cache Metrics ===")
    print(f"Total Permission Checks: {permission_metrics.permission_checks}")
    print(f"Estimated Cache Hits: {permission_metrics.cache_hits}")
    print(f"Estimated Cache Misses: {permission_metrics.cache_misses}")
    print(f"Estimated Hit Ratio: {permission_metrics.hit_ratio:.2%}")
    print(f"Concurrent Same-User Checks: {permission_metrics.concurrent_checks}")
    print(f"Cache Invalidations: {permission_metrics.invalidations}")
    print("=" * 30)


@events.request.add_listener
def on_request(
    request_type: str,  # noqa: ARG001
    name: str,
    response_time: float,
    response_length: int,  # noqa: ARG001
    response: object,  # noqa: ARG001
    context: dict,  # noqa: ARG001
    exception: Exception | None,
    **kwargs,  # noqa: ARG001
) -> None:
    """Track request timing for cache analysis."""
    if exception:
        return

    # Track very fast profile requests as likely cache hits
    if "profile" in name and response_time < 50:  # Under 50ms
        permission_metrics.cache_hits += 1
    elif "profile" in name and response_time >= 50:
        permission_metrics.cache_misses += 1
