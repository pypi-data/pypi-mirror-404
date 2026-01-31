"""Integration tests for concurrent quota enforcement.

This is the CRITICAL P0 test that validates the TOCTOU fix actually works
under real database concurrency. Without this test, we cannot be confident
that concurrent requests won't exceed quotas.
"""

import asyncio
from collections.abc import Callable
from datetime import date, timedelta
from typing import Any
from uuid import UUID, uuid4

import pytest
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
)

from identity_plan_kit.plans.domain.entities import PeriodType
from identity_plan_kit.plans.models.feature_usage import FeatureUsageModel
from identity_plan_kit.plans.repositories.usage_repo import (
    QuotaExceededInRepoError,
    UsageRepository,
)


# Skip if testcontainers not available
pytest.importorskip("testcontainers")


async def create_test_data(session: AsyncSession) -> tuple[UUID, int, int, int]:
    """Create all required test data and return IDs."""
    from identity_plan_kit.auth.models.user import UserModel
    from identity_plan_kit.plans.models.feature import FeatureModel
    from identity_plan_kit.plans.models.plan import PlanModel
    from identity_plan_kit.plans.models.plan_limit import PlanLimitModel
    from identity_plan_kit.plans.models.user_plan import UserPlanModel
    from identity_plan_kit.rbac.models.role import RoleModel

    # Use UUID for unique identifiers to avoid collisions across tests
    unique_id = uuid4().hex[:8]

    # Create role
    role = RoleModel(code=f"test_role_{unique_id}", name="Test Role")
    session.add(role)
    await session.flush()

    # Create user
    user = UserModel(
        email=f"test_{unique_id}@example.com",
        role_id=role.id,
        display_name=f"Test User {unique_id}",
        is_active=True,
        is_verified=True,
    )
    session.add(user)
    await session.flush()

    # Create plan
    plan = PlanModel(code=f"test_plan_{unique_id}", name="Test Plan")
    session.add(plan)
    await session.flush()

    # Create feature
    feature = FeatureModel(code=f"test_feature_{unique_id}", name="Test Feature")
    session.add(feature)
    await session.flush()

    # Create plan limit
    plan_limit = PlanLimitModel(
        plan_id=plan.id,
        feature_id=feature.id,
        feature_limit=100,
        period="daily",
    )
    session.add(plan_limit)
    await session.flush()

    # Create user plan
    user_plan = UserPlanModel(
        user_id=user.id,
        plan_id=plan.id,
        started_at=date.today(),
        ends_at=date.today() + timedelta(days=30),
    )
    session.add(user_plan)
    await session.flush()

    return user.id, user_plan.id, feature.id, plan.id


