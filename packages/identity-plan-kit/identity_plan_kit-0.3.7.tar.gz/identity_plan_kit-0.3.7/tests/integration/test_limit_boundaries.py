"""Integration tests for limit boundary conditions.

Tests edge cases in quota/limit enforcement:
- Zero limits
- Very large limits
- Integer boundary values
- Negative amounts (should fail validation)
- Overflow scenarios

CRITICAL: These tests ensure the system handles edge cases correctly
and doesn't have integer overflow or boundary vulnerabilities.
"""

import asyncio
from datetime import date, timedelta
from uuid import UUID

import pytest
from sqlalchemy import select
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


async def create_test_data(session: AsyncSession, suffix: str) -> tuple[UUID, int, int]:
    """Create test data and return (user_plan_id, feature_id, plan_id)."""
    from identity_plan_kit.auth.models.user import UserModel
    from identity_plan_kit.plans.models.feature import FeatureModel
    from identity_plan_kit.plans.models.plan import PlanModel
    from identity_plan_kit.rbac.models.role import RoleModel

    # Create role and user
    role = RoleModel(code=f"user_{suffix}", name="Test")
    session.add(role)
    await session.flush()

    user = UserModel(
        email=f"limit_test_{suffix}@example.com",
        role_id=role.id,
        display_name=f"Limit Test {suffix}",
        is_active=True,
        is_verified=True,
    )
    session.add(user)
    await session.flush()

    # Create plan and feature
    plan = PlanModel(code=f"test_plan_{suffix}", name="Test Plan")
    session.add(plan)
    await session.flush()

    feature = FeatureModel(code=f"feature_{suffix}", name="Test Feature")
    session.add(feature)
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

    return user_plan.id, feature.id, plan.id


