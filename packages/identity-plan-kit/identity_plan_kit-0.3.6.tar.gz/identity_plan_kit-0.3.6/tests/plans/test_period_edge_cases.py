"""Tests for plan period edge cases.

Tests cover:
- Leap year handling
- Month boundary transitions
- Timezone considerations
- End of month calculations
- Year boundary transitions

CRITICAL: These tests ensure usage period calculations
are correct across all date edge cases.
"""

from calendar import monthrange
from datetime import date, timedelta
from unittest.mock import patch

import pytest

from identity_plan_kit.plans.domain.entities import PeriodType
from identity_plan_kit.plans.repositories.usage_repo import (
    DEFAULT_LIFETIME_END_YEAR,
    DEFAULT_LIFETIME_START_YEAR,
    UsageRepository,
)


class MockSession:
    """Mock session for testing period calculation."""

    pass


class TestDailyPeriodCalculation:
    """Test daily period boundary calculations."""

    def test_daily_period_is_single_day(self):
        """Daily period starts and ends on same day."""
        repo = UsageRepository(MockSession())

        with patch("identity_plan_kit.plans.repositories.usage_repo.date") as mock_date:
            mock_date.today.return_value = date(2024, 6, 15)

            start, end = repo._get_period_range(PeriodType.DAILY)

            assert start == date(2024, 6, 15)
            assert end == date(2024, 6, 15)

    def test_daily_period_on_leap_day(self):
        """Daily period works on Feb 29."""
        repo = UsageRepository(MockSession())

        with patch("identity_plan_kit.plans.repositories.usage_repo.date") as mock_date:
            mock_date.today.return_value = date(2024, 2, 29)

            start, end = repo._get_period_range(PeriodType.DAILY)

            assert start == date(2024, 2, 29)
            assert end == date(2024, 2, 29)

    def test_daily_period_on_december_31(self):
        """Daily period works on Dec 31."""
        repo = UsageRepository(MockSession())

        with patch("identity_plan_kit.plans.repositories.usage_repo.date") as mock_date:
            mock_date.today.return_value = date(2024, 12, 31)

            start, end = repo._get_period_range(PeriodType.DAILY)

            assert start == date(2024, 12, 31)
            assert end == date(2024, 12, 31)

    def test_daily_period_on_january_1(self):
        """Daily period works on Jan 1."""
        repo = UsageRepository(MockSession())

        with patch("identity_plan_kit.plans.repositories.usage_repo.date") as mock_date:
            mock_date.today.return_value = date(2025, 1, 1)

            start, end = repo._get_period_range(PeriodType.DAILY)

            assert start == date(2025, 1, 1)
            assert end == date(2025, 1, 1)


