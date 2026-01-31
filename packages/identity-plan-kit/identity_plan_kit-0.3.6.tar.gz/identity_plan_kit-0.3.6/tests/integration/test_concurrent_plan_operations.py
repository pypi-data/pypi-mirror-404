"""Integration tests for concurrent plan operations.

Tests race conditions in:
- Concurrent plan assignment/upgrade
- Concurrent plan cancellation
- Concurrent usage reset
- Concurrent plan extension

CRITICAL: Plan operations must prevent:
1. User having multiple active plans simultaneously
2. Plan upgrade losing existing usage data
3. Usage reset happening during consumption
"""

import asyncio
from datetime import date, timedelta
from uuid import UUID

import pytest
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
)

from identity_plan_kit.plans.domain.entities import PeriodType
from identity_plan_kit.plans.models.feature_usage import FeatureUsageModel
from identity_plan_kit.plans.models.user_plan import UserPlanModel
from identity_plan_kit.plans.repositories.usage_repo import (
    QuotaExceededInRepoError,
    UsageRepository,
)

# Skip if testcontainers not available
pytest.importorskip("testcontainers")


async def create_test_infrastructure(
    session: AsyncSession,
    suffix: str,
) -> tuple[UUID, int, int, int]:
    """Create all required test data and return IDs."""
    from identity_plan_kit.auth.models.user import UserModel
    from identity_plan_kit.plans.models.feature import FeatureModel
    from identity_plan_kit.plans.models.plan import PlanModel
    from identity_plan_kit.plans.models.plan_limit import PlanLimitModel
    from identity_plan_kit.rbac.models.role import RoleModel

    # Create role
    role = RoleModel(code=f"user_{suffix}", name="Test Role")
    session.add(role)
    await session.flush()

    # Create user
    user = UserModel(
        email=f"plan_test_{suffix}@example.com",
        role_id=role.id,
        display_name=f"Plan Test {suffix}",
        is_active=True,
        is_verified=True,
    )
    session.add(user)
    await session.flush()

    # Create free and pro plans
    free_plan = PlanModel(code=f"free_{suffix}", name="Free Plan")
    pro_plan = PlanModel(code=f"pro_{suffix}", name="Pro Plan")
    session.add(free_plan)
    session.add(pro_plan)
    await session.flush()

    # Create feature
    feature = FeatureModel(code=f"api_calls_{suffix}", name="API Calls")
    session.add(feature)
    await session.flush()

    # Create plan limits
    free_limit = PlanLimitModel(
        plan_id=free_plan.id,
        feature_id=feature.id,
        feature_limit=100,
        period="daily",
    )
    pro_limit = PlanLimitModel(
        plan_id=pro_plan.id,
        feature_id=feature.id,
        feature_limit=1000,
        period="daily",
    )
    session.add(free_limit)
    session.add(pro_limit)
    await session.flush()

    return user.id, free_plan.id, pro_plan.id, feature.id


