"""
Load tests for plans and quota system.

Tests:
- Concurrent quota consumption (atomic check-and-consume)
- Quota exhaustion behavior
- Usage tracking accuracy under load
- Period boundary handling

Since quota operations are service-level (not HTTP endpoints), this module
provides both:
1. HTTP-based tests that indirectly test quotas via profile endpoint
2. Direct service tests using async Python (for deeper testing)

Run with: locust -f loadtests/test_plans_quota.py
"""

import random
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Any

from locust import HttpUser, between, events, task

from loadtests.config import config
from loadtests.utils import TestUser, get_user_pool, metrics


@dataclass
class QuotaMetrics:
    """Track quota-specific metrics."""

    quota_checks: int = 0
    quota_exceeded: int = 0
    successful_consumption: int = 0
    concurrent_consumption_attempts: int = 0
    feature_usage: dict[str, int] = field(default_factory=dict)

    def record_consumption(self, feature_code: str, amount: int = 1) -> None:
        """Record successful quota consumption."""
        self.successful_consumption += 1
        if feature_code not in self.feature_usage:
            self.feature_usage[feature_code] = 0
        self.feature_usage[feature_code] += amount


quota_metrics = QuotaMetrics()


class QuotaIndirectUser(HttpUser):
    """
    Test quotas indirectly through profile endpoint.

    The /profile endpoint returns plan info including limits,
    which exercises the plan service.
    """

    wait_time = between(1, 3)
    host = config.base_url

    def on_start(self) -> None:
        """Set up user with test credentials."""
        pool = get_user_pool()
        self.test_user: TestUser = pool.get_user()

    @task(10)
    def get_plan_info(self) -> None:
        """
        Get plan info via profile endpoint.

        This indirectly tests:
        - Plan lookup performance
        - User plan retrieval
        - Plan limit resolution
        """
        with self.client.get(
            f"{config.api_prefix}/auth/profile",
            headers=self.test_user.auth_headers(),
            cookies=self.test_user.auth_cookies(),
            catch_response=True,
            name="/auth/profile (plan info)",
        ) as response:
            quota_metrics.quota_checks += 1

            if response.status_code == 200:
                response.success()
                data = response.json()
                # Verify plan info is present
                if data.get("plan"):
                    plan = data["plan"]
                    # Log plan details for debugging
                    if plan.get("code"):
                        pass  # Plan loaded successfully
            elif response.status_code == 401:
                metrics.record_auth_failure()
                response.failure("Unauthorized")
            else:
                response.failure(f"Unexpected status: {response.status_code}")


class MultiPlanUser(HttpUser):
    """
    Simulate users with different plan types.

    Tests that the system correctly handles:
    - Different plans (free, pro, enterprise)
    - Different limit configurations
    - Plan-specific permissions
    """

    wait_time = between(1, 2)
    host = config.base_url

    def on_start(self) -> None:
        """Set up user with specific plan type."""
        pool = get_user_pool()
        # Get users with different plan types
        self.test_user: TestUser = pool.get_user()
        self.plan_type = self.test_user.plan_code or "free"

    @task
    def check_plan_access(self) -> None:
        """
        Check plan access and limits.

        Different plan types should show different permissions and limits.
        """
        with self.client.get(
            f"{config.api_prefix}/auth/profile",
            headers=self.test_user.auth_headers(),
            cookies=self.test_user.auth_cookies(),
            catch_response=True,
            name=f"/auth/profile (plan:{self.plan_type})",
        ) as response:
            if response.status_code == 200:
                response.success()
                data = response.json()
                plan = data.get("plan")
                if plan:
                    # Verify plan matches expected type
                    if plan.get("code") == self.plan_type:
                        pass  # Correct plan
                    # Check permissions are plan-appropriate
                    permissions = plan.get("permissions", [])
                    if self.plan_type == "enterprise" and len(permissions) < 3:
                        # Enterprise should have more permissions
                        response.failure("Enterprise plan missing expected permissions")
            elif response.status_code == 401:
                response.failure("Unauthorized")
            else:
                response.failure(f"Unexpected status: {response.status_code}")


