"""Goal-Based Investment Planning Engine (GBIPE) module."""

from __future__ import annotations

import streamlit as st

from config.allocation_matrix import get_allocation
from config.settings import EXPECTED_RETURN_RATES, INFLATION_RATE
from models.financial_metrics import FinancialMetrics
from models.financial_profile import FinancialProfile
from models.goal_plan import GoalPlan
from utils.calculators import (
    compute_adjusted_timeline,
    compute_inflation_adjusted,
    compute_pmt,
)
from utils.formatters import format_inr, format_months, format_pct


def analyse_goals(profile: FinancialProfile, metrics: FinancialMetrics) -> list[GoalPlan]:
    """
    Analyse each financial goal for feasibility and generate investment plans.

    Args:
        profile: Validated FinancialProfile.
        metrics: Computed FinancialMetrics.

    Returns:
        List[GoalPlan] sorted by priority_score descending.
    """
    horizon_str = profile.investment_horizon.value
    risk_str = profile.risk_tolerance.value
    expected_rate = EXPECTED_RETURN_RATES.get(risk_str, 10.0)
    allocation = get_allocation(horizon_str, risk_str)
    investable = metrics.investable_surplus

    goal_plans: list[GoalPlan] = []

    for goal_input in profile.financial_goals:
        months = goal_input.target_months
        years = months / 12

        # Inflation-adjusted target
        inflation_target = compute_inflation_adjusted(
            goal_input.target_amount, years, INFLATION_RATE
        )

        # Required monthly saving (PMT)
        required_monthly = compute_pmt(inflation_target, months, expected_rate)

        # Feasibility score
        feasibility_score = (investable / required_monthly * 100) if required_monthly > 0 else 0.0

        if feasibility_score < 80:
            feasibility_status = "infeasible"
            adjusted_timeline = compute_adjusted_timeline(
                investable, inflation_target, expected_rate
            )
        elif feasibility_score < 100:
            feasibility_status = "tight"
            adjusted_timeline = None
        else:
            feasibility_status = "feasible"
            adjusted_timeline = None

        # Priority score: urgency-weighted (shorter timeline = higher urgency)
        priority_score = 1000 / max(months, 1)

        goal_plans.append(
            GoalPlan(
                goal_name=goal_input.goal_name,
                target_amount=goal_input.target_amount,
                target_months=months,
                inflation_adjusted_target=round(inflation_target, 2),
                required_monthly_saving=round(required_monthly, 2),
                feasibility_score=round(feasibility_score, 2),
                feasibility_status=feasibility_status,
                adjusted_timeline_months=adjusted_timeline,
                allocation_breakdown=allocation,
                priority_score=round(priority_score, 4),
                expected_return_rate=expected_rate,
            )
        )

    # Sort by priority (most urgent first)
    goal_plans.sort(key=lambda g: g.priority_score, reverse=True)
    return goal_plans


def render_goal_cards(goals: list[GoalPlan], metrics: FinancialMetrics) -> None:
    """
    Render goal investment plan cards with progress bars and allocation tables.

    Args:
        goals: List of computed GoalPlan instances.
        metrics: FinancialMetrics for context.
    """
    # Page header
    st.markdown(
        """
        <div class="page-header">
            <div class="page-header-icon">🎯</div>
            <div>
                <div class="page-header-title">Goal-Based Investment Plans</div>
                <div class="page-header-sub">Personalised roadmaps for each of your financial goals.</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if not goals:
        st.info("No goals defined. Go back to your Financial Profile and add at least one goal.")
        return

    # Negative surplus: disable investment advice
    if metrics.net_monthly_surplus < 0:
        surplus_needed = abs(metrics.net_monthly_surplus)
        st.error(
            f"⛔ Goal planning is currently disabled. Your expenses exceed your income by "
            f"**{format_inr(surplus_needed)}/month**. Reduce expenses or increase income first."
        )
        return

    investable = metrics.investable_surplus
    total_required = sum(g.required_monthly_saving for g in goals)

    # Allocation summary progress bar
    if investable > 0:
        alloc_pct = min(total_required / investable * 100, 100)
        st.progress(
            alloc_pct / 100,
            text=f"**{format_inr(total_required)}/mo** required across all goals "
                 f"({format_pct(alloc_pct)} of your investable surplus of {format_inr(investable)})",
        )

    st.markdown("<div style='margin-top:8px;'></div>", unsafe_allow_html=True)

    for i, goal in enumerate(goals, start=1):
        _render_single_goal_card(goal, investable, i)


def _render_single_goal_card(goal: GoalPlan, investable_surplus: float, index: int) -> None:
    """Render a single goal card with metrics, allocation, and milestones."""
    status_configs = {
        "feasible":   {"icon": "✅", "color": "#10B981", "badge": "Feasible"},
        "tight":      {"icon": "⚠️", "color": "#F59E0B", "badge": "Tight — Stretch Goal"},
        "infeasible": {"icon": "🔴", "color": "#EF4444", "badge": "Infeasible (at current savings)"},
    }
    cfg = status_configs.get(goal.feasibility_status, status_configs["feasible"])

    with st.container():
        st.markdown(
            f"""
            <div class="goal-card" style="border-left: 5px solid {cfg['color']};">
                <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px;">
                    <h3 style="color:#0F172A;margin:0;font-size:1.1rem;font-weight:700;">
                        #{index} {goal.goal_name}
                    </h3>
                    <span style="
                        background:{cfg['color']}18;color:{cfg['color']};
                        padding:4px 14px;border-radius:20px;font-size:12px;font-weight:600;
                        border:1px solid {cfg['color']}40;
                    ">{cfg['icon']} {cfg['badge']}</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric("Target Amount", format_inr(goal.target_amount, compact=True))
            st.caption(f"Inflation-adjusted: {format_inr(goal.inflation_adjusted_target, compact=True)}")
        with c2:
            st.metric("Timeline", format_months(goal.target_months))
            st.caption(f"Expected return: {goal.expected_return_rate}% p.a.")
        with c3:
            st.metric(
                "Required Monthly Investment",
                format_inr(goal.required_monthly_saving, compact=True),
                delta=format_inr(investable_surplus - goal.required_monthly_saving, compact=True)
                if investable_surplus > 0 else None,
                delta_color="normal",
            )

        # Feasibility bar
        feasibility_display = min(goal.feasibility_score, 100)
        st.progress(
            feasibility_display / 100,
            text=(
                f"Feasibility: **{goal.feasibility_score:.0f}%** of required monthly "
                f"({format_inr(investable_surplus)} available / {format_inr(goal.required_monthly_saving)} needed)"
            ),
        )

        if goal.feasibility_status == "infeasible" and goal.adjusted_timeline_months:
            st.info(
                f"📅 **Adjusted Timeline**: With your current investable surplus of "
                f"{format_inr(investable_surplus)}/month, you can reach this goal in "
                f"**{format_months(goal.adjusted_timeline_months)}** instead."
            )

        # Asset allocation table
        with st.expander("📊 View Asset Allocation", expanded=(index == 1)):
            import pandas as pd

            alloc_data = [
                {
                    "Asset Class": asset,
                    "Allocation %": f"{pct}%",
                    "Monthly Amount (INR)": format_inr(
                        goal.required_monthly_saving * pct / 100, compact=True
                    ),
                }
                for asset, pct in goal.allocation_breakdown.items()
            ]
            df = pd.DataFrame(alloc_data)
            st.dataframe(df, use_container_width=True, hide_index=True)

        st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)