class TestMonthlyPeriodCalculation:
    """Test monthly period boundary calculations."""

    def test_monthly_period_full_month(self):
        """Monthly period covers full month."""
        repo = UsageRepository(MockSession())

        with patch("identity_plan_kit.plans.repositories.usage_repo.date") as mock_date:
            mock_date.today.return_value = date(2024, 6, 15)

            start, end = repo._get_period_range(PeriodType.MONTHLY)

            assert start == date(2024, 6, 1)
            assert end == date(2024, 6, 30)

    def test_monthly_period_31_day_month(self):
        """Monthly period in 31-day month."""
        repo = UsageRepository(MockSession())

        with patch("identity_plan_kit.plans.repositories.usage_repo.date") as mock_date:
            mock_date.today.return_value = date(2024, 7, 15)  # July

            start, end = repo._get_period_range(PeriodType.MONTHLY)

            assert start == date(2024, 7, 1)
            assert end == date(2024, 7, 31)

    def test_monthly_period_30_day_month(self):
        """Monthly period in 30-day month."""
        repo = UsageRepository(MockSession())

        with patch("identity_plan_kit.plans.repositories.usage_repo.date") as mock_date:
            mock_date.today.return_value = date(2024, 4, 15)  # April

            start, end = repo._get_period_range(PeriodType.MONTHLY)

            assert start == date(2024, 4, 1)
            assert end == date(2024, 4, 30)

    def test_monthly_period_february_non_leap(self):
        """Monthly period in February (non-leap year)."""
        repo = UsageRepository(MockSession())

        with patch("identity_plan_kit.plans.repositories.usage_repo.date") as mock_date:
            mock_date.today.return_value = date(2023, 2, 15)  # 2023 is not a leap year

            start, end = repo._get_period_range(PeriodType.MONTHLY)

            assert start == date(2023, 2, 1)
            assert end == date(2023, 2, 28)

    def test_monthly_period_february_leap_year(self):
        """Monthly period in February (leap year)."""
        repo = UsageRepository(MockSession())

        with patch("identity_plan_kit.plans.repositories.usage_repo.date") as mock_date:
            mock_date.today.return_value = date(2024, 2, 15)  # 2024 is a leap year

            start, end = repo._get_period_range(PeriodType.MONTHLY)

            assert start == date(2024, 2, 1)
            assert end == date(2024, 2, 29)

    def test_monthly_period_on_first_day(self):
        """Monthly period when today is first of month."""
        repo = UsageRepository(MockSession())

        with patch("identity_plan_kit.plans.repositories.usage_repo.date") as mock_date:
            mock_date.today.return_value = date(2024, 3, 1)

            start, end = repo._get_period_range(PeriodType.MONTHLY)

            assert start == date(2024, 3, 1)
            assert end == date(2024, 3, 31)

    def test_monthly_period_on_last_day(self):
        """Monthly period when today is last of month."""
        repo = UsageRepository(MockSession())

        with patch("identity_plan_kit.plans.repositories.usage_repo.date") as mock_date:
            mock_date.today.return_value = date(2024, 3, 31)

            start, end = repo._get_period_range(PeriodType.MONTHLY)

            assert start == date(2024, 3, 1)
            assert end == date(2024, 3, 31)


class TestLeapYearHandling:
    """Test leap year edge cases."""

    @pytest.mark.parametrize("year,is_leap", [
        (2020, True),   # Divisible by 4
        (2024, True),   # Divisible by 4
        (2000, True),   # Divisible by 400
        (2100, False),  # Divisible by 100 but not 400
        (2023, False),  # Not divisible by 4
        (1900, False),  # Divisible by 100 but not 400
    ])
    def test_leap_year_detection(self, year, is_leap):
        """Verify leap year is detected correctly."""
        # Using calendar.monthrange to check February days
        _, feb_days = monthrange(year, 2)

        if is_leap:
            assert feb_days == 29
        else:
            assert feb_days == 28

    def test_february_29_monthly_period(self):
        """Monthly period includes Feb 29 in leap year."""
        repo = UsageRepository(MockSession())

        with patch("identity_plan_kit.plans.repositories.usage_repo.date") as mock_date:
            mock_date.today.return_value = date(2024, 2, 29)

            start, end = repo._get_period_range(PeriodType.MONTHLY)

            assert start == date(2024, 2, 1)
            assert end == date(2024, 2, 29)

    def test_year_2100_not_leap(self):
        """Year 2100 is correctly identified as non-leap."""
        repo = UsageRepository(MockSession())

        with patch("identity_plan_kit.plans.repositories.usage_repo.date") as mock_date:
            mock_date.today.return_value = date(2100, 2, 15)

            start, end = repo._get_period_range(PeriodType.MONTHLY)

            # Feb 2100 has 28 days (not a leap year)
            assert end == date(2100, 2, 28)


class TestLifetimePeriodCalculation:
    """Test lifetime period calculations."""

    def test_lifetime_period_constants(self):
        """Lifetime period uses correct constant bounds."""
        assert DEFAULT_LIFETIME_START_YEAR == 2000
        assert DEFAULT_LIFETIME_END_YEAR == 2100

    def test_lifetime_period_is_static(self):
        """Lifetime period doesn't change with current date."""
        repo = UsageRepository(MockSession())

        # Lifetime period should always return the same static dates
        # regardless of current date (no mocking needed)
        start, end = repo._get_period_range(None)  # None = lifetime

        assert start == date(2000, 1, 1)
        assert end == date(2100, 12, 31)

    def test_lifetime_period_with_period_type_none(self):
        """Period type None returns lifetime period."""
        repo = UsageRepository(MockSession())

        start, end = repo._get_period_range(None)

        assert start == date(DEFAULT_LIFETIME_START_YEAR, 1, 1)
        assert end == date(DEFAULT_LIFETIME_END_YEAR, 12, 31)


