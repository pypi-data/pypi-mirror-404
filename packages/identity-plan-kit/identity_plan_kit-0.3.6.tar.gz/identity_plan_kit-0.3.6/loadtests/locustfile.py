"""
Main Locust file - combined load tests for identity-plan-kit.

This is the entry point for running comprehensive load tests that combine
all test scenarios with realistic user distribution.

Usage:
    # Run with web UI
    locust -f loadtests/locustfile.py

    # Run headless with specific users and duration
    locust -f loadtests/locustfile.py --headless -u 100 -r 10 -t 5m

    # Run specific test file only
    locust -f loadtests/test_auth.py

    # Run with custom host
    locust -f loadtests/locustfile.py --host http://localhost:8000

Environment Variables:
    LOADTEST_BASE_URL - Target application URL (default: http://localhost:8000)
    LOADTEST_API_PREFIX - API prefix (default: "")
    LOADTEST_USER_COUNT - Number of test users to generate (default: 100)
    LOADTEST_SECRET_KEY - JWT secret key for generating test tokens
"""

from locust import HttpUser, between, events, task

from loadtests.config import config
from loadtests.test_auth import AuthLoadUser, ConcurrentRefreshUser, LogoutStressUser
from loadtests.test_database_stress import (
    ConnectionPoolStressUser,
    ConcurrentReadUser,
    ConcurrentWriteUser,
    HealthCheckDbUser,
    MixedReadWriteUser,
)
from loadtests.test_mixed_scenarios import (
    AdminUser,
    APIConsumerUser,
    MonitoringUser,
    RealisticWebUser,
)
from loadtests.test_plans_quota import (
    HealthCheckUser,
    MultiPlanUser,
    PlanSwitchSimulator,
    QuotaIndirectUser,
)
from loadtests.test_rbac_cache import (
    CacheMixedWorkloadUser,
    CacheWarmingUser,
    ConcurrentSameUserCache,
    PermissionCacheUser,
)
from loadtests.utils import get_user_pool, metrics


# Re-export all user classes with weighted distribution
# Weights determine the proportion of each user type


class RealisticWebUserWeighted(RealisticWebUser):
    """Web users - 40% of traffic."""

    weight = 40


class APIConsumerUserWeighted(APIConsumerUser):
    """API consumers - 30% of traffic."""

    weight = 30


class AuthLoadUserWeighted(AuthLoadUser):
    """Auth-focused users - 15% of traffic."""

    weight = 15


class PermissionCacheUserWeighted(PermissionCacheUser):
    """Cache-testing users - 10% of traffic."""

    weight = 10


class AdminUserWeighted(AdminUser):
    """Admin users - 3% of traffic."""

    weight = 3


class MonitoringUserWeighted(MonitoringUser):
    """Monitoring systems - 2% of traffic."""

    weight = 2


# Event handlers for comprehensive reporting


@events.init.add_listener
def on_init(environment, **kwargs) -> None:  # noqa: ARG001
    """Initialize load test environment."""
    print("\n" + "=" * 50)
    print("IDENTITY-PLAN-KIT LOAD TEST")
    print("=" * 50)
    print(f"Target: {config.base_url}{config.api_prefix}")
    print(f"Test Users Pool: {config.test_user_count}")
    print(f"Test Auth: {config.test_auth}")
    print(f"Test RBAC: {config.test_rbac}")
    print(f"Test Plans: {config.test_plans}")
    print("=" * 50 + "\n")

    # Pre-warm the user pool
    get_user_pool()


@events.test_start.add_listener
def on_test_start(environment, **kwargs) -> None:  # noqa: ARG001
    """Called when test starts."""
    print("\n>>> Load test starting...")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs) -> None:  # noqa: ARG001
    """Called when test stops - print final summary."""
    print("\n" + "=" * 50)
    print("FINAL METRICS SUMMARY")
    print("=" * 50)

    # Print aggregated metrics from all modules
    print("\n--- Authentication Metrics ---")
    print(f"Auth Failures: {metrics.auth_failures}")

    print("\n--- Cache Metrics ---")
    print(f"Cache Hits: {metrics.cache_hits}")
    print(f"Cache Misses: {metrics.cache_misses}")
    print(f"Cache Hit Ratio: {metrics.cache_hit_ratio:.2%}")

    print("\n--- Error Metrics ---")
    print(f"Database Errors: {metrics.db_errors}")
    print(f"Quota Exceeded: {metrics.quota_exceeded}")

    print("\n" + "=" * 50)
    print("Load test complete!")
    print("=" * 50 + "\n")


@events.request.add_listener
def on_request(
    request_type: str,
    name: str,
    response_time: float,
    response_length: int,  # noqa: ARG001
    response: object,
    context: dict,  # noqa: ARG001
    exception: Exception | None,
    **kwargs,
) -> None:
    """Global request listener for all requests."""
    # Track slow requests across all tests
    if response_time > 5000 and not exception:
        print(f"SLOW REQUEST: {name} took {response_time:.0f}ms")
