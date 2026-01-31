"""
Database stress tests.

Tests:
- Connection pool exhaustion
- Concurrent database operations
- Connection recovery after failures
- Transaction contention
- Query performance under load

These tests stress the database layer to find:
- Connection pool sizing issues
- Lock contention problems
- Slow queries under load
- Connection leak detection

Run with: locust -f loadtests/test_database_stress.py
"""

import random
import time
from dataclasses import dataclass, field

from locust import HttpUser, between, events, task

from loadtests.config import config
from loadtests.utils import TestUser, get_user_pool, metrics


@dataclass
class DatabaseMetrics:
    """Track database-specific metrics."""

    connection_timeouts: int = 0
    connection_errors: int = 0
    slow_queries: int = 0  # Queries > 500ms
    very_slow_queries: int = 0  # Queries > 2000ms
    successful_queries: int = 0
    response_times: list[float] = field(default_factory=list)

    @property
    def avg_response_time(self) -> float:
        """Calculate average response time."""
        if not self.response_times:
            return 0.0
        return sum(self.response_times) / len(self.response_times)

    @property
    def p95_response_time(self) -> float:
        """Calculate 95th percentile response time."""
        if not self.response_times:
            return 0.0
        sorted_times = sorted(self.response_times)
        index = int(len(sorted_times) * 0.95)
        return sorted_times[index]

    @property
    def p99_response_time(self) -> float:
        """Calculate 99th percentile response time."""
        if not self.response_times:
            return 0.0
        sorted_times = sorted(self.response_times)
        index = int(len(sorted_times) * 0.99)
        return sorted_times[min(index, len(sorted_times) - 1)]


db_metrics = DatabaseMetrics()


class ConnectionPoolStressUser(HttpUser):
    """
    Stress test database connection pool.

    Makes rapid requests to exhaust connection pool and test:
    - Pool behavior under pressure
    - Connection acquisition timeout
    - Connection reuse patterns
    """

    wait_time = between(0.1, 0.3)  # Very short wait
    host = config.base_url

    def on_start(self) -> None:
        """Set up user."""
        pool = get_user_pool()
        self.test_user: TestUser = pool.get_user()

    @task
    def rapid_db_query(self) -> None:
        """
        Make rapid requests that hit the database.

        The /profile endpoint requires database access for:
        - User lookup
        - Permission lookup (cache miss)
        - Plan lookup
        """
        start_time = time.time()

        with self.client.get(
            f"{config.api_prefix}/auth/profile",
            headers=self.test_user.auth_headers(),
            catch_response=True,
            name="DB Stress: /auth/profile",
        ) as response:
            elapsed = (time.time() - start_time) * 1000  # ms
            db_metrics.response_times.append(elapsed)

            if response.status_code == 200:
                response.success()
                db_metrics.successful_queries += 1

                if elapsed > 2000:
                    db_metrics.very_slow_queries += 1
                elif elapsed > 500:
                    db_metrics.slow_queries += 1
            elif response.status_code == 503:
                db_metrics.connection_errors += 1
                response.failure("Service unavailable - possible connection pool exhaustion")
            elif response.status_code == 504:
                db_metrics.connection_timeouts += 1
                response.failure("Gateway timeout - query too slow")
            elif response.status_code == 401:
                response.failure("Unauthorized")
            else:
                response.failure(f"Error: {response.status_code}")


class ConcurrentReadUser(HttpUser):
    """
    Test concurrent read operations.

    Multiple users reading the same data simultaneously tests:
    - Read scalability
    - Index performance
    - Cache effectiveness
    """

    wait_time = between(0.2, 0.5)
    host = config.base_url

    def on_start(self) -> None:
        """Set up user."""
        pool = get_user_pool()
        self.test_user: TestUser = pool.get_user()

    @task(5)
    def read_user_info(self) -> None:
        """Read user info (simple query)."""
        start_time = time.time()

        with self.client.get(
            f"{config.api_prefix}/auth/me",
            headers=self.test_user.auth_headers(),
            catch_response=True,
            name="Concurrent Read: /auth/me",
        ) as response:
            elapsed = (time.time() - start_time) * 1000

            if response.status_code == 200:
                response.success()
                db_metrics.successful_queries += 1
                db_metrics.response_times.append(elapsed)
            else:
                response.failure(f"Error: {response.status_code}")

    @task(3)
    def read_full_profile(self) -> None:
        """Read full profile (complex query with joins)."""
        start_time = time.time()

        with self.client.get(
            f"{config.api_prefix}/auth/profile",
            headers=self.test_user.auth_headers(),
            catch_response=True,
            name="Concurrent Read: /auth/profile",
        ) as response:
            elapsed = (time.time() - start_time) * 1000

            if response.status_code == 200:
                response.success()
                db_metrics.successful_queries += 1
                db_metrics.response_times.append(elapsed)
            else:
                response.failure(f"Error: {response.status_code}")


