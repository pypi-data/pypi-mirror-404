"""
Load testing package for identity-plan-kit.

This package provides comprehensive Locust-based load tests for testing:
- Authentication flows (token refresh, logout, session management)
- RBAC permission cache (hit ratio, invalidation, concurrency)
- Plan and quota system (usage tracking, quota enforcement)
- Database performance (connection pool, concurrent operations)
- Mixed realistic scenarios (web users, API consumers, admins)

Usage:
    # Install dependencies
    pip install identity-plan-kit[loadtest]

    # Run with web UI
    locust -f loadtests/locustfile.py

    # Run headless
    locust -f loadtests/locustfile.py --headless -u 100 -r 10 -t 5m

    # Run specific test module
    locust -f loadtests/test_auth.py
"""

from loadtests.config import LoadTestConfig, config
from loadtests.utils import (
    MetricsCollector,
    TestUser,
    TestUserPool,
    get_user_pool,
    metrics,
)

__all__ = [
    "LoadTestConfig",
    "MetricsCollector",
    "TestUser",
    "TestUserPool",
    "config",
    "get_user_pool",
    "metrics",
]
