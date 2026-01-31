"""
Direct quota service stress tests.

This module tests the quota system directly at the service level,
bypassing HTTP to focus on:
- Atomic check-and-consume correctness under concurrency
- Race condition handling in quota updates
- Database transaction behavior
- Quota exhaustion edge cases

Run as a standalone script (not via Locust):
    python -m loadtests.test_quota_direct

Requires a running PostgreSQL database with test data.
"""

import asyncio
import time
from dataclasses import dataclass, field
from datetime import date, timedelta
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine


@dataclass
class QuotaTestMetrics:
    """Metrics for quota testing."""

    successful_consumptions: int = 0
    quota_exceeded_errors: int = 0
    other_errors: int = 0
    total_time_ms: float = 0.0
    concurrent_runs: int = 0
    race_conditions_detected: int = 0

    @property
    def error_rate(self) -> float:
        """Calculate error rate."""
        total = self.successful_consumptions + self.quota_exceeded_errors + self.other_errors
        if total == 0:
            return 0.0
        return (self.other_errors) / total

    @property
    def throughput(self) -> float:
        """Calculate throughput (ops/sec)."""
        if self.total_time_ms == 0:
            return 0.0
        return (
            self.successful_consumptions + self.quota_exceeded_errors
        ) * 1000 / self.total_time_ms


class DirectQuotaTest:
    """
    Direct quota service testing.

    Tests the atomic check-and-consume operation under concurrent load
    to verify that:
    1. Quotas are never over-consumed (TOCTOU race conditions fixed)
    2. Concurrent requests are handled correctly
    3. Database transactions provide proper isolation
    """

    def __init__(self, database_url: str) -> None:
        """Initialize with database connection."""
        self.database_url = database_url
        self.engine = None
        self.session_factory = None
        self.metrics = QuotaTestMetrics()

    async def setup(self) -> None:
        """Set up database connection."""
        self.engine = create_async_engine(
            self.database_url,
            pool_size=20,  # Match expected concurrency
            max_overflow=10,
            pool_pre_ping=True,
        )
        self.session_factory = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

    async def teardown(self) -> None:
        """Clean up database connection."""
        if self.engine:
            await self.engine.dispose()

    async def test_concurrent_quota_consumption(
        self,
        user_plan_id: int,
        feature_id: int,
        limit: int,
        concurrent_requests: int = 50,
        amount_per_request: int = 1,
    ) -> QuotaTestMetrics:
        """
        Test concurrent quota consumption.

        This test verifies that atomic check-and-consume works correctly
        by making many concurrent requests that should consume exactly
        the available quota without over-consumption.

        Args:
            user_plan_id: ID of the user plan to test
            feature_id: ID of the feature to consume quota for
            limit: The quota limit
            concurrent_requests: Number of concurrent requests to make
            amount_per_request: Amount to consume per request

        Returns:
            Metrics from the test run
        """
        from identity_plan_kit.plans.domain.entities import PeriodType
        from identity_plan_kit.plans.uow import PlansUnitOfWork
        from identity_plan_kit.plans.repositories.usage_repo import QuotaExceededInRepoError

        self.metrics = QuotaTestMetrics()
        self.metrics.concurrent_runs = concurrent_requests

        async def consume_quota(request_id: int) -> tuple[str, int]:
            """Single quota consumption attempt."""
            try:
                async with PlansUnitOfWork(self.session_factory) as uow:
                    new_usage = await uow.usage.atomic_check_and_consume(
                        user_plan_id=user_plan_id,
                        feature_id=feature_id,
                        amount=amount_per_request,
                        limit=limit,
                        period=PeriodType.DAILY,
                    )
                    return ("success", new_usage)
            except QuotaExceededInRepoError:
                return ("quota_exceeded", 0)
            except Exception as e:
                return ("error", str(e))

        # Run all requests concurrently
        start_time = time.time()
        tasks = [consume_quota(i) for i in range(concurrent_requests)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        self.metrics.total_time_ms = (time.time() - start_time) * 1000

        # Process results
        max_usage = 0
        for result in results:
            if isinstance(result, Exception):
                self.metrics.other_errors += 1
            elif result[0] == "success":
                self.metrics.successful_consumptions += 1
                max_usage = max(max_usage, result[1])
            elif result[0] == "quota_exceeded":
                self.metrics.quota_exceeded_errors += 1
            else:
                self.metrics.other_errors += 1

        # Verify correctness
        expected_success = min(concurrent_requests * amount_per_request, limit) // amount_per_request
        if self.metrics.successful_consumptions > expected_success:
            self.metrics.race_conditions_detected = (
                self.metrics.successful_consumptions - expected_success
            )
            print(f"RACE CONDITION: {self.metrics.race_conditions_detected} over-consumptions!")

        return self.metrics

    async def test_quota_exhaustion_accuracy(
        self,
        user_plan_id: int,
        feature_id: int,
        limit: int,
    ) -> bool:
        """
        Test that quota exhaustion happens at exactly the limit.

        Makes sequential requests until quota is exhausted and verifies
        the total consumed equals the limit exactly.

        Returns:
            True if quota system is accurate, False if over/under consumption
        """
        from identity_plan_kit.plans.domain.entities import PeriodType
        from identity_plan_kit.plans.uow import PlansUnitOfWork
        from identity_plan_kit.plans.repositories.usage_repo import QuotaExceededInRepoError

        consumed = 0

        while consumed < limit + 10:  # Try to go over limit
            try:
                async with PlansUnitOfWork(self.session_factory) as uow:
                    await uow.usage.atomic_check_and_consume(
                        user_plan_id=user_plan_id,
                        feature_id=feature_id,
                        amount=1,
                        limit=limit,
                        period=PeriodType.DAILY,
                    )
                    consumed += 1
            except QuotaExceededInRepoError:
                break

        is_accurate = consumed == limit
        if not is_accurate:
            print(f"ACCURACY ERROR: Consumed {consumed}, expected {limit}")

        return is_accurate


async def run_direct_tests() -> None:
    """Run direct quota tests."""
    from loadtests.config import config

    print("\n" + "=" * 50)
    print("DIRECT QUOTA SERVICE TESTS")
    print("=" * 50)

    tester = DirectQuotaTest(config.database_url)

    try:
        await tester.setup()

        # Note: These tests require a database with test data
        # You'll need to set up user_plan_id and feature_id based on your data

        print("\nRunning concurrent quota consumption test...")
        print("(Requires test data in database - adjust IDs as needed)")

        # Example test - adjust IDs for your test database
        # metrics = await tester.test_concurrent_quota_consumption(
        #     user_plan_id=1,
        #     feature_id=1,
        #     limit=100,
        #     concurrent_requests=200,  # More requests than quota
        # )
        #
        # print(f"\nResults:")
        # print(f"  Successful: {metrics.successful_consumptions}")
        # print(f"  Quota Exceeded: {metrics.quota_exceeded_errors}")
        # print(f"  Errors: {metrics.other_errors}")
        # print(f"  Throughput: {metrics.throughput:.2f} ops/sec")
        # print(f"  Race Conditions: {metrics.race_conditions_detected}")

        print("\nTo run these tests, uncomment the test calls above")
        print("and configure the user_plan_id and feature_id for your test data.")

    finally:
        await tester.teardown()

    print("\n" + "=" * 50)
    print("Direct tests complete!")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(run_direct_tests())
