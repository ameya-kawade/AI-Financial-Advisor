"""
Module 2: Financial Health Analysis Engine (FHAE)
Computes 8 financial health metrics and renders metric dashboard with traffic-light scoring.
"""

from __future__ import annotations

import streamlit as st

from config.settings import (
    EMERGENCY_BUFFER_RATE,
    SCORE_CRITICAL_THRESHOLD,
    SCORE_GOOD_THRESHOLD,
    SCORE_NEEDS_WORK_THRESHOLD,
)
from models.financial_metrics import FinancialMetrics
from models.financial_profile import FinancialProfile
from utils.calculators import compute_health_score
from utils.formatters import format_inr, format_months, format_pct, format_score_label, score_to_color


def compute_metrics(profile: FinancialProfile) -> FinancialMetrics:
    """
    Compute all 8 financial health metrics from validated profile.

    Args:
        profile: Validated FinancialProfile instance.

    Returns:
        FinancialMetrics with all computed values and status labels.
    """
    income = profile.monthly_income
    expenses = profile.monthly_expenses
    debt_monthly = profile.monthly_debt_repayments
    total_debt = profile.total_debt_outstanding
    savings = profile.current_savings

    # M01: Net Monthly Surplus
    net_surplus = income - expenses - debt_monthly

    # M02: Savings Rate — based on how much is left after expenses & debt
    savings_contribution = max(net_surplus, 0)  # Can't save if negative surplus
    savings_rate = (savings_contribution / income * 100) if income > 0 else 0.0

    # M03: Expense Ratio
    expense_ratio = (expenses / income * 100) if income > 0 else 0.0

    # M04: Debt-to-Income Ratio
    dti_ratio = (debt_monthly / income * 100) if income > 0 else 0.0

    # M05: Emergency Fund Coverage (months)
    ef_months = (savings / expenses) if expenses > 0 else float("inf")
    ef_months = min(ef_months, 99.9)  # Cap for display

    # M06: Financial Health Score (composite)
    health_score = compute_health_score(
        savings_rate=savings_rate,
        expense_ratio=expense_ratio,
        dti=dti_ratio,
        ef_months=ef_months,
        net_surplus=net_surplus,
        income=income,
    )

    # M07: Investable Surplus
    investable_surplus = max(net_surplus * (1 - EMERGENCY_BUFFER_RATE), 0.0)

    # M08: Debt Payoff Timeline
    if debt_monthly > 0 and total_debt > 0:
        debt_payoff_months = int(round(total_debt / debt_monthly))
    else:
        debt_payoff_months = None

    # Status labels
    savings_rate_status = _classify(
        savings_rate, [(10, "poor"), (20, "moderate")], "healthy"
    )
    dti_status = _classify(dti_ratio, [(15, "low"), (36, "manageable")], "high")
    ef_status = _classify(ef_months, [(3, "insufficient"), (6, "adequate")], "strong")
    expense_ratio_status = _classify(
        expense_ratio, [(50, "excellent"), (70, "good")], "high"
    )
    overall_status = _score_to_status(health_score)

    return FinancialMetrics(
        net_monthly_surplus=net_surplus,
        savings_rate_pct=round(savings_rate, 2),
        expense_ratio_pct=round(expense_ratio, 2),
        dti_ratio_pct=round(dti_ratio, 2),
        emergency_fund_months=round(ef_months, 2),
        financial_health_score=health_score,
        investable_surplus=round(investable_surplus, 2),
        debt_payoff_months=debt_payoff_months,
        savings_rate_status=savings_rate_status,
        dti_status=dti_status,
        ef_status=ef_status,
        expense_ratio_status=expense_ratio_status,
        overall_status=overall_status,
    )


def render_metrics_dashboard(metrics: FinancialMetrics, profile: FinancialProfile) -> None:
    """
    Render the financial health analysis dashboard with metric cards and alerts.

    Args:
        metrics: Computed FinancialMetrics instance.
        profile: The user's FinancialProfile (for context).
    """
    _render_health_score_hero(metrics)
    _render_critical_alerts(metrics)
    _render_metric_cards(metrics)
    _render_metrics_table(metrics, profile)


# ── Internal Helpers ──────────────────────────────────────────────────────────

def _classify(value: float, thresholds: list[tuple], final_label: str) -> str:
    """Map a numeric value to a label using ascending thresholds."""
    for threshold, label in thresholds:
        if value < threshold:
            return label
    return final_label