class ConcurrentWriteUser(HttpUser):
    """
    Test concurrent write operations.

    Simulates multiple users performing write operations:
    - Token refresh (creates new token, invalidates old)
    - Logout (updates token revoked_at)

    Tests:
    - Write contention
    - Transaction isolation
    - Deadlock handling
    """

    wait_time = between(0.5, 1.5)
    host = config.base_url

    def on_start(self) -> None:
        """Set up user."""
        pool = get_user_pool()
        self.test_user: TestUser = pool.get_user()

    @task(3)
    def concurrent_token_refresh(self) -> None:
        """
        Concurrent token refresh operations.

        Token refresh involves:
        - Reading existing token
        - Creating new token
        - Potentially revoking old token

        Multiple concurrent refreshes test transaction handling.
        """
        start_time = time.time()

        with self.client.post(
            f"{config.api_prefix}/auth/refresh",
            cookies={"refresh_token": self.test_user.refresh_token},
            catch_response=True,
            name="Concurrent Write: /auth/refresh",
        ) as response:
            elapsed = (time.time() - start_time) * 1000
            db_metrics.response_times.append(elapsed)

            if response.status_code == 200:
                response.success()
                db_metrics.successful_queries += 1
                data = response.json()
                if "access_token" in data:
                    self.test_user.access_token = data["access_token"]
            elif response.status_code == 401:
                # Token invalidated by concurrent operation - expected
                response.success()
                pool = get_user_pool()
                self.test_user = pool.get_user()
            else:
                response.failure(f"Error: {response.status_code}")

    @task(1)
    def concurrent_logout(self) -> None:
        """
        Concurrent logout operations.

        Tests bulk token revocation under concurrent access.
        """
        start_time = time.time()

        with self.client.post(
            f"{config.api_prefix}/auth/logout",
            headers=self.test_user.auth_headers(),
            cookies=self.test_user.auth_cookies(),
            catch_response=True,
            name="Concurrent Write: /auth/logout",
        ) as response:
            elapsed = (time.time() - start_time) * 1000
            db_metrics.response_times.append(elapsed)

            if response.status_code in (204, 401):
                response.success()
                pool = get_user_pool()
                self.test_user = pool.get_user()
            else:
                response.failure(f"Error: {response.status_code}")


class MixedReadWriteUser(HttpUser):
    """
    Mixed read/write workload.

    Simulates realistic database access patterns:
    - Mostly reads (80%)
    - Some writes (20%)

    Tests how reads and writes interact under load.
    """

    wait_time = between(0.5, 2)
    host = config.base_url

    def on_start(self) -> None:
        """Set up user."""
        pool = get_user_pool()
        self.test_user: TestUser = pool.get_user()

    @task(8)
    def read_operation(self) -> None:
        """Read operation (80% of traffic)."""
        endpoint = random.choice(["/auth/me", "/auth/profile"])
        name = f"Mixed: {endpoint} (read)"

        with self.client.get(
            f"{config.api_prefix}{endpoint}",
            headers=self.test_user.auth_headers(),
            cookies=self.test_user.auth_cookies(),
            catch_response=True,
            name=name,
        ) as response:
            if response.status_code == 200:
                response.success()
                db_metrics.successful_queries += 1
            elif response.status_code == 401:
                response.failure("Unauthorized")
            else:
                response.failure(f"Error: {response.status_code}")

    @task(2)
    def write_operation(self) -> None:
        """Write operation (20% of traffic)."""
        with self.client.post(
            f"{config.api_prefix}/auth/refresh",
            cookies={"refresh_token": self.test_user.refresh_token},
            catch_response=True,
            name="Mixed: /auth/refresh (write)",
        ) as response:
            if response.status_code == 200:
                response.success()
                db_metrics.successful_queries += 1
                data = response.json()
                if "access_token" in data:
                    self.test_user.access_token = data["access_token"]
            elif response.status_code == 401:
                response.success()  # Expected sometimes
                pool = get_user_pool()
                self.test_user = pool.get_user()
            else:
                response.failure(f"Error: {response.status_code}")