class TestYearBoundaryTransitions:
    """Test year boundary transitions."""

    def test_monthly_december_to_january(self):
        """Monthly period transitions correctly at year boundary."""
        repo = UsageRepository(MockSession())

        # December
        with patch("identity_plan_kit.plans.repositories.usage_repo.date") as mock_date:
            mock_date.today.return_value = date(2024, 12, 31)
            dec_start, dec_end = repo._get_period_range(PeriodType.MONTHLY)

        # January (next year)
        with patch("identity_plan_kit.plans.repositories.usage_repo.date") as mock_date:
            mock_date.today.return_value = date(2025, 1, 1)
            jan_start, jan_end = repo._get_period_range(PeriodType.MONTHLY)

        # December should be complete month in 2024
        assert dec_start == date(2024, 12, 1)
        assert dec_end == date(2024, 12, 31)

        # January should be complete month in 2025
        assert jan_start == date(2025, 1, 1)
        assert jan_end == date(2025, 1, 31)

        # Periods should not overlap
        assert dec_end < jan_start

    def test_daily_december_31_to_january_1(self):
        """Daily period transitions correctly at year boundary."""
        repo = UsageRepository(MockSession())

        with patch("identity_plan_kit.plans.repositories.usage_repo.date") as mock_date:
            mock_date.today.return_value = date(2024, 12, 31)
            dec_start, dec_end = repo._get_period_range(PeriodType.DAILY)

        with patch("identity_plan_kit.plans.repositories.usage_repo.date") as mock_date:
            mock_date.today.return_value = date(2025, 1, 1)
            jan_start, jan_end = repo._get_period_range(PeriodType.DAILY)

        assert dec_start == dec_end == date(2024, 12, 31)
        assert jan_start == jan_end == date(2025, 1, 1)


class TestMonthBoundaryTransitions:
    """Test month boundary transitions."""

    @pytest.mark.parametrize("month,next_month_days", [
        (1, 28),   # Jan -> Feb (non-leap)
        (2, 31),   # Feb -> Mar
        (3, 30),   # Mar -> Apr
        (4, 31),   # Apr -> May
        (5, 30),   # May -> Jun
        (6, 31),   # Jun -> Jul
        (7, 31),   # Jul -> Aug
        (8, 30),   # Aug -> Sep
        (9, 31),   # Sep -> Oct
        (10, 30),  # Oct -> Nov
        (11, 31),  # Nov -> Dec
        (12, 31),  # Dec -> Jan
    ])
    def test_month_transitions(self, month, next_month_days):
        """Each month transitions correctly to the next."""
        repo = UsageRepository(MockSession())

        # Non-leap year for consistent Feb days
        year = 2023
        if month == 1:  # Jan->Feb
            next_month_days = 28  # 2023 is not a leap year

        # Get period for last day of current month
        _, last_day = monthrange(year, month)

        with patch("identity_plan_kit.plans.repositories.usage_repo.date") as mock_date:
            mock_date.today.return_value = date(year, month, last_day)
            current_start, current_end = repo._get_period_range(PeriodType.MONTHLY)

        # Get period for first day of next month
        if month == 12:
            next_year, next_month = year + 1, 1
        else:
            next_year, next_month = year, month + 1

        with patch("identity_plan_kit.plans.repositories.usage_repo.date") as mock_date:
            mock_date.today.return_value = date(next_year, next_month, 1)
            next_start, next_end = repo._get_period_range(PeriodType.MONTHLY)

        # Verify no gap between months
        assert current_end + timedelta(days=1) == next_start