def _score_to_status(score: int) -> str:
    if score < SCORE_CRITICAL_THRESHOLD:
        return "critical"
    elif score < SCORE_NEEDS_WORK_THRESHOLD:
        return "needs_work"
    elif score < SCORE_GOOD_THRESHOLD:
        return "good"
    return "excellent"


def _render_health_score_hero(metrics: FinancialMetrics) -> None:
    """Render prominent health score badge with label."""
    score = metrics.financial_health_score
    color = score_to_color(score)
    label = format_score_label(score)

    st.markdown(
        f"""
        <div style="text-align:center;padding:24px 0 16px;">
            <div style="
                display:inline-flex;align-items:center;justify-content:center;
                width:120px;height:120px;border-radius:50%;
                background:linear-gradient(135deg, {color}22, {color}44);
                border: 4px solid {color};
                font-size:48px;font-weight:800;color:{color};
                margin-bottom:12px;
            ">{score}</div>
            <div style="font-size:22px;font-weight:700;color:{color};">{label}</div>
            <div style="font-size:14px;color:#595959;">Financial Health Score / 100</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_critical_alerts(metrics: FinancialMetrics) -> None:
    """Render alert banners for critical financial conditions."""
    if metrics.net_monthly_surplus < 0:
        st.error(
            "🔴 **Critical: Negative Surplus** — Your monthly outgoings exceed your income. "
            "Investment planning is not recommended until a positive surplus is achieved. "
            f"Current shortfall: **{format_inr(abs(metrics.net_monthly_surplus))}** per month."
        )
    if metrics.dti_ratio_pct > 36:
        st.error(
            f"🔴 **High Debt-to-Income Ratio** ({format_pct(metrics.dti_ratio_pct)}) — "
            "Your debt obligations exceed 36% of income, significantly limiting financial flexibility."
        )
    if metrics.savings_rate_pct < 5 and metrics.net_monthly_surplus >= 0:
        st.warning(
            "⚠️ **Low Savings Rate** — You are saving less than 5% of your income. "
            "Aim for at least 20% to achieve long-term financial security."
        )
    if metrics.ef_status == "insufficient":
        st.warning(
            f"⚠️ **Emergency Fund Insufficient** — You have {metrics.emergency_fund_months:.1f} months "
            "of coverage. Aim for a minimum of 3–6 months before aggressive investing."
        )
    if metrics.overall_status == "excellent":
        st.success(
            "🟢 **Excellent Financial Health** — Your finances are in great shape! "
            "Focus on optimising your investment allocation to maximise long-term wealth."
        )


def _render_metric_cards(metrics: FinancialMetrics) -> None:
    """Render the 8 metric summary cards in grid layout."""
    st.markdown("### 📊 Key Financial Metrics")

    surplus_color = "#1E7145" if metrics.net_monthly_surplus >= 0 else "#C0392B"
    surplus_label = "Monthly Buffer" if metrics.net_monthly_surplus >= 0 else "Monthly Shortfall"

    cards = [
        {
            "label": surplus_label,
            "value": format_inr(metrics.net_monthly_surplus, compact=True),
            "sub": "Income − Expenses − Debt",
            "color": surplus_color,
        },
        {
            "label": "Savings Rate",
            "value": format_pct(metrics.savings_rate_pct),
            "sub": _status_label(metrics.savings_rate_status),
            "color": _status_color(metrics.savings_rate_status, invert=False),
        },
        {
            "label": "Expense Ratio",
            "value": format_pct(metrics.expense_ratio_pct),
            "sub": _status_label(metrics.expense_ratio_status),
            "color": _status_color(metrics.expense_ratio_status, invert=True),
        },
        {
            "label": "Debt-to-Income",
            "value": format_pct(metrics.dti_ratio_pct),
            "sub": _status_label(metrics.dti_status),
            "color": _status_color(metrics.dti_status, invert=True),
        },
        {
            "label": "Emergency Fund",
            "value": f"{metrics.emergency_fund_months:.1f} mo",
            "sub": _status_label(metrics.ef_status),
            "color": _status_color(metrics.ef_status, invert=False),
        },
        {
            "label": "Investable Surplus",
            "value": format_inr(metrics.investable_surplus, compact=True),
            "sub": "Safe to invest monthly",
            "color": "#2E75B6",
        },
        {
            "label": "Debt Payoff",
            "value": format_months(metrics.debt_payoff_months) if metrics.debt_payoff_months else "No Debt 🎉",
            "sub": "At current repayment rate",
            "color": "#595959",
        },
        {
            "label": "Health Score",
            "value": f"{metrics.financial_health_score}/100",
            "sub": format_score_label(metrics.financial_health_score),
            "color": score_to_color(metrics.financial_health_score),
        },
    ]

    # 4 cards per row
    for i in range(0, len(cards), 4):
        cols = st.columns(4)
        for j, card in enumerate(cards[i : i + 4]):
            with cols[j]:
                st.markdown(
                    f"""
                    <div style="
                        background:#EBF2FA;border-radius:10px;padding:16px 14px;
                        border-left:4px solid {card['color']};margin-bottom:12px;
                        min-height:90px;
                    ">
                        <div style="font-size:22px;font-weight:700;color:{card['color']};">{card['value']}</div>
                        <div style="font-size:12px;font-weight:600;color:#1F3864;text-transform:uppercase;margin:4px 0 2px;">{card['label']}</div>
                        <div style="font-size:11px;color:#595959;">{card['sub']}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )


