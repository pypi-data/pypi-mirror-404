"""
Load tests for authentication endpoints.

Tests:
- Token refresh under high concurrency
- Logout operations (single and everywhere)
- /me endpoint performance
- /profile endpoint (with permissions and plan lookup)
- Concurrent token refresh (race condition testing)

Note: OAuth callback cannot be fully tested as it requires real Google OAuth flow.
We test the endpoints we can call directly.
"""

import random

from locust import HttpUser, between, events, task

from loadtests.config import config
from loadtests.utils import TestUser, get_user_pool, metrics


class AuthLoadUser(HttpUser):
    """
    Simulates users performing authentication operations.

    This user tests:
    - Token refresh (high frequency)
    - Getting user info (/me)
    - Getting full profile (/profile)
    - Logout operations
    """

    # Wait between 1-3 seconds between tasks
    wait_time = between(1, 3)

    # Host is set from config
    host = config.base_url

    def on_start(self) -> None:
        """Set up user with test credentials."""
        pool = get_user_pool()
        self.test_user: TestUser = pool.get_user()

    @task(10)
    def get_me(self) -> None:
        """
        Test /me endpoint - high frequency.

        This endpoint returns basic user info and is called frequently
        by frontend applications.
        """
        with self.client.get(
            f"{config.api_prefix}/auth/me",
            headers=self.test_user.auth_headers(),
            cookies=self.test_user.auth_cookies(),
            catch_response=True,
            name="/auth/me",
        ) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 401:
                metrics.record_auth_failure()
                response.failure("Unauthorized - token may have expired")
            else:
                response.failure(f"Unexpected status: {response.status_code}")

    @task(5)
    def get_profile(self) -> None:
        """
        Test /profile endpoint - moderate frequency.

        This endpoint loads user info + permissions + plan details.
        It exercises the permission cache and plan service.
        """
        with self.client.get(
            f"{config.api_prefix}/auth/profile",
            headers=self.test_user.auth_headers(),
            cookies=self.test_user.auth_cookies(),
            catch_response=True,
            name="/auth/profile",
        ) as response:
            if response.status_code == 200:
                response.success()
                # Track cache behavior if we have custom headers
                cache_status = response.headers.get("X-Cache-Status")
                if cache_status == "HIT":
                    metrics.record_cache_hit()
                elif cache_status == "MISS":
                    metrics.record_cache_miss()
            elif response.status_code == 401:
                metrics.record_auth_failure()
                response.failure("Unauthorized")
            else:
                response.failure(f"Unexpected status: {response.status_code}")

    @task(3)
    def refresh_token(self) -> None:
        """
        Test token refresh - moderate frequency.

        This tests the token rotation mechanism and concurrent refresh handling.
        """
        with self.client.post(
            f"{config.api_prefix}/auth/refresh",
            cookies={"refresh_token": self.test_user.refresh_token},
            catch_response=True,
            name="/auth/refresh",
        ) as response:
            if response.status_code == 200:
                response.success()
                # Update tokens from response
                data = response.json()
                if "access_token" in data:
                    self.test_user.access_token = data["access_token"]
                # Get new refresh token from cookies
                if "refresh_token" in response.cookies:
                    self.test_user.refresh_token = response.cookies["refresh_token"]
            elif response.status_code == 401:
                # Token expired or invalid - this is expected sometimes
                metrics.record_auth_failure()
                response.success()  # Don't fail the test, this is expected behavior
            else:
                response.failure(f"Unexpected status: {response.status_code}")

    @task(1)
    def logout_single(self) -> None:
        """
        Test single session logout - low frequency.

        After logout, get a fresh token from the pool.
        """
        with self.client.post(
            f"{config.api_prefix}/auth/logout",
            headers=self.test_user.auth_headers(),
            cookies=self.test_user.auth_cookies(),
            catch_response=True,
            name="/auth/logout",
        ) as response:
            if response.status_code == 204:
                response.success()
                # Get fresh user from pool
                pool = get_user_pool()
                self.test_user = pool.get_user()
            elif response.status_code == 401:
                # Already logged out or expired
                response.success()
                pool = get_user_pool()
                self.test_user = pool.get_user()
            else:
                response.failure(f"Unexpected status: {response.status_code}")


