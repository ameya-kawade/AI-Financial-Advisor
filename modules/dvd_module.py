"""
Module 5: Data Visualisation Dashboard (DVD)
Generates all 8 interactive Plotly charts and renders the tabbed dashboard.
"""

from __future__ import annotations

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np

from models.financial_metrics import FinancialMetrics
from models.financial_profile import FinancialProfile
from models.goal_plan import GoalPlan
from utils.calculators import compute_future_value
from utils.formatters import format_inr, score_to_color

# Updated colour palette — aligned with new design system
COLORS = {
    "primary":  "#2563EB",   # Professional blue
    "accent":   "#6366F1",   # Secondary indigo
    "success":  "#10B981",   # Accent green
    "warning":  "#F59E0B",   # Amber
    "danger":   "#EF4444",   # Red
    "neutral":  "#64748B",   # Slate grey
    "text":     "#0F172A",   # Near-black
    "bg":       "#F8FAFC",   # Off-white
}

ASSET_COLORS = [
    "#2563EB", "#6366F1", "#10B981", "#F59E0B", "#EF4444", "#8B5CF6",
]


def generate_charts(
    profile: FinancialProfile,
    metrics: FinancialMetrics,
    goals: list[GoalPlan],
    advice: dict,
) -> dict[str, go.Figure]:
    """
    Generate all 8 Plotly figures.

    Each chart is built inside its own try/except so that a single failure
    does not abort the rest of the dashboard.

    Returns:
        Dict mapping chart_id strings to Plotly Figure objects.
        Missing keys indicate a chart that failed to generate.
    """
    chart_builders = {
        "budget_donut":        lambda: _budget_donut(profile, metrics),
        "health_bar":          lambda: _health_metrics_bar(metrics, profile),
        "goal_projection":     lambda: _goal_projection(goals),
        "portfolio_pie":       lambda: _portfolio_pie(goals, profile),
        "cash_flow_waterfall": lambda: _cash_flow_waterfall(profile, metrics),
        "health_gauge":        lambda: _health_gauge(metrics),
        "wealth_growth":       lambda: _wealth_growth(metrics, profile),
        "goal_feasibility":    lambda: _goal_feasibility_chart(goals, metrics),
    }

    charts: dict[str, go.Figure] = {}
    for key, builder in chart_builders.items():
        try:
            charts[key] = builder()
        except Exception as exc:  # noqa: BLE001
            import traceback
            st.caption(f"⚠️ Chart '{key}' could not be generated — refresh to retry.")
            traceback.print_exc()

    return charts


def _safe_plotly_chart(
    fig: go.Figure | None,
    chart_name: str = "chart",
    **kwargs,
) -> None:
    """
    Bug 4 fix: render a Plotly figure only if it is not None.
    Passing None to st.plotly_chart() raises a ValueError.
    """
    if fig is not None:
        st.plotly_chart(fig, **kwargs)
    else:
        st.info(f"📊 *{chart_name} unavailable — please refresh the dashboard.*")


