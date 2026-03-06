"""
Tests for Financial Health Analysis Engine (FHAE).
Covers TC-001 through TC-004, TC-007 from test plan.
"""

import pytest
from models.financial_profile import FinancialProfile, GoalInput, InvestmentHorizon, RiskTolerance
from modules.fhae_module import compute_metrics


def make_test_profile(
    income=60000.0,
    expenses=40000.0,
    debt=10000.0,
    savings=120000.0,
    total_debt=360000.0,
    risk=RiskTolerance.MODERATE,
    horizon=InvestmentHorizon.MEDIUM,
    goals=None,
):
    """Helper to create minimal FinancialProfile for tests."""
    if goals is None:
        goals = [GoalInput(goal_name="Emergency Fund", target_amount=100000, target_months=24)]
    return FinancialProfile(
        name="Test User",
        age=30,
        occupation="Salaried",
        monthly_income=income,
        monthly_expenses=expenses,
        monthly_debt_repayments=debt,
        total_debt_outstanding=total_debt,
        current_savings=savings,
        risk_tolerance=risk,
        investment_horizon=horizon,
        financial_goals=goals,
    )


class TestSavingsRate:
    """TC-001: Savings rate calculation."""

    def test_savings_rate_basic(self):
        profile = make_test_profile(income=60000, expenses=40000, debt=10000)
        metrics = compute_metrics(profile)
        # Net surplus = 60000 - 40000 - 10000 = 10000
        # Savings rate = 10000 / 60000 * 100 ≈ 16.67%
        assert abs(metrics.savings_rate_pct - 16.67) < 0.1

    def test_savings_rate_zero_income(self):
        profile = make_test_profile(income=0, expenses=0, debt=0)
        metrics = compute_metrics(profile)
        assert metrics.savings_rate_pct == 0.0

    def test_savings_rate_high_income(self):
        profile = make_test_profile(income=150000, expenses=50000, debt=10000)
        metrics = compute_metrics(profile)
        # Surplus = 90000; rate = 60%
        assert metrics.savings_rate_pct > 20
        assert metrics.savings_rate_status == "healthy"


class TestDTIRatio:
    """TC-002: Debt-to-income ratio calculation."""

    def test_dti_basic(self):
        profile = make_test_profile(income=60000, debt=10000)
        metrics = compute_metrics(profile)
        # DTI = 10000 / 60000 * 100 ≈ 16.67%
        assert abs(metrics.dti_ratio_pct - 16.67) < 0.1

    def test_dti_status_low(self):
        profile = make_test_profile(income=100000, debt=10000)
        metrics = compute_metrics(profile)
        assert metrics.dti_status == "low"

    def test_dti_status_manageable(self):
        profile = make_test_profile(income=60000, debt=10000)
        metrics = compute_metrics(profile)
        assert metrics.dti_status == "manageable"

    def test_dti_status_high(self):
        profile = make_test_profile(income=30000, debt=12000)  # 40%
        metrics = compute_metrics(profile)
        assert metrics.dti_status == "high"


class TestEmergencyFund:
    """TC-003: Emergency fund coverage calculation."""

    def test_ef_coverage_basic(self):
        profile = make_test_profile(savings=120000, expenses=40000)
        metrics = compute_metrics(profile)
        # EF = 120000 / 40000 = 3.0 months
        assert abs(metrics.emergency_fund_months - 3.0) < 0.01
        assert metrics.ef_status == "adequate"

    def test_ef_status_insufficient(self):
        profile = make_test_profile(savings=40000, expenses=40000)
        metrics = compute_metrics(profile)
        assert metrics.ef_status == "insufficient"

    def test_ef_status_strong(self):
        profile = make_test_profile(savings=300000, expenses=40000)
        metrics = compute_metrics(profile)
        assert metrics.ef_status == "strong"


class TestHealthScore:
    """TC-004: Health score for critical conditions, and score in range."""

    def test_low_savings_high_debt_score(self):
        # Zero surplus (expenses = income), high DTI
        profile = make_test_profile(income=30000, expenses=30000, debt=12000)
        metrics = compute_metrics(profile)
        assert metrics.financial_health_score < 40
        assert metrics.overall_status == "critical"

    def test_health_score_in_range(self):
        for income in [20000, 60000, 150000]:
            profile = make_test_profile(
                income=income,
                expenses=income * 0.5,
                debt=income * 0.1,
            )
            metrics = compute_metrics(profile)
            assert 0 <= metrics.financial_health_score <= 100

    def test_excellent_score(self):
        profile = make_test_profile(income=100000, expenses=30000, debt=5000, savings=600000)
        metrics = compute_metrics(profile)
        assert metrics.financial_health_score >= 60


class TestNegativeSurplus:
    """TC-007: Negative surplus detection and critical alert."""

    def test_negative_surplus(self):
        profile = make_test_profile(income=30000, expenses=35000, debt=0)
        metrics = compute_metrics(profile)
        assert metrics.net_monthly_surplus < 0

    def test_negative_surplus_critical_status(self):
        profile = make_test_profile(income=30000, expenses=35000, debt=0)
        metrics = compute_metrics(profile)
        assert metrics.overall_status == "critical"

    def test_negative_surplus_investable_zero(self):
        profile = make_test_profile(income=30000, expenses=35000, debt=0)
        metrics = compute_metrics(profile)
        assert metrics.investable_surplus == 0.0


class TestNetSurplus:
    """Additional tests for net surplus computation."""

    def test_net_surplus_positive(self):
        profile = make_test_profile(income=90000, expenses=45000, debt=12000)
        metrics = compute_metrics(profile)
        assert abs(metrics.net_monthly_surplus - 33000) < 0.01

    def test_net_surplus_zero_debt(self):
        profile = make_test_profile(income=50000, expenses=30000, debt=0)
        metrics = compute_metrics(profile)
        assert metrics.net_monthly_surplus == 20000.0