class ConcurrentRefreshUser(HttpUser):
    """
    User that aggressively refreshes tokens to test race conditions.

    This tests the idempotent token refresh mechanism where multiple
    concurrent refresh requests should all succeed without creating
    duplicate tokens.
    """

    wait_time = between(0.1, 0.5)  # Very short wait to stress test
    host = config.base_url

    def on_start(self) -> None:
        """Set up user with test credentials."""
        pool = get_user_pool()
        self.test_user: TestUser = pool.get_user()
        self.refresh_count = 0

    @task
    def concurrent_refresh(self) -> None:
        """
        Aggressively refresh tokens to test concurrent handling.

        The system should handle multiple concurrent refreshes gracefully
        without creating duplicate sessions or race conditions.
        """
        with self.client.post(
            f"{config.api_prefix}/auth/refresh",
            cookies={"refresh_token": self.test_user.refresh_token},
            catch_response=True,
            name="/auth/refresh (concurrent)",
        ) as response:
            self.refresh_count += 1

            if response.status_code == 200:
                response.success()
                data = response.json()
                if "access_token" in data:
                    self.test_user.access_token = data["access_token"]
                if "refresh_token" in response.cookies:
                    self.test_user.refresh_token = response.cookies["refresh_token"]
            elif response.status_code == 401:
                # Token was invalidated by another request - expected behavior
                response.success()
            elif response.status_code == 429:
                # Rate limited - this is OK
                response.success()
            else:
                response.failure(f"Unexpected status: {response.status_code}")


class LogoutStressUser(HttpUser):
    """
    User that tests logout operations including "logout everywhere".

    This tests:
    - Session cleanup performance
    - Bulk token revocation
    - Concurrent logout handling
    """

    wait_time = between(2, 5)
    host = config.base_url

    def on_start(self) -> None:
        """Set up user with test credentials."""
        pool = get_user_pool()
        self.test_user: TestUser = pool.get_user()

    @task(3)
    def logout_single(self) -> None:
        """Test single session logout."""
        with self.client.post(
            f"{config.api_prefix}/auth/logout",
            headers=self.test_user.auth_headers(),
            cookies=self.test_user.auth_cookies(),
            catch_response=True,
            name="/auth/logout (single)",
        ) as response:
            if response.status_code in (204, 401):
                response.success()
                pool = get_user_pool()
                self.test_user = pool.get_user()
            else:
                response.failure(f"Unexpected status: {response.status_code}")

    @task(1)
    def logout_everywhere(self) -> None:
        """
        Test "logout everywhere" which revokes all sessions.

        This exercises bulk token revocation and should complete quickly
        even with many active sessions.
        """
        with self.client.post(
            f"{config.api_prefix}/auth/logout?everywhere=true",
            headers=self.test_user.auth_headers(),
            cookies=self.test_user.auth_cookies(),
            catch_response=True,
            name="/auth/logout (everywhere)",
        ) as response:
            if response.status_code in (204, 401):
                response.success()
                pool = get_user_pool()
                self.test_user = pool.get_user()
            else:
                response.failure(f"Unexpected status: {response.status_code}")


# Event handlers for reporting custom metrics


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs) -> None:  # noqa: ARG001
    """Report custom metrics when test stops."""
    print("\n=== Custom Auth Metrics ===")
    print(f"Cache Hit Ratio: {metrics.cache_hit_ratio:.2%}")
    print(f"Cache Hits: {metrics.cache_hits}")
    print(f"Cache Misses: {metrics.cache_misses}")
    print(f"Auth Failures: {metrics.auth_failures}")
    print("=" * 30)
