"""
Mixed scenario load tests - realistic user behavior patterns.

This module simulates realistic usage patterns combining:
- Authentication flows
- Permission checks
- Plan/quota access
- Health monitoring

Use these tests to validate system behavior under production-like loads.

Run with: locust -f loadtests/test_mixed_scenarios.py
"""

import random
import time
from dataclasses import dataclass, field
from typing import Any

from locust import HttpUser, LoadTestShape, between, events, task

from loadtests.config import config
from loadtests.utils import TestUser, get_user_pool, metrics


@dataclass
class ScenarioMetrics:
    """Track scenario-specific metrics."""

    total_sessions: int = 0
    session_durations: list[float] = field(default_factory=list)
    active_users_at_peak: int = 0
    errors_by_type: dict[str, int] = field(default_factory=dict)

    @property
    def avg_session_duration(self) -> float:
        """Calculate average session duration."""
        if not self.session_durations:
            return 0.0
        return sum(self.session_durations) / len(self.session_durations)


scenario_metrics = ScenarioMetrics()


class RealisticWebUser(HttpUser):
    """
    Simulates a realistic web application user.

    Behavior pattern:
    1. User "logs in" (simulated by getting profile)
    2. Makes several requests checking permissions/profile
    3. Occasionally refreshes token
    4. Eventually "logs out"

    This represents typical SPA (Single Page Application) behavior.
    """

    wait_time = between(2, 8)  # Realistic human think time
    host = config.base_url

    def on_start(self) -> None:
        """Initialize user session."""
        pool = get_user_pool()
        self.test_user: TestUser = pool.get_user()
        self.session_start = time.time()
        self.page_views = 0
        self.max_page_views = random.randint(5, 20)
        scenario_metrics.total_sessions += 1

    def on_stop(self) -> None:
        """Record session duration on stop."""
        duration = time.time() - self.session_start
        scenario_metrics.session_durations.append(duration)

    @task(10)
    def view_dashboard(self) -> None:
        """
        Simulate viewing a dashboard page.

        Dashboard typically loads user info and checks permissions.
        """
        self.page_views += 1

        # Get user info (simulates fetching user data for UI)
        with self.client.get(
            f"{config.api_prefix}/auth/me",
            headers=self.test_user.auth_headers(),
            catch_response=True,
            name="Dashboard: /auth/me",
        ) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 401:
                self._handle_auth_error()
                response.failure("Session expired")
            else:
                self._record_error("dashboard_me", response.status_code)
                response.failure(f"Error: {response.status_code}")

    @task(5)
    def check_account_settings(self) -> None:
        """
        Simulate viewing account settings.

        Account settings typically show full profile with plan info.
        """
        self.page_views += 1

        with self.client.get(
            f"{config.api_prefix}/auth/profile",
            headers=self.test_user.auth_headers(),
            catch_response=True,
            name="Settings: /auth/profile",
        ) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 401:
                self._handle_auth_error()
                response.failure("Session expired")
            else:
                self._record_error("settings_profile", response.status_code)
                response.failure(f"Error: {response.status_code}")

    @task(2)
    def refresh_session(self) -> None:
        """
        Periodically refresh the session token.

        Real SPAs typically refresh tokens before expiry.
        """
        with self.client.post(
            f"{config.api_prefix}/auth/refresh",
            cookies={"refresh_token": self.test_user.refresh_token},
            catch_response=True,
            name="Session: /auth/refresh",
        ) as response:
            if response.status_code == 200:
                response.success()
                data = response.json()
                if "access_token" in data:
                    self.test_user.access_token = data["access_token"]
            elif response.status_code == 401:
                # Session fully expired - would redirect to login in real app
                response.success()  # Expected behavior
            else:
                self._record_error("refresh", response.status_code)
                response.failure(f"Error: {response.status_code}")

    @task(1)
    def end_session(self) -> None:
        """
        End the user session (logout).

        Simulates user clicking logout or closing browser.
        """
        if self.page_views >= self.max_page_views:
            with self.client.post(
                f"{config.api_prefix}/auth/logout",
                headers=self.test_user.auth_headers(),
                cookies=self.test_user.auth_cookies(),
                catch_response=True,
                name="Session: /auth/logout",
            ) as response:
                if response.status_code in (204, 401):
                    response.success()
                else:
                    response.failure(f"Error: {response.status_code}")

            # Get fresh user for next session
            pool = get_user_pool()
            self.test_user = pool.get_user()
            self.session_start = time.time()
            self.page_views = 0
            self.max_page_views = random.randint(5, 20)
            scenario_metrics.total_sessions += 1

    def _handle_auth_error(self) -> None:
        """Handle authentication errors."""
        metrics.record_auth_failure()
        # Get fresh credentials
        pool = get_user_pool()
        self.test_user = pool.get_user()

    def _record_error(self, operation: str, status_code: int) -> None:
        """Record error for analysis."""
        key = f"{operation}_{status_code}"
        if key not in scenario_metrics.errors_by_type:
            scenario_metrics.errors_by_type[key] = 0
        scenario_metrics.errors_by_type[key] += 1