class TestZeroLimitBehavior:
    """Tests for zero limit handling."""

    async def test_zero_limit_rejects_all_consumption(
        self,
        db_engine: AsyncEngine,
    ) -> None:
        """
        A limit of 0 should reject any consumption, even 1 unit.

        This is important for features that are disabled in certain plans.
        """
        session_factory = async_sessionmaker(
            db_engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

        async with session_factory() as setup_session:
            async with setup_session.begin():
                user_plan_id, feature_id, _ = await create_test_data(
                    setup_session, f"zero_{id(db_engine)}"
                )

        async with session_factory() as test_session:
            async with test_session.begin():
                repo = UsageRepository(test_session)

                # Even 1 unit should fail with limit 0
                with pytest.raises(QuotaExceededInRepoError) as exc_info:
                    await repo.atomic_check_and_consume(
                        user_plan_id=user_plan_id,
                        feature_id=feature_id,
                        amount=1,
                        limit=0,
                        period=PeriodType.DAILY,
                    )

                assert exc_info.value.limit == 0
                assert exc_info.value.requested == 1
                assert exc_info.value.current_usage == 0

    async def test_zero_amount_consumption_succeeds(
        self,
        db_engine: AsyncEngine,
    ) -> None:
        """
        Consuming 0 units should succeed (no-op but valid).
        """
        session_factory = async_sessionmaker(
            db_engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

        async with session_factory() as setup_session:
            async with setup_session.begin():
                user_plan_id, feature_id, _ = await create_test_data(
                    setup_session, f"zero_amt_{id(db_engine)}"
                )

        async with session_factory() as test_session:
            async with test_session.begin():
                repo = UsageRepository(test_session)

                # Consuming 0 should work (returns 0)
                new_usage = await repo.atomic_check_and_consume(
                    user_plan_id=user_plan_id,
                    feature_id=feature_id,
                    amount=0,
                    limit=100,
                    period=PeriodType.DAILY,
                )

                assert new_usage == 0


class TestLargeNumberHandling:
    """Tests for very large numbers."""

    async def test_large_limit_works_correctly(
        self,
        db_engine: AsyncEngine,
    ) -> None:
        """
        Very large limits (billions) should work without overflow.
        """
        session_factory = async_sessionmaker(
            db_engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

        async with session_factory() as setup_session:
            async with setup_session.begin():
                user_plan_id, feature_id, _ = await create_test_data(
                    setup_session, f"large_{id(db_engine)}"
                )

        large_limit = 2_000_000_000  # 2 billion

        async with session_factory() as test_session:
            async with test_session.begin():
                repo = UsageRepository(test_session)

                # Should succeed with large limit
                new_usage = await repo.atomic_check_and_consume(
                    user_plan_id=user_plan_id,
                    feature_id=feature_id,
                    amount=1_000_000_000,  # 1 billion
                    limit=large_limit,
                    period=PeriodType.DAILY,
                )

                assert new_usage == 1_000_000_000

                # Second consumption should also work
                new_usage = await repo.atomic_check_and_consume(
                    user_plan_id=user_plan_id,
                    feature_id=feature_id,
                    amount=500_000_000,  # 500 million
                    limit=large_limit,
                    period=PeriodType.DAILY,
                )

                assert new_usage == 1_500_000_000

    async def test_large_consumption_at_limit_boundary(
        self,
        db_engine: AsyncEngine,
    ) -> None:
        """
        Large consumption at exactly the limit should work.
        """
        session_factory = async_sessionmaker(
            db_engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

        async with session_factory() as setup_session:
            async with setup_session.begin():
                user_plan_id, feature_id, _ = await create_test_data(
                    setup_session, f"boundary_{id(db_engine)}"
                )

        large_limit = 1_000_000_000  # 1 billion

        async with session_factory() as test_session:
            async with test_session.begin():
                repo = UsageRepository(test_session)

                # Consume exactly the limit
                new_usage = await repo.atomic_check_and_consume(
                    user_plan_id=user_plan_id,
                    feature_id=feature_id,
                    amount=large_limit,
                    limit=large_limit,
                    period=PeriodType.DAILY,
                )

                assert new_usage == large_limit

                # Any more should fail
                with pytest.raises(QuotaExceededInRepoError):
                    await repo.atomic_check_and_consume(
                        user_plan_id=user_plan_id,
                        feature_id=feature_id,
                        amount=1,
                        limit=large_limit,
                        period=PeriodType.DAILY,
                    )


class TestBoundaryConditions:
    """Tests for exact boundary conditions."""

    async def test_consumption_at_exact_remaining_capacity(
        self,
        db_engine: AsyncEngine,
    ) -> None:
        """
        Consuming exactly the remaining capacity should succeed.
        """
        session_factory = async_sessionmaker(
            db_engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

        async with session_factory() as setup_session:
            async with setup_session.begin():
                user_plan_id, feature_id, _ = await create_test_data(
                    setup_session, f"exact_{id(db_engine)}"
                )

        async with session_factory() as test_session:
            async with test_session.begin():
                repo = UsageRepository(test_session)

                # Consume 90 out of 100
                await repo.atomic_check_and_consume(
                    user_plan_id=user_plan_id,
                    feature_id=feature_id,
                    amount=90,
                    limit=100,
                    period=PeriodType.DAILY,
                )

                # Consume exactly remaining 10
                new_usage = await repo.atomic_check_and_consume(
                    user_plan_id=user_plan_id,
                    feature_id=feature_id,
                    amount=10,
                    limit=100,
                    period=PeriodType.DAILY,
                )

                assert new_usage == 100

                # Now even 1 more should fail
                with pytest.raises(QuotaExceededInRepoError) as exc_info:
                    await repo.atomic_check_and_consume(
                        user_plan_id=user_plan_id,
                        feature_id=feature_id,
                        amount=1,
                        limit=100,
                        period=PeriodType.DAILY,
                    )

                assert exc_info.value.current_usage == 100
                assert exc_info.value.limit == 100

    async def test_consumption_one_over_remaining(
        self,
        db_engine: AsyncEngine,
    ) -> None:
        """
        Consuming one unit more than remaining should fail.
        """
        session_factory = async_sessionmaker(
            db_engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

        async with session_factory() as setup_session:
            async with setup_session.begin():
                user_plan_id, feature_id, _ = await create_test_data(
                    setup_session, f"over_{id(db_engine)}"
                )

        async with session_factory() as test_session:
            async with test_session.begin():
                repo = UsageRepository(test_session)

                # Consume 95 out of 100
                await repo.atomic_check_and_consume(
                    user_plan_id=user_plan_id,
                    feature_id=feature_id,
                    amount=95,
                    limit=100,
                    period=PeriodType.DAILY,
                )

                # Try to consume 6 (only 5 remaining) - should fail
                with pytest.raises(QuotaExceededInRepoError) as exc_info:
                    await repo.atomic_check_and_consume(
                        user_plan_id=user_plan_id,
                        feature_id=feature_id,
                        amount=6,
                        limit=100,
                        period=PeriodType.DAILY,
                    )

                assert exc_info.value.current_usage == 95
                assert exc_info.value.requested == 6
                assert exc_info.value.limit == 100

                # But consuming exactly 5 should work
                new_usage = await repo.atomic_check_and_consume(
                    user_plan_id=user_plan_id,
                    feature_id=feature_id,
                    amount=5,
                    limit=100,
                    period=PeriodType.DAILY,
                )

                assert new_usage == 100


class TestUnlimitedQuota:
    """Tests for unlimited (-1) quota handling."""

    async def test_unlimited_accepts_any_amount(
        self,
        db_engine: AsyncEngine,
    ) -> None:
        """
        Unlimited quota (-1) should accept any consumption amount.
        """
        session_factory = async_sessionmaker(
            db_engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

        async with session_factory() as setup_session:
            async with setup_session.begin():
                user_plan_id, feature_id, _ = await create_test_data(
                    setup_session, f"unlimited_{id(db_engine)}"
                )

        async with session_factory() as test_session:
            async with test_session.begin():
                repo = UsageRepository(test_session)

                # Very large amount should work
                new_usage = await repo.atomic_check_and_consume(
                    user_plan_id=user_plan_id,
                    feature_id=feature_id,
                    amount=1_000_000_000,
                    limit=-1,  # Unlimited
                    period=PeriodType.DAILY,
                )

                assert new_usage == 1_000_000_000

                # Even more should still work
                new_usage = await repo.atomic_check_and_consume(
                    user_plan_id=user_plan_id,
                    feature_id=feature_id,
                    amount=1_000_000_000,
                    limit=-1,
                    period=PeriodType.DAILY,
                )

                assert new_usage == 2_000_000_000

    async def test_unlimited_concurrent_consumption(
        self,
        db_engine: AsyncEngine,
    ) -> None:
        """
        Concurrent consumption with unlimited quota should all succeed.
        """
        session_factory = async_sessionmaker(
            db_engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

        async with session_factory() as setup_session:
            async with setup_session.begin():
                user_plan_id, feature_id, _ = await create_test_data(
                    setup_session, f"unlimited_conc_{id(db_engine)}"
                )

        async def consume() -> int:
            async with session_factory() as session:
                async with session.begin():
                    repo = UsageRepository(session)
                    return await repo.atomic_check_and_consume(
                        user_plan_id=user_plan_id,
                        feature_id=feature_id,
                        amount=1000,
                        limit=-1,
                        period=PeriodType.DAILY,
                    )

        # Fire 50 concurrent requests
        tasks = [consume() for _ in range(50)]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        successes = [r for r in results if isinstance(r, int)]

        # ALL should succeed
        assert len(successes) == 50, "All unlimited requests should succeed"

        # Verify final usage
        async with session_factory() as verify_session:
            result = await verify_session.execute(
                select(FeatureUsageModel.feature_usage).where(
                    FeatureUsageModel.user_plan_id == user_plan_id,
                    FeatureUsageModel.feature_id == feature_id,
                )
            )
            final_usage = result.scalar_one_or_none() or 0

        assert final_usage == 50_000, f"Expected 50000, got {final_usage}"


class TestIncrementalConsumption:
    """Tests for incremental consumption patterns."""

    async def test_many_small_increments_to_limit(
        self,
        db_engine: AsyncEngine,
    ) -> None:
        """
        Many small increments should correctly track to the limit.
        """
        session_factory = async_sessionmaker(
            db_engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

        async with session_factory() as setup_session:
            async with setup_session.begin():
                user_plan_id, feature_id, _ = await create_test_data(
                    setup_session, f"incremental_{id(db_engine)}"
                )

        async with session_factory() as test_session:
            async with test_session.begin():
                repo = UsageRepository(test_session)

                # Consume 1 unit at a time, 100 times
                for i in range(100):
                    new_usage = await repo.atomic_check_and_consume(
                        user_plan_id=user_plan_id,
                        feature_id=feature_id,
                        amount=1,
                        limit=100,
                        period=PeriodType.DAILY,
                    )
                    assert new_usage == i + 1

                # 101st should fail
                with pytest.raises(QuotaExceededInRepoError):
                    await repo.atomic_check_and_consume(
                        user_plan_id=user_plan_id,
                        feature_id=feature_id,
                        amount=1,
                        limit=100,
                        period=PeriodType.DAILY,
                    )

    async def test_concurrent_incremental_consumption(
        self,
        db_engine: AsyncEngine,
    ) -> None:
        """
        Concurrent small increments should respect the total limit.
        """
        session_factory = async_sessionmaker(
            db_engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

        async with session_factory() as setup_session:
            async with setup_session.begin():
                user_plan_id, feature_id, _ = await create_test_data(
                    setup_session, f"conc_inc_{id(db_engine)}"
                )

        async def consume_one() -> tuple[bool, int | None]:
            async with session_factory() as session:
                async with session.begin():
                    repo = UsageRepository(session)
                    try:
                        new_usage = await repo.atomic_check_and_consume(
                            user_plan_id=user_plan_id,
                            feature_id=feature_id,
                            amount=1,
                            limit=100,
                            period=PeriodType.DAILY,
                        )
                        return (True, new_usage)
                    except QuotaExceededInRepoError:
                        return (False, None)

        # Fire 200 concurrent single-unit consumptions
        tasks = [consume_one() for _ in range(200)]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        successes = [r for r in results if isinstance(r, tuple) and r[0]]
        failures = [r for r in results if isinstance(r, tuple) and not r[0]]

        # Verify counts
        async with session_factory() as verify_session:
            result = await verify_session.execute(
                select(FeatureUsageModel.feature_usage).where(
                    FeatureUsageModel.user_plan_id == user_plan_id,
                    FeatureUsageModel.feature_id == feature_id,
                )
            )
            final_usage = result.scalar_one_or_none() or 0

        # CRITICAL: Usage must not exceed limit
        assert final_usage <= 100, (
            f"CRITICAL: Usage ({final_usage}) exceeded limit (100)!"
        )

        # Exactly 100 should have succeeded
        assert len(successes) == 100, (
            f"Expected 100 successes, got {len(successes)}"
        )

        # 100 should have failed
        assert len(failures) == 100, (
            f"Expected 100 failures, got {len(failures)}"
        )

        # Final usage should be exactly 100
        assert final_usage == 100, f"Expected usage 100, got {final_usage}"


class TestUsageRecordCreation:
    """Tests for usage record creation edge cases."""

    async def test_first_consumption_creates_record(
        self,
        db_engine: AsyncEngine,
    ) -> None:
        """
        First consumption should create a new usage record.
        """
        session_factory = async_sessionmaker(
            db_engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

        async with session_factory() as setup_session:
            async with setup_session.begin():
                user_plan_id, feature_id, _ = await create_test_data(
                    setup_session, f"first_{id(db_engine)}"
                )

        # Verify no record exists yet
        async with session_factory() as check_session:
            result = await check_session.execute(
                select(FeatureUsageModel).where(
                    FeatureUsageModel.user_plan_id == user_plan_id,
                    FeatureUsageModel.feature_id == feature_id,
                )
            )
            existing = result.scalar_one_or_none()
            assert existing is None, "No usage record should exist yet"

        # First consumption creates record
        async with session_factory() as test_session:
            async with test_session.begin():
                repo = UsageRepository(test_session)
                new_usage = await repo.atomic_check_and_consume(
                    user_plan_id=user_plan_id,
                    feature_id=feature_id,
                    amount=10,
                    limit=100,
                    period=PeriodType.DAILY,
                )
                assert new_usage == 10

        # Verify record was created
        async with session_factory() as verify_session:
            result = await verify_session.execute(
                select(FeatureUsageModel).where(
                    FeatureUsageModel.user_plan_id == user_plan_id,
                    FeatureUsageModel.feature_id == feature_id,
                )
            )
            record = result.scalar_one()
            assert record.feature_usage == 10

    async def test_concurrent_first_consumption(
        self,
        db_engine: AsyncEngine,
    ) -> None:
        """
        Concurrent first consumption should not create duplicate records.
        """
        session_factory = async_sessionmaker(
            db_engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

        async with session_factory() as setup_session:
            async with setup_session.begin():
                user_plan_id, feature_id, _ = await create_test_data(
                    setup_session, f"conc_first_{id(db_engine)}"
                )

        async def first_consume() -> tuple[bool, int | None]:
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
                    except Exception:
                        return (False, None)

        # Fire 10 concurrent first consumptions
        tasks = [first_consume() for _ in range(10)]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        successes = [r for r in results if isinstance(r, tuple) and r[0]]

        # All should succeed (upsert handles concurrent insert)
        assert len(successes) == 10, f"Expected 10 successes, got {len(successes)}"

        # Verify only ONE record exists
        async with session_factory() as verify_session:
            result = await verify_session.execute(
                select(FeatureUsageModel).where(
                    FeatureUsageModel.user_plan_id == user_plan_id,
                    FeatureUsageModel.feature_id == feature_id,
                )
            )
            records = result.scalars().all()

        assert len(records) == 1, (
            f"Expected 1 usage record, found {len(records)}"
        )

        # Final usage should be exactly 100 (10 requests * 10 units)
        assert records[0].feature_usage == 100
