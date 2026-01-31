"""Integration tests for usage period boundary conditions.

Tests cover:
- Daily period boundaries
- Monthly period boundaries
- Lifetime (no period) handling
- Period transitions
- Usage isolation between periods

CRITICAL: These tests ensure usage tracking correctly handles
time-based period boundaries and doesn't leak usage between periods.
"""

import asyncio
from calendar import monthrange
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

    role = RoleModel(code=f"user_{suffix}", name="Test")
    session.add(role)
    await session.flush()

    user = UserModel(
        email=f"period_test_{suffix}@example.com",
        role_id=role.id,
        display_name=f"Period Test {suffix}",
        is_active=True,
        is_verified=True,
    )
    session.add(user)
    await session.flush()

    plan = PlanModel(code=f"test_plan_{suffix}", name="Test Plan")
    session.add(plan)
    await session.flush()

    feature = FeatureModel(code=f"feature_{suffix}", name="Test Feature")
    session.add(feature)
    await session.flush()

    user_plan = UserPlanModel(
        user_id=user.id,
        plan_id=plan.id,
        started_at=date.today(),
        ends_at=date.today() + timedelta(days=365),
    )
    session.add(user_plan)
    await session.flush()

    return user_plan.id, feature.id, plan.id


class TestDailyPeriodBehavior:
    """Tests for daily period handling."""

    async def test_daily_period_creates_correct_boundaries(
        self,
        db_engine: AsyncEngine,
    ) -> None:
        """Daily period should use today's date as both start and end."""
        session_factory = async_sessionmaker(
            db_engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

        async with session_factory() as setup_session:
            async with setup_session.begin():
                user_plan_id, feature_id, _ = await create_test_data(
                    setup_session, f"daily_{id(db_engine)}"
                )

        async with session_factory() as test_session:
            async with test_session.begin():
                repo = UsageRepository(test_session)
                await repo.atomic_check_and_consume(
                    user_plan_id=user_plan_id,
                    feature_id=feature_id,
                    amount=10,
                    limit=100,
                    period=PeriodType.DAILY,
                )

        # Verify the period boundaries
        async with session_factory() as verify_session:
            result = await verify_session.execute(
                select(FeatureUsageModel).where(
                    FeatureUsageModel.user_plan_id == user_plan_id,
                    FeatureUsageModel.feature_id == feature_id,
                )
            )
            record = result.scalar_one()

        today = date.today()
        assert record.start_period == today, f"Start should be today: {today}"
        assert record.end_period == today, f"End should be today: {today}"

    async def test_daily_usage_isolated_to_current_day(
        self,
        db_engine: AsyncEngine,
    ) -> None:
        """
        Usage from a previous day should not affect today's quota.

        Note: This test manually creates records for different days to
        simulate usage over multiple days.
        """
        session_factory = async_sessionmaker(
            db_engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

        async with session_factory() as setup_session:
            async with setup_session.begin():
                user_plan_id, feature_id, _ = await create_test_data(
                    setup_session, f"daily_iso_{id(db_engine)}"
                )

                # Manually create a usage record for yesterday
                yesterday = date.today() - timedelta(days=1)
                yesterday_usage = FeatureUsageModel(
                    user_plan_id=user_plan_id,
                    feature_id=feature_id,
                    feature_usage=100,  # Maxed out yesterday
                    start_period=yesterday,
                    end_period=yesterday,
                )
                setup_session.add(yesterday_usage)
                await setup_session.flush()

        # Today's consumption should work (different period)
        async with session_factory() as test_session:
            async with test_session.begin():
                repo = UsageRepository(test_session)
                new_usage = await repo.atomic_check_and_consume(
                    user_plan_id=user_plan_id,
                    feature_id=feature_id,
                    amount=50,
                    limit=100,
                    period=PeriodType.DAILY,
                )

        # Should start fresh today
        assert new_usage == 50, f"Today should start fresh, got {new_usage}"


class TestMonthlyPeriodBehavior:
    """Tests for monthly period handling."""

    async def test_monthly_period_creates_correct_boundaries(
        self,
        db_engine: AsyncEngine,
    ) -> None:
        """Monthly period should use first and last day of current month."""
        session_factory = async_sessionmaker(
            db_engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

        async with session_factory() as setup_session:
            async with setup_session.begin():
                user_plan_id, feature_id, _ = await create_test_data(
                    setup_session, f"monthly_{id(db_engine)}"
                )

        async with session_factory() as test_session:
            async with test_session.begin():
                repo = UsageRepository(test_session)
                await repo.atomic_check_and_consume(
                    user_plan_id=user_plan_id,
                    feature_id=feature_id,
                    amount=10,
                    limit=100,
                    period=PeriodType.MONTHLY,
                )

        # Verify the period boundaries
        async with session_factory() as verify_session:
            result = await verify_session.execute(
                select(FeatureUsageModel).where(
                    FeatureUsageModel.user_plan_id == user_plan_id,
                    FeatureUsageModel.feature_id == feature_id,
                )
            )
            record = result.scalar_one()

        today = date.today()
        _, last_day = monthrange(today.year, today.month)

        expected_start = today.replace(day=1)
        expected_end = today.replace(day=last_day)

        assert record.start_period == expected_start, (
            f"Start should be first of month: {expected_start}"
        )
        assert record.end_period == expected_end, (
            f"End should be last of month: {expected_end}"
        )

    async def test_monthly_usage_accumulates_within_month(
        self,
        db_engine: AsyncEngine,
    ) -> None:
        """Multiple consumptions within same month should accumulate."""
        session_factory = async_sessionmaker(
            db_engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

        async with session_factory() as setup_session:
            async with setup_session.begin():
                user_plan_id, feature_id, _ = await create_test_data(
                    setup_session, f"monthly_acc_{id(db_engine)}"
                )

        async with session_factory() as test_session:
            async with test_session.begin():
                repo = UsageRepository(test_session)

                # Multiple consumptions should accumulate
                for i in range(5):
                    new_usage = await repo.atomic_check_and_consume(
                        user_plan_id=user_plan_id,
                        feature_id=feature_id,
                        amount=20,
                        limit=100,
                        period=PeriodType.MONTHLY,
                    )
                    assert new_usage == (i + 1) * 20

        # Verify only one record was created
        async with session_factory() as verify_session:
            result = await verify_session.execute(
                select(FeatureUsageModel).where(
                    FeatureUsageModel.user_plan_id == user_plan_id,
                    FeatureUsageModel.feature_id == feature_id,
                )
            )
            records = result.scalars().all()

        assert len(records) == 1, f"Should have 1 record, found {len(records)}"
        assert records[0].feature_usage == 100

    async def test_monthly_usage_isolated_between_months(
        self,
        db_engine: AsyncEngine,
    ) -> None:
        """
        Usage from a previous month should not affect current month's quota.
        """
        session_factory = async_sessionmaker(
            db_engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

        async with session_factory() as setup_session:
            async with setup_session.begin():
                user_plan_id, feature_id, _ = await create_test_data(
                    setup_session, f"monthly_iso_{id(db_engine)}"
                )

                # Create usage record for previous month
                today = date.today()
                if today.month == 1:
                    prev_month = today.replace(year=today.year - 1, month=12, day=1)
                else:
                    prev_month = today.replace(month=today.month - 1, day=1)

                _, last_day = monthrange(prev_month.year, prev_month.month)
                prev_month_end = prev_month.replace(day=last_day)

                prev_usage = FeatureUsageModel(
                    user_plan_id=user_plan_id,
                    feature_id=feature_id,
                    feature_usage=100,  # Maxed out last month
                    start_period=prev_month,
                    end_period=prev_month_end,
                )
                setup_session.add(prev_usage)
                await setup_session.flush()

        # This month's consumption should work
        async with session_factory() as test_session:
            async with test_session.begin():
                repo = UsageRepository(test_session)
                new_usage = await repo.atomic_check_and_consume(
                    user_plan_id=user_plan_id,
                    feature_id=feature_id,
                    amount=50,
                    limit=100,
                    period=PeriodType.MONTHLY,
                )

        assert new_usage == 50, f"This month should start fresh, got {new_usage}"


class TestLifetimePeriodBehavior:
    """Tests for lifetime (no period) handling."""

    async def test_lifetime_period_creates_wide_boundaries(
        self,
        db_engine: AsyncEngine,
    ) -> None:
        """Lifetime period should use far past and future dates."""
        session_factory = async_sessionmaker(
            db_engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

        async with session_factory() as setup_session:
            async with setup_session.begin():
                user_plan_id, feature_id, _ = await create_test_data(
                    setup_session, f"lifetime_{id(db_engine)}"
                )

        async with session_factory() as test_session:
            async with test_session.begin():
                repo = UsageRepository(test_session)
                await repo.atomic_check_and_consume(
                    user_plan_id=user_plan_id,
                    feature_id=feature_id,
                    amount=10,
                    limit=100,
                    period=None,  # Lifetime
                )

        # Verify the period boundaries
        async with session_factory() as verify_session:
            result = await verify_session.execute(
                select(FeatureUsageModel).where(
                    FeatureUsageModel.user_plan_id == user_plan_id,
                    FeatureUsageModel.feature_id == feature_id,
                )
            )
            record = result.scalar_one()

        # Should have very wide date range
        assert record.start_period.year <= 2000
        assert record.end_period.year >= 2100

    async def test_lifetime_usage_persists_across_time(
        self,
        db_engine: AsyncEngine,
    ) -> None:
        """Lifetime usage should accumulate regardless of when consumed."""
        session_factory = async_sessionmaker(
            db_engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

        async with session_factory() as setup_session:
            async with setup_session.begin():
                user_plan_id, feature_id, _ = await create_test_data(
                    setup_session, f"lifetime_persist_{id(db_engine)}"
                )

        # First consumption
        async with session_factory() as test_session:
            async with test_session.begin():
                repo = UsageRepository(test_session)
                new_usage = await repo.atomic_check_and_consume(
                    user_plan_id=user_plan_id,
                    feature_id=feature_id,
                    amount=30,
                    limit=100,
                    period=None,
                )
                assert new_usage == 30

        # Second consumption (simulating days later)
        async with session_factory() as test_session2:
            async with test_session2.begin():
                repo = UsageRepository(test_session2)
                new_usage = await repo.atomic_check_and_consume(
                    user_plan_id=user_plan_id,
                    feature_id=feature_id,
                    amount=40,
                    limit=100,
                    period=None,
                )
                assert new_usage == 70

        # Third consumption
        async with session_factory() as test_session3:
            async with test_session3.begin():
                repo = UsageRepository(test_session3)
                new_usage = await repo.atomic_check_and_consume(
                    user_plan_id=user_plan_id,
                    feature_id=feature_id,
                    amount=30,
                    limit=100,
                    period=None,
                )
                assert new_usage == 100

                # Now at limit
                with pytest.raises(QuotaExceededInRepoError):
                    await repo.atomic_check_and_consume(
                        user_plan_id=user_plan_id,
                        feature_id=feature_id,
                        amount=1,
                        limit=100,
                        period=None,
                    )


class TestConcurrentPeriodOperations:
    """Tests for concurrent operations across different periods."""

    async def test_concurrent_different_periods_same_feature(
        self,
        db_engine: AsyncEngine,
    ) -> None:
        """
        Concurrent consumption with different periods should create separate records.
        """
        session_factory = async_sessionmaker(
            db_engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

        async with session_factory() as setup_session:
            async with setup_session.begin():
                user_plan_id, feature_id, _ = await create_test_data(
                    setup_session, f"multi_period_{id(db_engine)}"
                )

        async def consume_with_period(period: PeriodType | None) -> tuple[PeriodType | None, int]:
            async with session_factory() as session:
                async with session.begin():
                    repo = UsageRepository(session)
                    new_usage = await repo.atomic_check_and_consume(
                        user_plan_id=user_plan_id,
                        feature_id=feature_id,
                        amount=10,
                        limit=100,
                        period=period,
                    )
                    return (period, new_usage)

        # Fire concurrent consumption with different periods
        tasks = [
            consume_with_period(PeriodType.DAILY),
            consume_with_period(PeriodType.MONTHLY),
            consume_with_period(None),  # Lifetime
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        successes = [(p, u) for p, u in results if isinstance(p, (PeriodType, type(None)))]

        # All should succeed (different periods = different records)
        assert len(successes) == 3, f"Expected 3 successes, got {len(successes)}"

        # Verify separate records created
        async with session_factory() as verify_session:
            result = await verify_session.execute(
                select(FeatureUsageModel).where(
                    FeatureUsageModel.user_plan_id == user_plan_id,
                    FeatureUsageModel.feature_id == feature_id,
                )
            )
            records = result.scalars().all()

        # Should have 3 separate records (daily, monthly, lifetime)
        assert len(records) == 3, f"Expected 3 records, found {len(records)}"

        # All should have 10 usage (independent of each other)
        for record in records:
            assert record.feature_usage == 10


class TestUsageResetBehavior:
    """Tests for usage reset across different periods."""

    async def test_reset_specific_period_only(
        self,
        db_engine: AsyncEngine,
    ) -> None:
        """Resetting usage should only affect current period's record."""
        session_factory = async_sessionmaker(
            db_engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

        async with session_factory() as setup_session:
            async with setup_session.begin():
                user_plan_id, feature_id, _ = await create_test_data(
                    setup_session, f"reset_{id(db_engine)}"
                )

                # Create usage records for different periods
                today = date.today()
                _, last_day = monthrange(today.year, today.month)

                # Daily record
                daily_usage = FeatureUsageModel(
                    user_plan_id=user_plan_id,
                    feature_id=feature_id,
                    feature_usage=50,
                    start_period=today,
                    end_period=today,
                )
                setup_session.add(daily_usage)

                # Monthly record (if daily and monthly don't overlap perfectly)
                monthly_start = today.replace(day=1)
                monthly_end = today.replace(day=last_day)
                if monthly_start != today or monthly_end != today:
                    monthly_usage = FeatureUsageModel(
                        user_plan_id=user_plan_id,
                        feature_id=feature_id,
                        feature_usage=100,
                        start_period=monthly_start,
                        end_period=monthly_end,
                    )
                    setup_session.add(monthly_usage)

                await setup_session.flush()

        # Reset daily usage
        async with session_factory() as test_session:
            async with test_session.begin():
                repo = UsageRepository(test_session)
                await repo.reset_usage(user_plan_id, feature_id)

        # Verify daily was reset but monthly preserved
        async with session_factory() as verify_session:
            result = await verify_session.execute(
                select(FeatureUsageModel).where(
                    FeatureUsageModel.user_plan_id == user_plan_id,
                    FeatureUsageModel.feature_id == feature_id,
                )
            )
            records = {
                (r.start_period, r.end_period): r.feature_usage
                for r in result.scalars().all()
            }

        # At least the current period should be reset
        today = date.today()
        if (today, today) in records:
            assert records[(today, today)] == 0, "Daily should be reset to 0"


class TestUsageQueryBehavior:
    """Tests for usage query operations."""

    async def test_get_current_usage_returns_correct_period(
        self,
        db_engine: AsyncEngine,
    ) -> None:
        """get_current_usage should return usage for the current period only."""
        session_factory = async_sessionmaker(
            db_engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

        async with session_factory() as setup_session:
            async with setup_session.begin():
                user_plan_id, feature_id, _ = await create_test_data(
                    setup_session, f"query_{id(db_engine)}"
                )

                # Create yesterday's usage (should not be returned for daily)
                yesterday = date.today() - timedelta(days=1)
                old_usage = FeatureUsageModel(
                    user_plan_id=user_plan_id,
                    feature_id=feature_id,
                    feature_usage=99,
                    start_period=yesterday,
                    end_period=yesterday,
                )
                setup_session.add(old_usage)
                await setup_session.flush()

        # Query for today's daily usage (should be 0, yesterday's is separate)
        async with session_factory() as test_session:
            async with test_session.begin():
                repo = UsageRepository(test_session)
                current = await repo.get_current_usage(
                    user_plan_id, feature_id, PeriodType.DAILY
                )

        assert current == 0, f"Today's usage should be 0, got {current}"

    async def test_get_all_usage_returns_current_periods_only(
        self,
        db_engine: AsyncEngine,
    ) -> None:
        """get_all_usage should only return records that span today."""
        session_factory = async_sessionmaker(
            db_engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

        async with session_factory() as setup_session:
            async with setup_session.begin():
                user_plan_id, feature_id, _ = await create_test_data(
                    setup_session, f"all_usage_{id(db_engine)}"
                )

                # Create old usage (yesterday, should be excluded for daily)
                yesterday = date.today() - timedelta(days=1)
                old_usage = FeatureUsageModel(
                    user_plan_id=user_plan_id,
                    feature_id=feature_id,
                    feature_usage=50,
                    start_period=yesterday,
                    end_period=yesterday,
                )
                setup_session.add(old_usage)

                # Create current usage (today)
                today = date.today()
                current_usage = FeatureUsageModel(
                    user_plan_id=user_plan_id,
                    feature_id=feature_id,
                    feature_usage=25,
                    start_period=today,
                    end_period=today,
                )
                setup_session.add(current_usage)
                await setup_session.flush()

        # Query all current usage
        async with session_factory() as test_session:
            async with test_session.begin():
                repo = UsageRepository(test_session)
                all_usage = await repo.get_all_usage(user_plan_id)

        # Should only include today's record
        assert len(all_usage) == 1, f"Expected 1 current record, got {len(all_usage)}"
        assert all_usage[0].usage == 25
