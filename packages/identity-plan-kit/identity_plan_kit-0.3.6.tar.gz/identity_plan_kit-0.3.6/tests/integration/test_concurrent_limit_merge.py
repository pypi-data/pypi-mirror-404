"""Integration tests for concurrent limit merge operations.

Tests the FOR UPDATE locking added to prevent lost updates when multiple
concurrent requests try to update user plan custom_limits simultaneously.

CRITICAL: Without proper locking, concurrent limit updates could lose changes:
1. Request A reads custom_limits = {"api_calls": 100}
2. Request B reads custom_limits = {"api_calls": 100}
3. Request A writes {"api_calls": 100, "storage": 500}
4. Request B writes {"api_calls": 100, "downloads": 200}
   -> Lost update! storage limit from Request A is gone

With FOR UPDATE locking:
1. Request A reads (locks row) custom_limits = {"api_calls": 100}
2. Request B waits for lock
3. Request A writes {"api_calls": 100, "storage": 500}, releases lock
4. Request B reads (locks row) {"api_calls": 100, "storage": 500}
5. Request B writes {"api_calls": 100, "storage": 500, "downloads": 200}
   -> No lost update! Both changes preserved
"""

import asyncio
from datetime import date, timedelta
from uuid import UUID, uuid4

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
)

from identity_plan_kit.plans.models.user_plan import UserPlanModel

# Skip if testcontainers not available
pytest.importorskip("testcontainers")


async def create_test_infrastructure(
    session: AsyncSession,
    suffix: str,
) -> tuple[UUID, UUID]:
    """Create required test data and return (user_id, user_plan_id)."""
    from identity_plan_kit.auth.models.user import UserModel
    from identity_plan_kit.plans.models.plan import PlanModel
    from identity_plan_kit.rbac.models.role import RoleModel

    # Create role
    role = RoleModel(code=f"role_{suffix}", name="Test Role")
    session.add(role)
    await session.flush()

    # Create user
    user = UserModel(
        email=f"limit_test_{suffix}@example.com",
        role_id=role.id,
        display_name=f"Limit Test {suffix}",
        is_active=True,
        is_verified=True,
    )
    session.add(user)
    await session.flush()

    # Create plan
    plan = PlanModel(code=f"plan_{suffix}", name="Test Plan")
    session.add(plan)
    await session.flush()

    # Create user plan with empty custom_limits
    user_plan = UserPlanModel(
        user_id=user.id,
        plan_id=plan.id,
        started_at=date.today(),
        ends_at=date.today() + timedelta(days=30),
        custom_limits={},
    )
    session.add(user_plan)
    await session.flush()

    return user.id, user_plan.id