class TestConcurrentQuotaEnforcement:
    """Critical integration tests for concurrent quota enforcement.

    These tests validate that the atomic quota check prevents race conditions
    when multiple concurrent requests try to consume the same quota.
    """

    async def test_concurrent_quota_consumption_respects_limit(
        self,
        db_engine: AsyncEngine,
    ) -> None:
        """
        CRITICAL P0 TEST: Concurrent quota requests respect the limit.

        This test fires 20 concurrent requests, each trying to consume 10 units
        from a quota of 100. Without atomic enforcement, all 20 could succeed
        (consuming 200 units). With correct enforcement, only 10 should succeed.
        """
        session_factory = async_sessionmaker(
            db_engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

        # Create test data
        async with session_factory() as setup_session:
            async with setup_session.begin():
                user_id, user_plan_id, feature_id, plan_id = await create_test_data(
                    setup_session
                )

        async def consume_quota() -> tuple[bool, int | None]:
            """Attempt to consume 10 units of quota."""
            async with session_factory() as session:
                async with session.begin():
                    repo = UsageRepository(session)
                    try:
                        new_usage = await repo.atomic_check_and_consume(
                            user_plan_id=user_plan_id,
                            feature_id=feature_id,
                            amount=10,
                            limit=100,
                            period=PeriodType.DAILY,
                        )
                        return (True, new_usage)
                    except QuotaExceededInRepoError:
                        return (False, None)

        # Fire all 20 requests concurrently
        tasks = [consume_quota() for _ in range(20)]
        results = await asyncio.gather(*tasks)

        # Analyze results
        successes = [r for r in results if r[0]]
        failures = [r for r in results if not r[0]]

        # Verify final usage in database
        async with session_factory() as verify_session:
            result = await verify_session.execute(
                select(FeatureUsageModel.feature_usage).where(
                    FeatureUsageModel.user_plan_id == user_plan_id,
                    FeatureUsageModel.feature_id == feature_id,
                )
            )
            final_usage = result.scalar_one_or_none() or 0

        # CRITICAL ASSERTION 1: Quota must NEVER be exceeded
        # This is the key invariant - if this fails, we have a TOCTOU vulnerability
        assert final_usage <= 100, (
            f"CRITICAL: Quota exceeded! Final usage {final_usage} > limit 100. "
            f"This indicates a TOCTOU race condition vulnerability!"
        )

        # CRITICAL ASSERTION 2: Final usage should equal successful consumption
        expected_usage = len(successes) * 10
        assert final_usage == expected_usage, (
            f"Final usage {final_usage} doesn't match successful consumption "
            f"({len(successes)} successes * 10 = {expected_usage})"
        )

        # The number of successes may vary due to concurrency characteristics,
        # but we should have at least some successes and the total should fit within limit
        assert len(successes) >= 1, "At least one request should succeed"
        assert len(successes) <= 10, f"At most 10 requests should succeed (got {len(successes)})"

        # Combined: all 20 requests should complete (either success or quota exceeded)
        assert len(successes) + len(failures) == 20, "All 20 requests should complete"

    async def test_single_large_request_respects_limit(
        self,
        db_engine: AsyncEngine,
    ) -> None:
        """A single request exceeding the limit is rejected."""
        session_factory = async_sessionmaker(
            db_engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

        # Create test data
        async with session_factory() as setup_session:
            async with setup_session.begin():
                user_id, user_plan_id, feature_id, plan_id = await create_test_data(
                    setup_session
                )

        # Test: Try to consume more than the limit in one request
        async with session_factory() as test_session:
            async with test_session.begin():
                repo = UsageRepository(test_session)

                with pytest.raises(QuotaExceededInRepoError) as exc_info:
                    await repo.atomic_check_and_consume(
                        user_plan_id=user_plan_id,
                        feature_id=feature_id,
                        amount=150,  # Exceeds limit of 100
                        limit=100,
                        period=PeriodType.DAILY,
                    )

                assert exc_info.value.current_usage == 0
                assert exc_info.value.limit == 100
                assert exc_info.value.requested == 150

    async def test_unlimited_quota_always_succeeds(
        self,
        db_engine: AsyncEngine,
    ) -> None:
        """Unlimited quota (-1) allows any amount of consumption."""
        session_factory = async_sessionmaker(
            db_engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

        # Create test data
        async with session_factory() as setup_session:
            async with setup_session.begin():
                user_id, user_plan_id, feature_id, plan_id = await create_test_data(
                    setup_session
                )

        # Test: Consume a large amount with unlimited quota
        async with session_factory() as test_session:
            async with test_session.begin():
                repo = UsageRepository(test_session)

                # This should succeed because limit=-1 means unlimited
                new_usage = await repo.atomic_check_and_consume(
                    user_plan_id=user_plan_id,
                    feature_id=feature_id,
                    amount=1000000,  # Very large amount
                    limit=-1,  # Unlimited
                    period=PeriodType.DAILY,
                )

                assert new_usage == 1000000


class TestQuotaEdgeCases:
    """Test edge cases in quota enforcement."""

    async def test_exact_limit_consumption(
        self,
        db_engine: AsyncEngine,
    ) -> None:
        """Consuming exactly the limit should succeed."""
        session_factory = async_sessionmaker(
            db_engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

        # Create test data
        async with session_factory() as setup_session:
            async with setup_session.begin():
                user_id, user_plan_id, feature_id, plan_id = await create_test_data(
                    setup_session
                )

        # Test: Consume exactly 100 units with limit of 100
        async with session_factory() as test_session:
            async with test_session.begin():
                repo = UsageRepository(test_session)

                new_usage = await repo.atomic_check_and_consume(
                    user_plan_id=user_plan_id,
                    feature_id=feature_id,
                    amount=100,  # Exactly the limit
                    limit=100,
                    period=PeriodType.DAILY,
                )

                assert new_usage == 100

                # Now any additional consumption should fail
                with pytest.raises(QuotaExceededInRepoError):
                    await repo.atomic_check_and_consume(
                        user_plan_id=user_plan_id,
                        feature_id=feature_id,
                        amount=1,  # Even 1 more should fail
                        limit=100,
                        period=PeriodType.DAILY,
                    )

    async def test_incremental_consumption_to_limit(
        self,
        db_engine: AsyncEngine,
    ) -> None:
        """Multiple small consumptions up to the limit work correctly."""
        session_factory = async_sessionmaker(
            db_engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

        # Create test data
        async with session_factory() as setup_session:
            async with setup_session.begin():
                user_id, user_plan_id, feature_id, plan_id = await create_test_data(
                    setup_session
                )

        # Test: Consume in increments of 20, should succeed 5 times, fail on 6th
        async with session_factory() as test_session:
            async with test_session.begin():
                repo = UsageRepository(test_session)

                # 5 successful consumptions (20 * 5 = 100)
                for i in range(5):
                    new_usage = await repo.atomic_check_and_consume(
                        user_plan_id=user_plan_id,
                        feature_id=feature_id,
                        amount=20,
                        limit=100,
                        period=PeriodType.DAILY,
                    )
                    assert new_usage == (i + 1) * 20

                # 6th should fail
                with pytest.raises(QuotaExceededInRepoError) as exc_info:
                    await repo.atomic_check_and_consume(
                        user_plan_id=user_plan_id,
                        feature_id=feature_id,
                        amount=20,
                        limit=100,
                        period=PeriodType.DAILY,
                    )

                assert exc_info.value.current_usage == 100
                assert exc_info.value.requested == 20