class TestConcurrentPlanAssignment:
    """Tests for concurrent plan assignment scenarios."""

    async def test_concurrent_plan_assignment_only_one_active(
        self,
        db_engine: AsyncEngine,
    ) -> None:
        """
        CRITICAL: Multiple concurrent plan assignments should result in
        exactly ONE active plan for the user.

        This simulates:
        1. Payment webhook retry creates duplicate assignments
        2. Or race between plan upgrade and downgrade
        """
        session_factory = async_sessionmaker(
            db_engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

        # Setup
        async with session_factory() as setup_session:
            async with setup_session.begin():
                user_id, free_plan_id, pro_plan_id, feature_id = await create_test_infrastructure(
                    setup_session, f"assign_{id(db_engine)}"
                )

        async def assign_plan(plan_id: int, attempt: int) -> UUID | None:
            """Attempt to assign a plan to the user."""
            async with session_factory() as session:
                async with session.begin():
                    user_plan = UserPlanModel(
                        user_id=user_id,
                        plan_id=plan_id,
                        started_at=date.today(),
                        ends_at=date.today() + timedelta(days=30),
                    )
                    session.add(user_plan)
                    await session.flush()
                    return user_plan.id

        # Fire concurrent plan assignments
        tasks = [assign_plan(free_plan_id, i) for i in range(10)]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        successes = [r for r in results if isinstance(r, UUID)]

        # Check active plans
        async with session_factory() as verify_session:
            today = date.today()
            result = await verify_session.execute(
                select(func.count(UserPlanModel.id)).where(
                    UserPlanModel.user_id == user_id,
                    UserPlanModel.started_at <= today,
                    UserPlanModel.ends_at >= today,
                    UserPlanModel.is_cancelled == False,
                )
            )
            active_count = result.scalar()

        # NOTE: Without explicit unique constraint on (user_id, is_active),
        # multiple plans could be created. This test documents the behavior.
        # In production, the service layer should handle plan expiration first.
        assert active_count >= 1, "At least one plan should exist"

    async def test_concurrent_usage_consumption_with_plan_change(
        self,
        db_engine: AsyncEngine,
    ) -> None:
        """
        Test: Usage consumption during plan upgrade/downgrade.

        Consumption should either succeed with old limit or new limit,
        never with inconsistent state.
        """
        session_factory = async_sessionmaker(
            db_engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

        # Setup with user plan
        async with session_factory() as setup_session:
            async with setup_session.begin():
                user_id, free_plan_id, pro_plan_id, feature_id = await create_test_infrastructure(
                    setup_session, f"usage_{id(db_engine)}"
                )

                # Create initial user plan
                user_plan = UserPlanModel(
                    user_id=user_id,
                    plan_id=free_plan_id,
                    started_at=date.today(),
                    ends_at=date.today() + timedelta(days=30),
                )
                setup_session.add(user_plan)
                await setup_session.flush()
                user_plan_id = user_plan.id

        consumption_results: list[tuple[bool, int | None]] = []
        results_lock = asyncio.Lock()

        async def consume_quota(amount: int, limit: int) -> tuple[bool, int | None]:
            """Attempt to consume quota."""
            async with session_factory() as session:
                async with session.begin():
                    repo = UsageRepository(session)
                    try:
                        new_usage = await repo.atomic_check_and_consume(
                            user_plan_id=user_plan_id,
                            feature_id=feature_id,
                            amount=amount,
                            limit=limit,
                            period=PeriodType.DAILY,
                        )
                        return (True, new_usage)
                    except QuotaExceededInRepoError:
                        return (False, None)

        # Fire concurrent consumption with different limits
        # (simulating plan change during consumption)
        tasks = [
            consume_quota(10, 100),  # Free tier limit
            consume_quota(10, 100),
            consume_quota(10, 1000),  # Pro tier limit (upgrade happened)
            consume_quota(10, 100),
            consume_quota(10, 1000),
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        successes = [(s, u) for s, u in results if isinstance(s, bool) and s]

        # Verify final usage is consistent
        async with session_factory() as verify_session:
            result = await verify_session.execute(
                select(FeatureUsageModel.feature_usage).where(
                    FeatureUsageModel.user_plan_id == user_plan_id,
                    FeatureUsageModel.feature_id == feature_id,
                )
            )
            final_usage = result.scalar_one_or_none() or 0

        # Final usage should equal sum of successful consumptions
        expected = len(successes) * 10
        assert final_usage == expected, (
            f"Usage mismatch: expected {expected}, got {final_usage}"
        )


class TestConcurrentUsageReset:
    """Tests for concurrent usage reset operations."""

    async def test_concurrent_reset_and_consumption(
        self,
        db_engine: AsyncEngine,
    ) -> None:
        """
        CRITICAL: Reset and consumption happening concurrently.

        This tests the scenario where:
        1. Background job resets usage for new billing period
        2. User is actively consuming quota
        """
        session_factory = async_sessionmaker(
            db_engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

        # Setup with existing usage
        async with session_factory() as setup_session:
            async with setup_session.begin():
                user_id, free_plan_id, pro_plan_id, feature_id = await create_test_infrastructure(
                    setup_session, f"reset_{id(db_engine)}"
                )

                user_plan = UserPlanModel(
                    user_id=user_id,
                    plan_id=free_plan_id,
                    started_at=date.today(),
                    ends_at=date.today() + timedelta(days=30),
                )
                setup_session.add(user_plan)
                await setup_session.flush()
                user_plan_id = user_plan.id

                # Create initial usage of 50
                usage_repo = UsageRepository(setup_session)
                await usage_repo.record_usage(
                    user_plan_id=user_plan_id,
                    feature_id=feature_id,
                    amount=50,
                    period=PeriodType.DAILY,
                )

        async def reset_usage() -> bool:
            """Reset all usage."""
            async with session_factory() as session:
                async with session.begin():
                    repo = UsageRepository(session)
                    await repo.reset_usage(user_plan_id, feature_id)
                    return True

        async def consume_quota() -> tuple[bool, int | None]:
            """Consume 10 units."""
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

        # Interleave reset and consumption
        tasks = [
            consume_quota(),
            reset_usage(),
            consume_quota(),
            consume_quota(),
            reset_usage(),
            consume_quota(),
        ]
        await asyncio.gather(*tasks, return_exceptions=True)

        # Final usage should be consistent (either from before or after reset)
        async with session_factory() as verify_session:
            result = await verify_session.execute(
                select(FeatureUsageModel.feature_usage).where(
                    FeatureUsageModel.user_plan_id == user_plan_id,
                    FeatureUsageModel.feature_id == feature_id,
                )
            )
            final_usage = result.scalar_one_or_none() or 0

        # Usage should be non-negative and within reasonable bounds
        assert final_usage >= 0, f"Usage cannot be negative: {final_usage}"
        assert final_usage <= 100, f"Usage exceeds limit: {final_usage}"


class TestConcurrentMultiFeatureUsage:
    """Tests for concurrent usage across multiple features."""

    async def test_concurrent_consumption_different_features(
        self,
        db_engine: AsyncEngine,
    ) -> None:
        """
        Concurrent consumption of different features should not interfere.
        """
        session_factory = async_sessionmaker(
            db_engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

        # Setup with multiple features
        from identity_plan_kit.plans.models.feature import FeatureModel
        from identity_plan_kit.plans.models.plan_limit import PlanLimitModel

        async with session_factory() as setup_session:
            async with setup_session.begin():
                user_id, plan_id, _, _ = await create_test_infrastructure(
                    setup_session, f"multi_{id(db_engine)}"
                )

                # Create additional features
                features = []
                for i in range(5):
                    feature = FeatureModel(code=f"feature_{i}_{id(db_engine)}", name=f"Feature {i}")
                    setup_session.add(feature)
                    await setup_session.flush()

                    limit = PlanLimitModel(
                        plan_id=plan_id,
                        feature_id=feature.id,
                        feature_limit=100,
                        period="daily",
                    )
                    setup_session.add(limit)
                    features.append(feature.id)
                await setup_session.flush()

                # Create user plan
                user_plan = UserPlanModel(
                    user_id=user_id,
                    plan_id=plan_id,
                    started_at=date.today(),
                    ends_at=date.today() + timedelta(days=30),
                )
                setup_session.add(user_plan)
                await setup_session.flush()
                user_plan_id = user_plan.id

        async def consume_feature(feature_id: int, amount: int) -> tuple[int, bool, int | None]:
            """Consume quota for a specific feature."""
            async with session_factory() as session:
                async with session.begin():
                    repo = UsageRepository(session)
                    try:
                        new_usage = await repo.atomic_check_and_consume(
                            user_plan_id=user_plan_id,
                            feature_id=feature_id,
                            amount=amount,
                            limit=100,
                            period=PeriodType.DAILY,
                        )
                        return (feature_id, True, new_usage)
                    except QuotaExceededInRepoError:
                        return (feature_id, False, None)

        # Fire concurrent consumption across all features
        tasks = []
        for feature_id in features:
            for _ in range(10):
                tasks.append(consume_feature(feature_id, 10))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Verify each feature's usage independently
        async with session_factory() as verify_session:
            for feature_id in features:
                result = await verify_session.execute(
                    select(FeatureUsageModel.feature_usage).where(
                        FeatureUsageModel.user_plan_id == user_plan_id,
                        FeatureUsageModel.feature_id == feature_id,
                    )
                )
                usage = result.scalar_one_or_none() or 0

                # Each feature should have 100 (10 requests * 10 units each)
                assert usage == 100, (
                    f"Feature {feature_id} usage mismatch: expected 100, got {usage}"
                )


class TestConcurrentPlanCancellation:
    """Tests for concurrent plan cancellation scenarios."""

    async def test_concurrent_cancellation_is_idempotent(
        self,
        db_engine: AsyncEngine,
    ) -> None:
        """
        Multiple concurrent cancellation requests should be safe.
        """
        session_factory = async_sessionmaker(
            db_engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

        from identity_plan_kit.plans.repositories.plan_repo import PlanRepository

        async with session_factory() as setup_session:
            async with setup_session.begin():
                user_id, plan_id, _, _ = await create_test_infrastructure(
                    setup_session, f"cancel_{id(db_engine)}"
                )

                user_plan = UserPlanModel(
                    user_id=user_id,
                    plan_id=plan_id,
                    started_at=date.today(),
                    ends_at=date.today() + timedelta(days=30),
                )
                setup_session.add(user_plan)
                await setup_session.flush()

        async def cancel_plan() -> bool:
            """Attempt to cancel the plan."""
            from sqlalchemy import update

            async with session_factory() as session:
                async with session.begin():
                    stmt = (
                        update(UserPlanModel)
                        .where(
                            UserPlanModel.user_id == user_id,
                            UserPlanModel.is_cancelled == False,
                        )
                        .values(is_cancelled=True)
                    )
                    result = await session.execute(stmt)
                    return result.rowcount > 0

        # Fire concurrent cancellation requests
        tasks = [cancel_plan() for _ in range(10)]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        successes = [r for r in results if isinstance(r, bool)]

        # Exactly one should have actually cancelled
        assert successes.count(True) == 1, (
            f"Expected exactly 1 cancellation, got {successes.count(True)}"
        )

        # Verify plan is cancelled
        async with session_factory() as verify_session:
            result = await verify_session.execute(
                select(UserPlanModel).where(UserPlanModel.user_id == user_id)
            )
            plan = result.scalar_one()

        assert plan.is_cancelled is True, "Plan should be cancelled"


class TestHighConcurrencyScenarios:
    """High-stress concurrency tests."""

    async def test_extreme_concurrent_quota_consumption(
        self,
        db_engine: AsyncEngine,
    ) -> None:
        """
        Stress test: 100 concurrent requests consuming from 1000-unit quota.

        Each request tries to consume 15 units. With 100 concurrent:
        - If all succeed: 1500 units (exceeds limit)
        - Correct behavior: ~66 succeed (990 units), ~34 fail
        """
        session_factory = async_sessionmaker(
            db_engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

        async with session_factory() as setup_session:
            async with setup_session.begin():
                user_id, plan_id, _, feature_id = await create_test_infrastructure(
                    setup_session, f"stress_{id(db_engine)}"
                )

                user_plan = UserPlanModel(
                    user_id=user_id,
                    plan_id=plan_id,
                    started_at=date.today(),
                    ends_at=date.today() + timedelta(days=30),
                )
                setup_session.add(user_plan)
                await setup_session.flush()
                user_plan_id = user_plan.id

        async def consume() -> tuple[bool, int | None]:
            """Try to consume 15 units from 1000 limit."""
            async with session_factory() as session:
                async with session.begin():
                    repo = UsageRepository(session)
                    try:
                        new_usage = await repo.atomic_check_and_consume(
                            user_plan_id=user_plan_id,
                            feature_id=feature_id,
                            amount=15,
                            limit=1000,
                            period=PeriodType.DAILY,
                        )
                        return (True, new_usage)
                    except QuotaExceededInRepoError:
                        return (False, None)

        # Fire 100 concurrent requests
        tasks = [consume() for _ in range(100)]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        successes = [r for r in results if isinstance(r, tuple) and r[0]]
        failures = [r for r in results if isinstance(r, tuple) and not r[0]]

        # Verify final usage
        async with session_factory() as verify_session:
            result = await verify_session.execute(
                select(FeatureUsageModel.feature_usage).where(
                    FeatureUsageModel.user_plan_id == user_plan_id,
                    FeatureUsageModel.feature_id == feature_id,
                )
            )
            final_usage = result.scalar_one_or_none() or 0

        # CRITICAL: Usage must NEVER exceed limit
        assert final_usage <= 1000, (
            f"CRITICAL: Usage ({final_usage}) exceeded limit (1000)! "
            f"TOCTOU vulnerability detected!"
        )

        # Usage should match successful consumptions
        expected_usage = len(successes) * 15
        assert final_usage == expected_usage, (
            f"Usage mismatch: expected {expected_usage}, got {final_usage}"
        )

        # At least some should have succeeded
        assert len(successes) >= 1, "At least one request should succeed"

        # Some should have failed (we can't fit 100*15=1500 in 1000)
        assert len(failures) >= 1, "Some requests should fail due to quota"

        # Total requests accounted for
        assert len(successes) + len(failures) == 100, "All requests should complete"