class APIConsumerUser(HttpUser):
    """
    Simulates an API consumer (backend service or mobile app).

    Behavior pattern:
    - High frequency API calls
    - Minimal wait time between requests
    - Heavy permission/quota checking
    """

    wait_time = between(0.5, 2)
    host = config.base_url

    def on_start(self) -> None:
        """Initialize API consumer."""
        pool = get_user_pool()
        self.test_user: TestUser = pool.get_user()
        self.request_count = 0

    @task(20)
    def api_request_with_auth(self) -> None:
        """
        Simulate authenticated API request.

        API consumers typically make frequent requests with auth headers.
        """
        self.request_count += 1

        with self.client.get(
            f"{config.api_prefix}/auth/me",
            headers=self.test_user.auth_headers(),
            catch_response=True,
            name="API: /auth/me",
        ) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 401:
                metrics.record_auth_failure()
                response.failure("Token expired")
            else:
                response.failure(f"Error: {response.status_code}")

    @task(5)
    def api_check_permissions(self) -> None:
        """
        Check permissions before performing action.

        API consumers often check permissions before sensitive operations.
        """
        with self.client.get(
            f"{config.api_prefix}/auth/profile",
            headers=self.test_user.auth_headers(),
            catch_response=True,
            name="API: /auth/profile (permission check)",
        ) as response:
            if response.status_code == 200:
                response.success()
                # Verify we have permissions data
                data = response.json()
                if "user_permissions" not in data:
                    response.failure("Missing permissions in response")
            elif response.status_code == 401:
                response.failure("Token expired")
            else:
                response.failure(f"Error: {response.status_code}")