def render_dashboard(
    profile: FinancialProfile,
    metrics: FinancialMetrics,
    goals: list[GoalPlan],
    charts: dict[str, go.Figure],
) -> None:
    """Render the tabbed dashboard with all charts."""
    st.markdown(
        """
        <div class="page-header">
            <div class="page-header-icon">📈</div>
            <div>
                <div class="page-header-title">Visualisation Dashboard</div>
                <div class="page-header-sub">Interactive charts powered by Plotly. Hover for details, download via camera icon.</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Overview",
        "🎯 Goals",
        "💼 Portfolio",
        "💵 Cash Flow",
        "📉 Projections",
    ])

    with tab1:
        c1, c2 = st.columns(2)
        with c1:
            _safe_plotly_chart(charts.get("health_gauge"), "Health Gauge", use_container_width=True)
        with c2:
            _safe_plotly_chart(charts.get("budget_donut"), "Budget Breakdown", use_container_width=True)
        _safe_plotly_chart(charts.get("health_bar"), "Health Metrics Bar", use_container_width=True)

    with tab2:
        if goals:
            _safe_plotly_chart(charts.get("goal_projection"), "Goal Projection", use_container_width=True)
            _safe_plotly_chart(charts.get("goal_feasibility"), "Goal Feasibility", use_container_width=True)
        else:
            st.info("No goals defined. Add goals in your Financial Profile.")

    with tab3:
        _safe_plotly_chart(charts.get("portfolio_pie"), "Portfolio Allocation", use_container_width=True)

    with tab4:
        _safe_plotly_chart(charts.get("cash_flow_waterfall"), "Cash Flow Waterfall", use_container_width=True)

    with tab5:
        _safe_plotly_chart(charts.get("wealth_growth"), "Wealth Growth", use_container_width=True)


# ── Individual Chart Generators ───────────────────────────────────────────────

def _chart_layout_defaults() -> dict:
    """Shared Plotly layout defaults for a clean, consistent look."""
    return {
        "paper_bgcolor": "rgba(0,0,0,0)",
        "plot_bgcolor": COLORS["bg"],
        "font": {"family": "Inter, sans-serif", "color": COLORS["text"]},
        "margin": {"t": 64, "b": 60, "l": 24, "r": 24},
    }


def _budget_donut(profile: FinancialProfile, metrics: FinancialMetrics) -> go.Figure:
    """Donut chart showing income allocation breakdown."""
    labels = ["Expenses", "Debt Repayments", "Investable Surplus", "Emergency Buffer"]
    surplus = max(metrics.net_monthly_surplus, 0)
    buffer = surplus * 0.10
    investable = metrics.investable_surplus

    values = [
        profile.monthly_expenses,
        profile.monthly_debt_repayments,
        max(investable, 0),
        buffer,
    ]
    colors = [COLORS["warning"], COLORS["danger"], COLORS["success"], COLORS["primary"]]

    filtered = [(l, v, c) for l, v, c in zip(labels, values, colors) if v > 0]
    if not filtered:
        labels, values, colors = ["Income"], [profile.monthly_income], [COLORS["primary"]]
    else:
        labels, values, colors = zip(*filtered)

    fig = go.Figure(go.Pie(
        labels=list(labels),
        values=list(values),
        hole=0.58,
        marker=dict(colors=list(colors), line=dict(color="white", width=2.5)),
        textinfo="label+percent",
        hovertemplate="<b>%{label}</b><br>₹%{value:,.0f}<br>%{percent}<extra></extra>",
    ))
    fig.update_layout(
        title=dict(text="Monthly Budget Breakdown", font=dict(size=15, color=COLORS["text"])),
        legend=dict(orientation="h", yanchor="bottom", y=-0.22, font=dict(size=12)),
        annotations=[dict(
            text=f"₹{profile.monthly_income/1000:.0f}K",
            x=0.5, y=0.5,
            font_size=22,
            font_color=COLORS["text"],
            showarrow=False,
        )],
        **_chart_layout_defaults(),
    )
    return fig


def _health_metrics_bar(metrics: FinancialMetrics, profile: FinancialProfile) -> go.Figure:
    """Bar chart comparing actual metrics vs benchmarks."""
    metric_names = ["Savings Rate", "Expense Ratio", "DTI Ratio", "Emergency Fund (mo)"]
    actuals = [
        metrics.savings_rate_pct,
        metrics.expense_ratio_pct,
        metrics.dti_ratio_pct,
        metrics.emergency_fund_months,
    ]
    benchmarks = [20, 50, 15, 6]
    bench_labels = ["Target: 20%", "Target: <50%", "Target: <15%", "Target: 6mo"]

    colors_actual = []
    for i, (actual, bench) in enumerate(zip(actuals, benchmarks)):
        if i == 0:  # savings rate: higher is better
            colors_actual.append(COLORS["success"] if actual >= bench else COLORS["warning"])
        else:  # lower is better
            colors_actual.append(COLORS["success"] if actual <= bench else COLORS["danger"])

    fig = go.Figure()
    fig.add_trace(go.Bar(
        name="Your Value",
        x=metric_names,
        y=actuals,
        marker_color=colors_actual,
        marker_line_color="white",
        marker_line_width=1.5,
        text=[f"{v:.1f}" for v in actuals],
        textposition="auto",
        hovertemplate="<b>%{x}</b><br>Your value: %{y:.1f}<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        name="Benchmark",
        x=metric_names,
        y=benchmarks,
        mode="markers+text",
        marker=dict(symbol="line-ew", size=22, color=COLORS["text"], line_width=3),
        text=bench_labels,
        textposition="top center",
        hovertemplate="<b>Benchmark</b>: %{y}<extra></extra>",
    ))
    layout = _chart_layout_defaults()
    layout["margin"]["b"] = 80
    fig.update_layout(
        title=dict(text="Financial Metrics vs Benchmarks", font=dict(size=15, color=COLORS["text"])),
        yaxis_title="Value",
        barmode="group",
        legend=dict(orientation="h", yanchor="bottom", y=-0.28, font=dict(size=12)),
        **layout,
    )
    return fig


def _goal_projection(goals: list[GoalPlan]) -> go.Figure:
    """Line chart showing month-by-month savings accumulation toward each goal."""
    fig = go.Figure()

    color_cycle = [
        COLORS["primary"], COLORS["success"], COLORS["warning"],
        COLORS["danger"], COLORS["accent"],
    ]

    for i, goal in enumerate(goals[:5]):
        months = list(range(0, goal.target_months + 1))
        r = goal.expected_return_rate / 12 / 100

        cumulative = []
        running = 0
        for m in months:
            if m == 0:
                cumulative.append(0)
            else:
                running = running * (1 + r) + goal.required_monthly_saving
                cumulative.append(running)

        color = color_cycle[i % len(color_cycle)]
        fig.add_trace(go.Scatter(
            x=months,
            y=cumulative,
            mode="lines",
            name=goal.goal_name,
            line=dict(color=color, width=2.5),
            hovertemplate=f"<b>{goal.goal_name}</b><br>Month %{{x}}<br>₹%{{y:,.0f}}<extra></extra>",
        ))
        fig.add_hline(
            y=goal.inflation_adjusted_target,
            line_dash="dot",
            line_color=color,
            annotation_text=f"{goal.goal_name} target",
            annotation_position="bottom right",
        )

    layout = _chart_layout_defaults()
    layout["margin"]["b"] = 100
    fig.update_layout(
        title=dict(text="Goal Savings Projection (Month by Month)", font=dict(size=15, color=COLORS["text"])),
        xaxis_title="Months",
        yaxis_title="Accumulated Savings (INR)",
        legend=dict(orientation="h", yanchor="bottom", y=-0.3, font=dict(size=12)),
        hovermode="x unified",
        **layout,
    )
    return fig


def _portfolio_pie(goals: list[GoalPlan], profile: FinancialProfile) -> go.Figure:
    """Pie chart of recommended asset allocation from the primary goal."""
    if goals:
        allocation = goals[0].allocation_breakdown
    else:
        from config.allocation_matrix import get_allocation
        allocation = get_allocation(
            profile.investment_horizon.value,
            profile.risk_tolerance.value,
        )

    labels = list(allocation.keys())
    values = list(allocation.values())

    fig = go.Figure(go.Pie(
        labels=labels,
        values=values,
        hole=0.42,
        marker=dict(colors=ASSET_COLORS[:len(labels)], line=dict(color="white", width=2.5)),
        textinfo="label+percent",
        hovertemplate="<b>%{label}</b><br>%{value}% allocation<extra></extra>",
    ))
    layout = _chart_layout_defaults()
    layout["margin"]["b"] = 80
    fig.update_layout(
        title=dict(
            text=f"Portfolio Allocation — {profile.risk_tolerance.value.title()} / {profile.investment_horizon.value.title()}",
            font=dict(size=15, color=COLORS["text"]),
        ),
        legend=dict(orientation="h", yanchor="bottom", y=-0.28, font=dict(size=12)),
        **layout,
    )
    return fig


def _cash_flow_waterfall(profile: FinancialProfile, metrics: FinancialMetrics) -> go.Figure:
    """Waterfall chart of monthly cash flow."""
    surplus = metrics.net_monthly_surplus
    fig = go.Figure(go.Waterfall(
        name="Cash Flow",
        orientation="v",
        measure=["absolute", "relative", "relative", "total"],
        x=["Income", "Expenses", "Debt Repayments", "Net Surplus"],
        y=[profile.monthly_income, -profile.monthly_expenses, -profile.monthly_debt_repayments, surplus],
        connector=dict(line=dict(color=COLORS["neutral"], width=0.5, dash="dot")),
        increasing=dict(marker=dict(color=COLORS["success"])),
        decreasing=dict(marker=dict(color=COLORS["danger"])),
        totals=dict(marker=dict(color=COLORS["primary"])),
        text=[
            format_inr(profile.monthly_income, compact=True),
            f"-{format_inr(profile.monthly_expenses, compact=True)}",
            f"-{format_inr(profile.monthly_debt_repayments, compact=True)}",
            format_inr(surplus, compact=True),
        ],
        textposition="outside",
        hovertemplate="<b>%{x}</b><br>₹%{y:,.0f}<extra></extra>",
    ))
    fig.update_layout(
        title=dict(text="Monthly Cash Flow Breakdown", font=dict(size=15, color=COLORS["text"])),
        yaxis_title="Amount (INR)",
        showlegend=False,
        **_chart_layout_defaults(),
    )
    return fig


def _health_gauge(metrics: FinancialMetrics) -> go.Figure:
    """Gauge chart for financial health score."""
    score = metrics.financial_health_score
    color = score_to_color(score)

    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=score,
        domain={"x": [0, 1], "y": [0, 1]},
        title={"text": "Financial Health Score", "font": {"size": 15, "color": COLORS["text"]}},
        delta={"reference": 60, "increasing": {"color": COLORS["success"]}},
        gauge={
            "axis": {"range": [0, 100], "tickwidth": 1, "tickcolor": COLORS["neutral"]},
            "bar": {"color": color},
            "bgcolor": "white",
            "borderwidth": 1.5,
            "bordercolor": "#E2E8F0",
            "steps": [
                {"range": [0,  40], "color": "#FEE2E2"},
                {"range": [40, 60], "color": "#FEF3C7"},
                {"range": [60, 80], "color": "#DBEAFE"},
                {"range": [80, 100], "color": "#D1FAE5"},
            ],
            "threshold": {
                "line": {"color": COLORS["text"], "width": 3},
                "thickness": 0.75,
                "value": 60,
            },
        },
        number={"font": {"size": 44, "color": color, "family": "Inter, sans-serif"}},
    ))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(t=80, b=20, l=28, r=28),
        height=280,
        font={"family": "Inter, sans-serif"},
    )
    return fig


def _wealth_growth(metrics: FinancialMetrics, profile: FinancialProfile) -> go.Figure:
    """Area chart of compound wealth growth over 0–30 years."""
    from config.settings import EXPECTED_RETURN_RATES

    if metrics.investable_surplus <= 0:
        fig = go.Figure()
        fig.add_annotation(
            text="No investable surplus to project",
            showarrow=False,
            font_size=16,
            font_color=COLORS["neutral"],
        )
        fig.update_layout(**_chart_layout_defaults())
        return fig

    monthly_invest = metrics.investable_surplus
    years_range = list(range(0, 31))
    months_range = [y * 12 for y in years_range]

    fig = go.Figure()

    scenarios = [
        ("Conservative (7%)",  7.0,  COLORS["primary"]),
        ("Moderate (10%)",    10.0,  COLORS["success"]),
        ("Aggressive (12%)",  12.0,  COLORS["danger"]),
    ]

    for label, rate, color in scenarios:
        values = [compute_future_value(monthly_invest, m, rate) for m in months_range]
        fig.add_trace(go.Scatter(
            x=years_range,
            y=values,
            mode="lines",
            fill="tonexty" if label != "Conservative (7%)" else "tozeroy",
            name=label,
            line=dict(color=color, width=2.5),
            fillcolor=color + "1A",
            hovertemplate=f"<b>{label}</b><br>Year %{{x}}<br>₹%{{y:,.0f}}<extra></extra>",
        ))

    layout = _chart_layout_defaults()
    layout["margin"]["b"] = 100
    fig.update_layout(
        title=dict(
            text=f"Wealth Growth Projection (₹{monthly_invest:,.0f}/mo invested)",
            font=dict(size=15, color=COLORS["text"]),
        ),
        xaxis_title="Years",
        yaxis_title="Portfolio Value (INR)",
        legend=dict(orientation="h", yanchor="bottom", y=-0.28, font=dict(size=12)),
        hovermode="x unified",
        **layout,
    )
    return fig


def _goal_feasibility_chart(goals: list[GoalPlan], metrics: FinancialMetrics) -> go.Figure:
    """Horizontal bar chart: required vs available monthly savings per goal."""
    goal_names = [g.goal_name for g in goals]
    required = [g.required_monthly_saving for g in goals]
    available = [metrics.investable_surplus] * len(goals)

    fig = go.Figure()
    fig.add_trace(go.Bar(
        name="Required Monthly",
        y=goal_names,
        x=required,
        orientation="h",
        marker_color=COLORS["warning"],
        marker_line_color="white",
        marker_line_width=1,
        text=[format_inr(r, compact=True) for r in required],
        textposition="auto",
    ))
    fig.add_trace(go.Bar(
        name="Investable Surplus",
        y=goal_names,
        x=available,
        orientation="h",
        marker_color=COLORS["success"],
        marker_line_color="white",
        marker_line_width=1,
        text=[format_inr(a, compact=True) for a in available],
        textposition="auto",
    ))
    layout = _chart_layout_defaults()
    layout["margin"]["b"] = 80
    fig.update_layout(
        title=dict(
            text="Goal Feasibility: Required vs Available Monthly Savings",
            font=dict(size=15, color=COLORS["text"]),
        ),
        xaxis_title="Monthly Amount (INR)",
        barmode="group",
        legend=dict(orientation="h", yanchor="bottom", y=-0.28, font=dict(size=12)),
        **layout,
    )
    return fig