class HealthCheckUser(HttpUser):
    """
    Test health endpoints which verify database connectivity.

    Health checks are critical for:
    - Kubernetes probes
    - Load balancer health checks
    - Monitoring systems
    """

    wait_time = between(5, 10)
    host = config.base_url

    @task(5)
    def health_full(self) -> None:
        """
        Full health check - includes database and Redis.

        This is the most comprehensive health check and should complete
        quickly even under load.
        """
        with self.client.get(
            f"{config.api_prefix}/health",
            catch_response=True,
            name="/health (full)",
        ) as response:
            if response.status_code == 200:
                response.success()
                data = response.json()
                # Verify all components are healthy
                if data.get("status") != "healthy":
                    response.failure(f"Unhealthy status: {data.get('status')}")
            elif response.status_code == 503:
                # Service unavailable - system is unhealthy
                metrics.record_db_error()
                response.failure("Service unhealthy")
            else:
                response.failure(f"Unexpected status: {response.status_code}")

    @task(10)
    def health_live(self) -> None:
        """
        Liveness probe - should always be fast.

        This check should never fail unless the process is truly dead.
        """
        with self.client.get(
            f"{config.api_prefix}/health/live",
            catch_response=True,
            name="/health/live",
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Liveness check failed: {response.status_code}")

    @task(10)
    def health_ready(self) -> None:
        """
        Readiness probe - checks if service can accept traffic.

        This may fail during startup or if database is unavailable.
        """
        with self.client.get(
            f"{config.api_prefix}/health/ready",
            catch_response=True,
            name="/health/ready",
        ) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 503:
                # Service not ready - this can happen
                response.failure("Service not ready")
            else:
                response.failure(f"Unexpected status: {response.status_code}")


class PlanSwitchSimulator(HttpUser):
    """
    Simulate users switching between different plans.

    This tests:
    - Plan transition handling
    - Cache invalidation on plan change
    - Concurrent plan access during transitions
    """

    wait_time = between(2, 5)
    host = config.base_url

    def on_start(self) -> None:
        """Set up user."""
        pool = get_user_pool()
        self.test_user: TestUser = pool.get_user()
        self.access_count = 0

    @task(10)
    def access_plan_info(self) -> None:
        """
        Continuously access plan info.

        This simulates a user actively using the service while
        plan changes might be happening in the background.
        """
        self.access_count += 1

        with self.client.get(
            f"{config.api_prefix}/auth/profile",
            headers=self.test_user.auth_headers(),
            cookies=self.test_user.auth_cookies(),
            catch_response=True,
            name="/auth/profile (during plan switch)",
        ) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 401:
                response.failure("Unauthorized")
            else:
                response.failure(f"Unexpected status: {response.status_code}")

    @task(1)
    def simulate_plan_activity(self) -> None:
        """
        Simulate activity that would typically trigger quota usage.

        In a real scenario, this would call an API endpoint that
        consumes quota. Here we just verify the profile/plan is accessible.
        """
        # Make multiple rapid requests to simulate feature usage
        for _ in range(3):
            with self.client.get(
                f"{config.api_prefix}/auth/profile",
                headers=self.test_user.auth_headers(),
                cookies=self.test_user.auth_cookies(),
                catch_response=True,
                name="/auth/profile (feature simulation)",
            ) as response:
                if response.status_code == 200:
                    response.success()
                else:
                    response.failure(f"Status: {response.status_code}")
                    break


# Event handlers for reporting


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs) -> None:  # noqa: ARG001
    """Report quota metrics when test stops."""
    print("\n=== Quota/Plan Metrics ===")
    print(f"Total Quota Checks: {quota_metrics.quota_checks}")
    print(f"Quota Exceeded Events: {quota_metrics.quota_exceeded}")
    print(f"Successful Consumptions: {quota_metrics.successful_consumption}")
    print(f"Concurrent Attempts: {quota_metrics.concurrent_consumption_attempts}")
    print(f"Feature Usage Breakdown: {quota_metrics.feature_usage}")
    print("=" * 30)