class TestConcurrentLimitMerge:
    """Integration tests for concurrent custom_limits merge operations."""

    async def test_concurrent_limit_updates_preserve_all_changes(
        self,
        db_engine: AsyncEngine,
    ) -> None:
        """
        CRITICAL: Concurrent limit updates must preserve ALL changes.

        This test fires multiple concurrent updates, each adding a different
        limit. All limits must be present in the final result.
        """
        session_factory = async_sessionmaker(
            db_engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

        # Setup
        unique_id = uuid4().hex[:8]
        async with session_factory() as setup_session:
            async with setup_session.begin():
                user_id, user_plan_id = await create_test_infrastructure(
                    setup_session, unique_id
                )

        # Track which updates completed successfully
        completed_updates: list[str] = []
        results_lock = asyncio.Lock()

        async def update_limit(feature_code: str, limit_value: int) -> bool:
            """Update a specific limit using FOR UPDATE locking."""
            async with session_factory() as session:
                async with session.begin():
                    # Read with FOR UPDATE lock (simulates what plan_service does)
                    stmt = (
                        select(UserPlanModel)
                        .where(UserPlanModel.id == user_plan_id)
                        .with_for_update()
                    )
                    result = await session.execute(stmt)
                    user_plan = result.scalar_one()

                    # Merge new limit with existing
                    current_limits = dict(user_plan.custom_limits or {})
                    current_limits[feature_code] = limit_value
                    user_plan.custom_limits = current_limits

                    await session.flush()

                    async with results_lock:
                        completed_updates.append(feature_code)

                    return True

        # Fire 10 concurrent updates, each adding a different feature limit
        features = [f"feature_{i}" for i in range(10)]
        tasks = [update_limit(feat, (i + 1) * 100) for i, feat in enumerate(features)]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # All updates should succeed (no exceptions)
        exceptions = [r for r in results if isinstance(r, Exception)]
        assert len(exceptions) == 0, f"Updates failed with exceptions: {exceptions}"

        # Verify final state contains ALL limits
        async with session_factory() as verify_session:
            result = await verify_session.execute(
                select(UserPlanModel).where(UserPlanModel.id == user_plan_id)
            )
            final_plan = result.scalar_one()
            final_limits = final_plan.custom_limits or {}

        # CRITICAL ASSERTION: All feature limits must be present
        missing_features = [f for f in features if f not in final_limits]
        assert len(missing_features) == 0, (
            f"LOST UPDATE DETECTED! Missing features: {missing_features}. "
            f"Final limits only contain: {list(final_limits.keys())}"
        )

        # Verify correct values
        for i, feat in enumerate(features):
            expected_value = (i + 1) * 100
            actual_value = final_limits.get(feat)
            assert actual_value == expected_value, (
                f"Feature {feat}: expected {expected_value}, got {actual_value}"
            )

    async def test_concurrent_limit_updates_same_feature(
        self,
        db_engine: AsyncEngine,
    ) -> None:
        """
        Multiple concurrent updates to the SAME feature should not conflict.

        The last write wins, but no data corruption should occur.
        """
        session_factory = async_sessionmaker(
            db_engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

        # Setup
        unique_id = uuid4().hex[:8]
        async with session_factory() as setup_session:
            async with setup_session.begin():
                user_id, user_plan_id = await create_test_infrastructure(
                    setup_session, unique_id
                )

        written_values: list[int] = []
        values_lock = asyncio.Lock()

        async def update_same_limit(limit_value: int) -> int:
            """Update the same feature limit."""
            async with session_factory() as session:
                async with session.begin():
                    stmt = (
                        select(UserPlanModel)
                        .where(UserPlanModel.id == user_plan_id)
                        .with_for_update()
                    )
                    result = await session.execute(stmt)
                    user_plan = result.scalar_one()

                    current_limits = dict(user_plan.custom_limits or {})
                    current_limits["api_calls"] = limit_value
                    user_plan.custom_limits = current_limits

                    await session.flush()

                    async with values_lock:
                        written_values.append(limit_value)

                    return limit_value

        # Fire 20 concurrent updates to the same feature
        values = list(range(100, 2100, 100))  # 100, 200, ..., 2000
        tasks = [update_same_limit(v) for v in values]
        await asyncio.gather(*tasks, return_exceptions=True)

        # Verify final state is one of the valid values
        async with session_factory() as verify_session:
            result = await verify_session.execute(
                select(UserPlanModel).where(UserPlanModel.id == user_plan_id)
            )
            final_plan = result.scalar_one()
            final_limits = final_plan.custom_limits or {}

        assert "api_calls" in final_limits, "api_calls limit should be set"
        assert final_limits["api_calls"] in values, (
            f"Final value {final_limits['api_calls']} is not a valid input value"
        )

    async def test_limit_update_with_initial_limits(
        self,
        db_engine: AsyncEngine,
    ) -> None:
        """
        Updates should correctly merge with pre-existing custom_limits.
        """
        session_factory = async_sessionmaker(
            db_engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

        # Setup with initial custom_limits
        unique_id = uuid4().hex[:8]
        async with session_factory() as setup_session:
            async with setup_session.begin():
                user_id, user_plan_id = await create_test_infrastructure(
                    setup_session, unique_id
                )

                # Set initial custom_limits
                result = await setup_session.execute(
                    select(UserPlanModel).where(UserPlanModel.id == user_plan_id)
                )
                user_plan = result.scalar_one()
                user_plan.custom_limits = {"existing_feature": 1000}
                await setup_session.flush()

        async def update_limit(feature_code: str, limit_value: int) -> bool:
            """Update a specific limit."""
            async with session_factory() as session:
                async with session.begin():
                    stmt = (
                        select(UserPlanModel)
                        .where(UserPlanModel.id == user_plan_id)
                        .with_for_update()
                    )
                    result = await session.execute(stmt)
                    user_plan = result.scalar_one()

                    current_limits = dict(user_plan.custom_limits or {})
                    current_limits[feature_code] = limit_value
                    user_plan.custom_limits = current_limits

                    await session.flush()
                    return True

        # Fire concurrent updates
        tasks = [
            update_limit("new_feature_1", 500),
            update_limit("new_feature_2", 600),
            update_limit("new_feature_3", 700),
        ]
        await asyncio.gather(*tasks)

        # Verify final state contains BOTH existing and new limits
        async with session_factory() as verify_session:
            result = await verify_session.execute(
                select(UserPlanModel).where(UserPlanModel.id == user_plan_id)
            )
            final_plan = result.scalar_one()
            final_limits = final_plan.custom_limits or {}

        # All limits should be present
        assert final_limits.get("existing_feature") == 1000, "Existing limit should be preserved"
        assert final_limits.get("new_feature_1") == 500, "New feature 1 should be present"
        assert final_limits.get("new_feature_2") == 600, "New feature 2 should be present"
        assert final_limits.get("new_feature_3") == 700, "New feature 3 should be present"


class TestConcurrentLimitMergeWithoutLocking:
    """
    Tests that demonstrate the lost update problem WITHOUT FOR UPDATE locking.

    These tests intentionally skip the FOR UPDATE lock to show what would happen
    without proper concurrency control. They document the problem we're solving.
    """

    async def test_without_locking_demonstrates_lost_update_risk(
        self,
        db_engine: AsyncEngine,
    ) -> None:
        """
        WITHOUT locking, concurrent updates MAY lose changes.

        This test demonstrates the race condition that FOR UPDATE prevents.
        Note: This test may occasionally pass due to timing, but under load
        it would fail frequently.
        """
        session_factory = async_sessionmaker(
            db_engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

        # Setup
        unique_id = uuid4().hex[:8]
        async with session_factory() as setup_session:
            async with setup_session.begin():
                user_id, user_plan_id = await create_test_infrastructure(
                    setup_session, unique_id
                )

        # Barrier to synchronize all tasks to start reading at the same time
        barrier = asyncio.Barrier(5)

        async def update_without_lock(feature_code: str, limit_value: int) -> bool:
            """Update WITHOUT FOR UPDATE - demonstrates the race condition."""
            async with session_factory() as session:
                async with session.begin():
                    # Wait for all tasks to be ready
                    await barrier.wait()

                    # Read WITHOUT lock - this is the vulnerable pattern
                    stmt = select(UserPlanModel).where(UserPlanModel.id == user_plan_id)
                    result = await session.execute(stmt)
                    user_plan = result.scalar_one()

                    # All tasks will see the SAME custom_limits here
                    current_limits = dict(user_plan.custom_limits or {})
                    current_limits[feature_code] = limit_value

                    # Each task overwrites with its own version
                    user_plan.custom_limits = current_limits
                    await session.flush()
                    return True

        # Fire 5 concurrent updates without locking
        features = [f"unlocked_feature_{i}" for i in range(5)]
        tasks = [update_without_lock(feat, (i + 1) * 100) for i, feat in enumerate(features)]
        await asyncio.gather(*tasks, return_exceptions=True)

        # Check final state
        async with session_factory() as verify_session:
            result = await verify_session.execute(
                select(UserPlanModel).where(UserPlanModel.id == user_plan_id)
            )
            final_plan = result.scalar_one()
            final_limits = final_plan.custom_limits or {}

        # Document what happened - without locking, we may have lost updates
        present_features = [f for f in features if f in final_limits]

        # Log the result for documentation purposes
        # In a properly locked system, all 5 features would be present
        # Without locking, only the last writer's feature survives
        print(f"Without locking: {len(present_features)}/5 features present")
        print(f"Present: {present_features}")
        print(f"Final limits: {final_limits}")

        # We expect FEWER than all 5 features due to lost updates
        # (though timing could occasionally preserve all - that's okay for this doc test)
        # The important thing is the WITH locking test above ALWAYS preserves all features