def _render_metrics_table(metrics: FinancialMetrics, profile: FinancialProfile) -> None:
    """Render detailed metrics comparison table."""
    import pandas as pd

    st.markdown("### 📋 Detailed Metrics Breakdown")

    data = [
        {
            "Metric": "Net Monthly Surplus",
            "Your Value": format_inr(metrics.net_monthly_surplus),
            "Benchmark": "> ₹0",
            "Status": "✅" if metrics.net_monthly_surplus >= 0 else "🔴",
        },
        {
            "Metric": "Savings Rate",
            "Your Value": format_pct(metrics.savings_rate_pct),
            "Benchmark": "≥ 20%",
            "Status": "🟢" if metrics.savings_rate_pct >= 20 else ("🟡" if metrics.savings_rate_pct >= 10 else "🔴"),
        },
        {
            "Metric": "Expense Ratio",
            "Your Value": format_pct(metrics.expense_ratio_pct),
            "Benchmark": "< 50%",
            "Status": "🟢" if metrics.expense_ratio_pct < 50 else ("🟡" if metrics.expense_ratio_pct < 70 else "🔴"),
        },
        {
            "Metric": "Debt-to-Income Ratio",
            "Your Value": format_pct(metrics.dti_ratio_pct),
            "Benchmark": "< 15%",
            "Status": "🟢" if metrics.dti_ratio_pct < 15 else ("🟡" if metrics.dti_ratio_pct < 36 else "🔴"),
        },
        {
            "Metric": "Emergency Fund Coverage",
            "Your Value": f"{metrics.emergency_fund_months:.1f} months",
            "Benchmark": "3–6 months",
            "Status": "🟢" if metrics.emergency_fund_months >= 6 else ("🟡" if metrics.emergency_fund_months >= 3 else "🔴"),
        },
        {
            "Metric": "Investable Surplus",
            "Your Value": format_inr(metrics.investable_surplus),
            "Benchmark": "> ₹0",
            "Status": "✅" if metrics.investable_surplus > 0 else "🔴",
        },
        {
            "Metric": "Debt Payoff Timeline",
            "Your Value": format_months(metrics.debt_payoff_months) if metrics.debt_payoff_months else "No Debt",
            "Benchmark": "< 36 months",
            "Status": "🟢" if not metrics.debt_payoff_months or metrics.debt_payoff_months <= 36 else ("🟡" if metrics.debt_payoff_months <= 60 else "🔴"),
        },
    ]

    df = pd.DataFrame(data)
    st.dataframe(df, use_container_width=True, hide_index=True)


def _status_color(status: str, invert: bool = False) -> str:
    """Convert a status label to a hex colour. invert=True means 'high' is bad."""
    mapping = {
        "poor": "#C0392B",
        "moderate": "#F5A623",
        "healthy": "#1E7145",
        "low": "#1E7145",
        "manageable": "#F5A623",
        "high": "#C0392B" if invert else "#1E7145",
        "insufficient": "#C0392B",
        "adequate": "#F5A623",
        "strong": "#1E7145",
        "excellent": "#1E7145",
        "good": "#2E75B6",
        "needs_work": "#F5A623",
        "critical": "#C0392B",
    }
    return mapping.get(status, "#2E75B6")


def _status_label(status: str) -> str:
    return status.replace("_", " ").title()
