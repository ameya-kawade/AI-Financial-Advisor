"""
Tests for Goal-Based Investment Planning Engine (GBIPE).
Covers TC-005, TC-006 from test plan.
"""

import pytest
from models.financial_metrics import FinancialMetrics
from models.financial_profile import FinancialProfile, GoalInput, InvestmentHorizon, RiskTolerance
from modules.gbipe_module import analyse_goals


def make_profile(income=60000.0, expenses=30000.0, debt=5000.0, savings=60000.0,
                 risk=RiskTolerance.MODERATE, horizon=InvestmentHorizon.MEDIUM, goals=None):
    if goals is None:
        goals = [GoalInput(goal_name="Test Goal", target_amount=500000, target_months=36)]
    return FinancialProfile(
        name="Test User", age=30, occupation="Salaried",
        monthly_income=income, monthly_expenses=expenses,
        monthly_debt_repayments=debt, total_debt_outstanding=debt * 20,
        current_savings=savings, risk_tolerance=risk,
        investment_horizon=horizon, financial_goals=goals,
    )


def make_metrics(net_surplus=15000.0, investable=13500.0, score=65):
    return FinancialMetrics(
        net_monthly_surplus=net_surplus,
        savings_rate_pct=25.0,
        expense_ratio_pct=50.0,
        dti_ratio_pct=8.33,
        emergency_fund_months=2.0,
        financial_health_score=score,
        investable_surplus=investable,
        debt_payoff_months=None,
        savings_rate_status="healthy",
        dti_status="low",
        ef_status="insufficient",
        expense_ratio_status="excellent",
        overall_status="good",
    )


class TestGoalFeasibility:
    """TC-005: Feasible goal (surplus > required monthly)."""

    def test_feasible_goal(self):
        """Surplus of 15000 should easily cover 12000 requirement."""
        goals = [GoalInput(goal_name="Emergency Fund", target_amount=200000, target_months=36)]
        profile = make_profile(goals=goals)
        metrics = make_metrics(investable=15000.0)
        result = analyse_goals(profile, metrics)
        assert len(result) == 1
        assert result[0].feasibility_score > 80
        assert result[0].feasibility_status in ("feasible", "tight")

    def test_feasible_score_over_100(self):
        """Very large surplus should give score > 100."""
        goals = [GoalInput(goal_name="Emergency Fund", target_amount=50000, target_months=24)]
        profile = make_profile(goals=goals)
        metrics = make_metrics(investable=50000.0)
        result = analyse_goals(profile, metrics)
        assert result[0].feasibility_score > 100


class TestGoalInfeasibility:
    """TC-006: Infeasible goal with adjusted timeline."""

    def test_infeasible_goal_returns_adjusted_timeline(self):
        """Small surplus vs large requirement should be infeasible with adjusted timeline."""
        goals = [GoalInput(goal_name="Home", target_amount=3000000, target_months=24)]
        profile = make_profile(goals=goals)
        metrics = make_metrics(investable=8000.0)
        result = analyse_goals(profile, metrics)
        assert result[0].feasibility_status == "infeasible"
        assert result[0].adjusted_timeline_months is not None
        assert result[0].adjusted_timeline_months > 24

    def test_infeasible_goal_feasibility_below_80(self):
        goals = [GoalInput(goal_name="Home", target_amount=5000000, target_months=36)]
        profile = make_profile(goals=goals)
        metrics = make_metrics(investable=5000.0)
        result = analyse_goals(profile, metrics)
        assert result[0].feasibility_score < 80


class TestGoalPriority:
    """Goals should be sorted by priority (shorter timeline first)."""

    def test_priority_sorting(self):
        goals = [
            GoalInput(goal_name="Retirement", target_amount=10000000, target_months=300),
            GoalInput(goal_name="Emergency Fund", target_amount=100000, target_months=12),
            GoalInput(goal_name="Travel", target_amount=200000, target_months=24),
        ]
        profile = make_profile(goals=goals)
        metrics = make_metrics(investable=20000.0)
        result = analyse_goals(profile, metrics)
        # Emergency Fund (12 months) should be first
        assert result[0].goal_name == "Emergency Fund"
        assert result[-1].goal_name == "Retirement"


class TestInflationAdjustment:
    """Inflation-adjusted target should be > nominal target."""

    def test_inflation_adjusted_greater_than_nominal(self):
        goals = [GoalInput(goal_name="Home", target_amount=1000000, target_months=120)]
        profile = make_profile(goals=goals)
        metrics = make_metrics(investable=20000.0)
        result = analyse_goals(profile, metrics)
        assert result[0].inflation_adjusted_target > result[0].target_amount