class AdminUser(HttpUser):
    """
    Simulates an admin user with elevated privileges.

    Admin users typically:
    - Have more permissions
    - Access admin-specific endpoints
    - May trigger cache invalidations
    """

    wait_time = between(3, 10)
    host = config.base_url

    def on_start(self) -> None:
        """Initialize admin user."""
        pool = get_user_pool()
        self.test_user: TestUser = pool.get_admin_user()

    @task(5)
    def admin_check_profile(self) -> None:
        """Admin checking their own profile."""
        with self.client.get(
            f"{config.api_prefix}/auth/profile",
            headers=self.test_user.auth_headers(),
            catch_response=True,
            name="Admin: /auth/profile",
        ) as response:
            if response.status_code == 200:
                response.success()
                data = response.json()
                # Verify admin has expected role
                if data.get("role_code") != "admin":
                    response.failure("Not an admin user")
            else:
                response.failure(f"Error: {response.status_code}")

    @task(2)
    def admin_health_check(self) -> None:
        """Admin checking system health."""
        with self.client.get(
            f"{config.api_prefix}/health",
            catch_response=True,
            name="Admin: /health",
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Health check failed: {response.status_code}")


class MonitoringUser(HttpUser):
    """
    Simulates monitoring/observability systems.

    Monitoring systems typically:
    - Call health endpoints frequently
    - Need very fast responses
    - Should not interfere with normal traffic
    """

    wait_time = between(5, 15)
    host = config.base_url
    weight = 1  # Lower weight - fewer monitoring users

    @task(3)
    def health_check(self) -> None:
        """Standard health check."""
        with self.client.get(
            f"{config.api_prefix}/health",
            catch_response=True,
            name="Monitor: /health",
        ) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 503:
                response.failure("Service unhealthy")
            else:
                response.failure(f"Error: {response.status_code}")

    @task(5)
    def liveness_probe(self) -> None:
        """Kubernetes liveness probe."""
        with self.client.get(
            f"{config.api_prefix}/health/live",
            catch_response=True,
            name="Monitor: /health/live",
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Liveness failed: {response.status_code}")

    @task(5)
    def readiness_probe(self) -> None:
        """Kubernetes readiness probe."""
        with self.client.get(
            f"{config.api_prefix}/health/ready",
            catch_response=True,
            name="Monitor: /health/ready",
        ) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 503:
                response.failure("Service not ready")
            else:
                response.failure(f"Error: {response.status_code}")


class SpikeLoadShape(LoadTestShape):
    """
    Custom load shape that simulates traffic spikes.

    Pattern:
    1. Ramp up to baseline
    2. Spike to 3x baseline
    3. Return to baseline
    4. Repeat

    This tests system behavior under sudden load increases.
    """

    # Configuration
    baseline_users = 50
    spike_users = 150
    baseline_duration = 60  # seconds
    spike_duration = 30
    ramp_time = 30

    def tick(self) -> tuple[int, float] | None:
        """Return the user count and spawn rate for the current time."""
        run_time = self.get_run_time()

        # Calculate cycle position
        cycle_duration = self.baseline_duration + self.spike_duration + (2 * self.ramp_time)
        cycle_position = run_time % cycle_duration

        if cycle_position < self.ramp_time:
            # Ramping up from baseline
            progress = cycle_position / self.ramp_time
            users = int(self.baseline_users + (self.spike_users - self.baseline_users) * progress)
        elif cycle_position < self.ramp_time + self.spike_duration:
            # At spike level
            users = self.spike_users
        elif cycle_position < (2 * self.ramp_time) + self.spike_duration:
            # Ramping down to baseline
            progress = (cycle_position - self.ramp_time - self.spike_duration) / self.ramp_time
            users = int(self.spike_users - (self.spike_users - self.baseline_users) * progress)
        else:
            # At baseline
            users = self.baseline_users

        # Update peak metric
        if users > scenario_metrics.active_users_at_peak:
            scenario_metrics.active_users_at_peak = users

        return (users, 10)  # 10 users/second spawn rate


class GradualRampShape(LoadTestShape):
    """
    Gradual ramp-up load shape for stress testing.

    Pattern:
    1. Start with minimal users
    2. Gradually increase to max
    3. Hold at max
    4. Gradually decrease

    This helps identify at what load level issues start appearing.
    """

    min_users = 10
    max_users = 200
    ramp_up_time = 120  # 2 minutes
    hold_time = 180  # 3 minutes
    ramp_down_time = 60  # 1 minute

    def tick(self) -> tuple[int, float] | None:
        """Return the user count and spawn rate for the current time."""
        run_time = self.get_run_time()

        total_time = self.ramp_up_time + self.hold_time + self.ramp_down_time

        if run_time > total_time:
            return None  # Test complete

        if run_time < self.ramp_up_time:
            # Ramping up
            progress = run_time / self.ramp_up_time
            users = int(self.min_users + (self.max_users - self.min_users) * progress)
        elif run_time < self.ramp_up_time + self.hold_time:
            # Holding at max
            users = self.max_users
        else:
            # Ramping down
            progress = (run_time - self.ramp_up_time - self.hold_time) / self.ramp_down_time
            users = int(self.max_users - (self.max_users - self.min_users) * progress)

        if users > scenario_metrics.active_users_at_peak:
            scenario_metrics.active_users_at_peak = users

        return (users, 5)


# Event handlers


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs) -> None:  # noqa: ARG001
    """Report scenario metrics when test stops."""
    print("\n=== Scenario Metrics ===")
    print(f"Total Sessions: {scenario_metrics.total_sessions}")
    print(f"Average Session Duration: {scenario_metrics.avg_session_duration:.2f}s")
    print(f"Peak Active Users: {scenario_metrics.active_users_at_peak}")
    print(f"Errors by Type: {scenario_metrics.errors_by_type}")
    print("=" * 30)