class TestPeriodTypeHandling:
    """Test PeriodType enum handling."""

    def test_daily_period_type(self):
        """PeriodType.DAILY is handled correctly."""
        repo = UsageRepository(MockSession())

        with patch("identity_plan_kit.plans.repositories.usage_repo.date") as mock_date:
            mock_date.today.return_value = date(2024, 6, 15)

            start, end = repo._get_period_range(PeriodType.DAILY)

            assert start == end  # Same day

    def test_monthly_period_type(self):
        """PeriodType.MONTHLY is handled correctly."""
        repo = UsageRepository(MockSession())

        with patch("identity_plan_kit.plans.repositories.usage_repo.date") as mock_date:
            mock_date.today.return_value = date(2024, 6, 15)

            start, end = repo._get_period_range(PeriodType.MONTHLY)

            assert start == date(2024, 6, 1)
            assert end == date(2024, 6, 30)

    def test_none_period_type(self):
        """None period type is handled as lifetime."""
        repo = UsageRepository(MockSession())

        start, end = repo._get_period_range(None)

        assert start.year == DEFAULT_LIFETIME_START_YEAR
        assert end.year == DEFAULT_LIFETIME_END_YEAR


class TestEdgeCaseDates:
    """Test edge case dates."""

    def test_century_boundary(self):
        """Period calculation works at century boundary."""
        repo = UsageRepository(MockSession())

        # Dec 31, 2099
        with patch("identity_plan_kit.plans.repositories.usage_repo.date") as mock_date:
            mock_date.today.return_value = date(2099, 12, 31)

            start, end = repo._get_period_range(PeriodType.MONTHLY)

            assert start == date(2099, 12, 1)
            assert end == date(2099, 12, 31)

    def test_minimum_valid_date(self):
        """Period calculation works with early dates."""
        repo = UsageRepository(MockSession())

        with patch("identity_plan_kit.plans.repositories.usage_repo.date") as mock_date:
            mock_date.today.return_value = date(2000, 1, 1)

            start, end = repo._get_period_range(PeriodType.MONTHLY)

            assert start == date(2000, 1, 1)
            assert end == date(2000, 1, 31)

    def test_february_28_non_leap(self):
        """Feb 28 in non-leap year is last day."""
        repo = UsageRepository(MockSession())

        with patch("identity_plan_kit.plans.repositories.usage_repo.date") as mock_date:
            mock_date.today.return_value = date(2023, 2, 28)

            start, end = repo._get_period_range(PeriodType.MONTHLY)

            assert end == date(2023, 2, 28)


class TestPeriodDurationConsistency:
    """Test period duration consistency."""

    def test_daily_period_always_one_day(self):
        """Daily period is always exactly one day."""
        repo = UsageRepository(MockSession())

        for month in range(1, 13):
            with patch(
                "identity_plan_kit.plans.repositories.usage_repo.date"
            ) as mock_date:
                mock_date.today.return_value = date(2024, month, 15)

                start, end = repo._get_period_range(PeriodType.DAILY)

                duration = (end - start).days + 1
                assert duration == 1

    def test_monthly_period_matches_month_length(self):
        """Monthly period matches actual month length."""
        repo = UsageRepository(MockSession())

        for month in range(1, 13):
            with patch(
                "identity_plan_kit.plans.repositories.usage_repo.date"
            ) as mock_date:
                mock_date.today.return_value = date(2024, month, 15)

                start, end = repo._get_period_range(PeriodType.MONTHLY)

                duration = (end - start).days + 1
                expected_days, _ = monthrange(2024, month)
                # monthrange returns (weekday, days_in_month)
                _, expected_days = monthrange(2024, month)
                assert duration == expected_days

    def test_lifetime_period_consistent(self):
        """Lifetime period is always the same duration."""
        repo = UsageRepository(MockSession())

        # Calculate expected duration
        lifetime_start = date(DEFAULT_LIFETIME_START_YEAR, 1, 1)
        lifetime_end = date(DEFAULT_LIFETIME_END_YEAR, 12, 31)
        expected_duration = (lifetime_end - lifetime_start).days + 1

        # Lifetime period doesn't depend on current date
        start, end = repo._get_period_range(None)

        duration = (end - start).days + 1
        assert duration == expected_duration
