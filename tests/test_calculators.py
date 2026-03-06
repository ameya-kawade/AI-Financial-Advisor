"""
Tests for financial calculator utility functions.
Covers TC-008 (PMT calculation accuracy).
"""

import pytest
from utils.calculators import (
    compute_adjusted_timeline,
    compute_future_value,
    compute_health_score,
    compute_inflation_adjusted,
    compute_pmt,
)


class TestPMT:
    """TC-008: PMT calculation accuracy."""

    def test_pmt_basic(self):
        """FV=500000, N=36 months, Rate=8% annual → PMT ≈ 12334.85."""
        result = compute_pmt(future_value=500000, months=36, annual_rate_pct=8.0)
        assert abs(result - 12334.85) < 10  # ±INR 10 tolerance

    def test_pmt_zero_rate(self):
        """Zero rate should divide evenly."""
        result = compute_pmt(future_value=120000, months=12, annual_rate_pct=0.0)
        assert abs(result - 10000) < 0.01

    def test_pmt_positive(self):
        """PMT must always be positive for positive FV."""
        result = compute_pmt(future_value=1000000, months=60, annual_rate_pct=10.0)
        assert result > 0

    def test_pmt_higher_rate_lower_pmt(self):
        """Higher return rate requires lower monthly contribution for same FV."""
        pmt_low = compute_pmt(500000, 60, 7.0)
        pmt_high = compute_pmt(500000, 60, 12.0)
        assert pmt_low > pmt_high


class TestHealthScore:
    """Health score edge cases and range validation."""

    def test_score_range(self):
        for sr, er, dti, ef, surplus, income in [
            (0, 100, 50, 0, -5000, 30000),
            (20, 50, 15, 6, 5000, 60000),
            (40, 30, 5, 12, 20000, 100000),
        ]:
            score = compute_health_score(sr, er, dti, ef, surplus, income)
            assert 0 <= score <= 100

    def test_perfect_profile_high_score(self):
        score = compute_health_score(
            savings_rate=30, expense_ratio=40, dti=5,
            ef_months=12, net_surplus=20000, income=80000
        )
        assert score >= 80

    def test_critical_profile_low_score(self):
        score = compute_health_score(
            savings_rate=0, expense_ratio=100, dti=45,
            ef_months=0, net_surplus=-5000, income=30000
        )
        assert score < 40


class TestInflationAdjustment:
    """Inflation adjustment calculations."""

    def test_inflation_increases_target(self):
        result = compute_inflation_adjusted(1000000, years=5, inflation_rate=0.06)
        assert result > 1000000

    def test_inflation_zero_rate_unchanged(self):
        result = compute_inflation_adjusted(500000, years=10, inflation_rate=0.0)
        assert abs(result - 500000) < 0.01

    def test_inflation_10_years(self):
        # 1,000,000 at 6% for 10 years ≈ 1,790,847
        result = compute_inflation_adjusted(1000000, years=10, inflation_rate=0.06)
        assert abs(result - 1790847) < 1000


class TestAdjustedTimeline:
    """Adjusted timeline calculation for infeasible goals."""

    def test_positive_surplus_returns_valid_months(self):
        months = compute_adjusted_timeline(10000, 500000, 10.0)
        assert months > 0
        assert months <= 480

    def test_zero_surplus_returns_max(self):
        months = compute_adjusted_timeline(0, 500000, 10.0)
        assert months == 480

    def test_larger_surplus_shorter_timeline(self):
        m1 = compute_adjusted_timeline(10000, 500000, 10.0)
        m2 = compute_adjusted_timeline(20000, 500000, 10.0)
        assert m2 < m1


class TestFutureValue:
    """Future value computation."""

    def test_fv_zero_rate(self):
        result = compute_future_value(1000, 12, 0.0)
        assert abs(result - 12000) < 0.01

    def test_fv_positive(self):
        result = compute_future_value(5000, 36, 10.0)
        assert result > 5000 * 36  # Should exceed simple sum due to compounding