class HealthCheckDbUser(HttpUser):
    """
    Test database health check performance.

    Health checks that include database validation should:
    - Complete quickly even under load
    - Not starve other operations
    - Accurately report database status
    """

    wait_time = between(2, 5)
    host = config.base_url

    @task
    def db_health_check(self) -> None:
        """
        Health check including database status.

        The full health endpoint checks database connectivity.
        """
        start_time = time.time()

        with self.client.get(
            f"{config.api_prefix}/health",
            catch_response=True,
            name="Health: /health (with DB)",
        ) as response:
            elapsed = (time.time() - start_time) * 1000

            if response.status_code == 200:
                response.success()
                data = response.json()

                # Verify database component is healthy
                components = data.get("components", {})
                db_status = components.get("database", {})
                if db_status.get("status") != "healthy":
                    response.failure(f"Database unhealthy: {db_status}")

                # Health checks should be fast
                if elapsed > 1000:
                    db_metrics.slow_queries += 1
            elif response.status_code == 503:
                db_metrics.connection_errors += 1
                response.failure("Database unavailable")
            else:
                response.failure(f"Error: {response.status_code}")


class ConnectionRecoveryUser(HttpUser):
    """
    Test connection pool recovery.

    After connection errors, the pool should recover gracefully.
    This user generates bursts of requests to test recovery.
    """

    wait_time = between(1, 3)
    host = config.base_url

    def on_start(self) -> None:
        """Set up user."""
        pool = get_user_pool()
        self.test_user: TestUser = pool.get_user()
        self.burst_count = 0

    @task
    def burst_requests(self) -> None:
        """
        Make a burst of requests.

        This tests connection pool behavior under sudden load spikes.
        """
        # Make 5-10 rapid requests
        burst_size = random.randint(5, 10)

        for i in range(burst_size):
            with self.client.get(
                f"{config.api_prefix}/auth/profile",
                headers=self.test_user.auth_headers(),
                catch_response=True,
                name=f"Burst: /auth/profile (burst-{i})",
            ) as response:
                if response.status_code == 200:
                    response.success()
                elif response.status_code in (503, 504):
                    # Connection issues during burst
                    db_metrics.connection_errors += 1
                    response.failure("Connection issue during burst")
                else:
                    response.failure(f"Error: {response.status_code}")

        self.burst_count += 1


# Event handlers


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs) -> None:  # noqa: ARG001
    """Report database metrics when test stops."""
    print("\n=== Database Stress Metrics ===")
    print(f"Successful Queries: {db_metrics.successful_queries}")
    print(f"Connection Timeouts: {db_metrics.connection_timeouts}")
    print(f"Connection Errors: {db_metrics.connection_errors}")
    print(f"Slow Queries (>500ms): {db_metrics.slow_queries}")
    print(f"Very Slow Queries (>2s): {db_metrics.very_slow_queries}")
    if db_metrics.response_times:
        print(f"Average Response Time: {db_metrics.avg_response_time:.2f}ms")
        print(f"P95 Response Time: {db_metrics.p95_response_time:.2f}ms")
        print(f"P99 Response Time: {db_metrics.p99_response_time:.2f}ms")
    print("=" * 30)


@events.request.add_listener
def on_request(
    request_type: str,  # noqa: ARG001
    name: str,  # noqa: ARG001
    response_time: float,
    response_length: int,  # noqa: ARG001
    response: object,  # noqa: ARG001
    context: dict,  # noqa: ARG001
    exception: Exception | None,
    **kwargs,  # noqa: ARG001
) -> None:
    """Track response times for all requests."""
    if not exception:
        db_metrics.response_times.append(response_time)
        if response_time > 2000:
            db_metrics.very_slow_queries += 1
        elif response_time > 500:
            db_metrics.slow_queries += 1
