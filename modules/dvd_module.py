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

# Theme configuration
BG_CHART   = "rgba(0,0,0,0)"
BG_PLOT    = "#0D1526"
GRID_CLR   = "#1E2E47"
FONT_CLR   = "#F0F6FF"
FONT_MUTED = "#7A9CC0"

COLORS = {
    "primary":  "#0EA5E9",
    "accent":   "#8B5CF6",
    "success":  "#10B981",
    "warning":  "#F59E0B",
    "danger":   "#EF4444",
    "neutral":  "#415E80",
    "text":     "#F0F6FF",
    "bg":       "#0D1526",
    "amber":    "#F59E0B",
    "cyan":     "#06B6D4",
    "rose":     "#F43F5E",
}

ASSET_COLORS = [
    "#0EA5E9", "#8B5CF6", "#10B981", "#F59E0B",
    "#EF4444", "#06B6D4", "#F43F5E", "#A3E635",
]

# Utility functions

def hex_to_rgba(hex_color: str, opacity: float) -> str:

    hex_color = hex_color.lstrip('#')
    r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    return f"rgba({r}, {g}, {b}, {opacity})"

def generate_charts(
    profile: FinancialProfile,
    metrics: FinancialMetrics,
    goals: list[GoalPlan],
    advice: dict,
) -> dict[str, go.Figure]:
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
        except Exception as exc:
            import traceback
            st.caption(f"⚠️ Chart '{key}' could not be generated — refresh to retry.")
            traceback.print_exc()

    return charts


def _safe_plotly_chart(fig: go.Figure | None, chart_name: str = "chart", **kwargs) -> None:
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
            _safe_plotly_chart(charts.get("health_gauge"), "Health Gauge", width="stretch")
        with c2:
            _safe_plotly_chart(charts.get("budget_donut"), "Budget Breakdown", width="stretch")
        _safe_plotly_chart(charts.get("health_bar"), "Health Metrics Bar", width="stretch")

    with tab2:
        if goals:
            _safe_plotly_chart(charts.get("goal_projection"), "Goal Projection", width="stretch")
            _safe_plotly_chart(charts.get("goal_feasibility"), "Goal Feasibility", width="stretch")
        else:
            st.info("No goals defined. Add goals in your Financial Profile.")

    with tab3:
        _safe_plotly_chart(charts.get("portfolio_pie"), "Portfolio Allocation", width="stretch")

    with tab4:
        _safe_plotly_chart(charts.get("cash_flow_waterfall"), "Cash Flow Waterfall", width="stretch")

    with tab5:
        _safe_plotly_chart(charts.get("wealth_growth"), "Wealth Growth", width="stretch")


# Chart settings

def _chart_layout_defaults() -> dict:
    return {
        "paper_bgcolor": BG_CHART,
        "plot_bgcolor": BG_PLOT,
        "font": {"family": "DM Sans, sans-serif", "color": FONT_CLR, "size": 12},
        "margin": {"t": 70, "b": 60, "l": 30, "r": 30},
        "xaxis": {
            "gridcolor": GRID_CLR,
            "zerolinecolor": GRID_CLR,
            "tickfont": {"color": FONT_MUTED, "size": 11},
            "title_font": {"color": FONT_MUTED},
            "linecolor": GRID_CLR,
        },
        "yaxis": {
            "gridcolor": GRID_CLR,
            "zerolinecolor": GRID_CLR,
            "tickfont": {"color": FONT_MUTED, "size": 11},
            "title_font": {"color": FONT_MUTED},
            "linecolor": GRID_CLR,
        },
        "legend": {
            "bgcolor": "rgba(13,21,38,0.8)",
            "bordercolor": GRID_CLR,
            "borderwidth": 1,
            "font": {"color": FONT_MUTED, "size": 12},
        },
    }


# Chart builders

def _budget_donut(profile: FinancialProfile, metrics: FinancialMetrics) -> go.Figure:
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
        hole=0.62,
        marker=dict(
            colors=list(colors),
            line=dict(color=BG_PLOT, width=3),
        ),
        textinfo="label+percent",
        textfont=dict(size=12, color=FONT_CLR),
        hovertemplate="<b>%{label}</b><br>₹%{value:,.0f}<br>%{percent}<extra></extra>",
        pull=[0.03] * len(labels),
    ))
    fig.update_layout(
        title=dict(
            text="Monthly Budget Breakdown",
            font=dict(size=15, color=FONT_CLR, family="DM Sans, sans-serif"),
            x=0.5,
        ),
        legend=dict(
            orientation="h", yanchor="bottom", y=-0.25,
            font=dict(size=11, color=FONT_MUTED),
            bgcolor="rgba(0,0,0,0)",
        ),
        annotations=[dict(
            text=f"<b>₹{profile.monthly_income/1000:.0f}K</b>",
            x=0.5, y=0.5,
            font=dict(size=22, color=FONT_CLR, family="DM Sans, sans-serif"),
            showarrow=False,
        )],
        **{k: v for k, v in _chart_layout_defaults().items() if k not in ("xaxis", "yaxis", "legend")},
        height=360,
    )
    return fig


def _health_metrics_bar(metrics: FinancialMetrics, profile: FinancialProfile) -> go.Figure:
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
        if i == 0:
            colors_actual.append(COLORS["success"] if actual >= bench else COLORS["warning"])
        else:
            colors_actual.append(COLORS["success"] if actual <= bench else COLORS["danger"])

    fig = go.Figure()
    fig.add_trace(go.Bar(
        name="Your Value",
        x=metric_names,
        y=actuals,
        marker=dict(
            color=colors_actual,
            line=dict(color=BG_PLOT, width=2),
            opacity=0.9,
        ),
        text=[f"{v:.1f}" for v in actuals],
        textposition="auto",
        textfont=dict(color=FONT_CLR, size=12),
        hovertemplate="<b>%{x}</b><br>Your value: <b>%{y:.1f}</b><extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        name="Benchmark",
        x=metric_names,
        y=benchmarks,
        mode="markers+text",
        marker=dict(
            symbol="line-ew", size=28,
            color=COLORS["amber"],
            line=dict(width=3, color=COLORS["amber"]),
        ),
        text=bench_labels,
        textposition="top center",
        textfont=dict(size=11, color=COLORS["amber"]),
        hovertemplate="<b>Benchmark</b>: %{y}<extra></extra>",
    ))
    layout = _chart_layout_defaults()
    layout["margin"]["b"] = 90
    layout["yaxis"]["title"] = "Value"
    fig.update_layout(
        title=dict(
            text="Financial Metrics vs Benchmarks",
            font=dict(size=15, color=FONT_CLR, family="DM Sans, sans-serif"),
            x=0.5,
        ),
        barmode="group",
        bargap=0.3,
        legend=dict(
            orientation="h", yanchor="bottom", y=-0.32,
            font=dict(size=12, color=FONT_MUTED),
            bgcolor="rgba(0,0,0,0)",
        ),
        height=380,
        **{k: v for k, v in layout.items() if k != "legend"},
    )
    return fig


def _goal_projection(goals: list[GoalPlan]) -> go.Figure:
    fig = go.Figure()

    color_cycle = [
        COLORS["primary"], COLORS["success"], COLORS["warning"],
        COLORS["danger"], COLORS["accent"],
    ]

    for i, goal in enumerate(goals[:5]):
        months = list(range(0, int(goal.target_months) + 1))
        r = goal.expected_return_rate / 12 / 100

        cumulative = []
        running: float = 0.0
        for m in months:
            if m == 0:
                cumulative.append(0.0)
            else:
                running = running * (1.0 + r) + goal.required_monthly_saving
                cumulative.append(running)

        color = color_cycle[i % len(color_cycle)]
        fig.add_trace(go.Scatter(
            x=months,
            y=cumulative,
            mode="lines",
            name=goal.goal_name,
            line=dict(color=color, width=2.5, shape="spline"),
            fill="tozeroy",
            fillcolor=hex_to_rgba(color, 0.15),
            hovertemplate=f"<b>{goal.goal_name}</b><br>Month %{{x}}<br>₹%{{y:,.0f}}<extra></extra>",
        ))
        fig.add_hline(
            y=goal.inflation_adjusted_target,
            line_dash="dot",
            line_color=color,
            line_width=1.5,
            annotation_text=f"{goal.goal_name} target",
            annotation_position="bottom right",
            annotation=dict(font=dict(size=10, color=color)),
        )

    layout = _chart_layout_defaults()
    layout["margin"]["b"] = 100
    layout["xaxis"]["title"] = "Months"
    layout["yaxis"]["title"] = "Accumulated Savings (INR)"
    fig.update_layout(
        title=dict(
            text="Goal Savings Projection",
            font=dict(size=15, color=FONT_CLR, family="DM Sans, sans-serif"),
            x=0.5,
        ),
        hovermode="x unified",
        height=400,
        **layout,
    )
    return fig


def _portfolio_pie(goals: list[GoalPlan], profile: FinancialProfile) -> go.Figure:
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
        hole=0.50,
        marker=dict(
            colors=ASSET_COLORS[:len(labels)],
            line=dict(color=BG_PLOT, width=3),
        ),
        textinfo="label+percent",
        textfont=dict(size=12, color=FONT_CLR),
        hovertemplate="<b>%{label}</b><br>%{value}% allocation<extra></extra>",
        pull=[0.04 if i == 0 else 0 for i in range(len(labels))],
    ))
    layout = _chart_layout_defaults()
    layout["margin"]["b"] = 80
    fig.update_layout(
        title=dict(
            text=f"Portfolio Allocation — {profile.risk_tolerance.value.title()} / {profile.investment_horizon.value.title()}",
            font=dict(size=15, color=FONT_CLR, family="DM Sans, sans-serif"),
            x=0.5,
        ),
        legend=dict(
            orientation="h", yanchor="bottom", y=-0.28,
            font=dict(size=12, color=FONT_MUTED),
            bgcolor="rgba(0,0,0,0)",
        ),
        height=400,
        **{k: v for k, v in layout.items() if k not in ("xaxis", "yaxis", "legend")},
    )
    return fig


def _cash_flow_waterfall(profile: FinancialProfile, metrics: FinancialMetrics) -> go.Figure:
    surplus = metrics.net_monthly_surplus
    fig = go.Figure(go.Waterfall(
        name="Cash Flow",
        orientation="v",
        measure=["absolute", "relative", "relative", "total"],
        x=["Income", "Expenses", "Debt Repayments", "Net Surplus"],
        y=[profile.monthly_income, -profile.monthly_expenses, -profile.monthly_debt_repayments, surplus],
        connector=dict(line=dict(color=GRID_CLR, width=1, dash="dot")),
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
        textfont=dict(color=FONT_CLR, size=12),
        hovertemplate="<b>%{x}</b><br>₹%{y:,.0f}<extra></extra>",
    ))
    layout = _chart_layout_defaults()
    layout["yaxis"]["title"] = "Amount (INR)"
    fig.update_layout(
        title=dict(
            text="Monthly Cash Flow Breakdown",
            font=dict(size=15, color=FONT_CLR, family="DM Sans, sans-serif"),
            x=0.5,
        ),
        showlegend=False,
        height=380,
        **layout,
    )
    return fig


def _health_gauge(metrics: FinancialMetrics) -> go.Figure:
    score = metrics.financial_health_score
    color = score_to_color(score)

    # Remap colors to dark theme
    _score_map = {
        "#10B981": "#10B981",
        "#2563EB": "#0EA5E9",
        "#F59E0B": "#F59E0B",
        "#EF4444": "#EF4444",
    }
    color = _score_map.get(color, color)

    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=score,
        domain={"x": [0, 1], "y": [0, 1]},
        title={"text": "Financial Health Score", "font": {"size": 14, "color": FONT_MUTED, "family": "DM Sans, sans-serif"}},
        delta={"reference": 60, "increasing": {"color": COLORS["success"]}, "font": {"size": 13}},
        gauge={
            "axis": {
                "range": [0, 100],
                "tickwidth": 1,
                "tickcolor": GRID_CLR,
                "tickfont": {"color": FONT_MUTED, "size": 10},
            },
            "bar": {"color": color, "thickness": 0.28},
            "bgcolor": BG_PLOT,
            "borderwidth": 1,
            "bordercolor": GRID_CLR,
            "steps": [
                {"range": [0, 40],  "color": "rgba(239,68,68,0.15)"},
                {"range": [40, 60], "color": "rgba(245,158,11,0.12)"},
                {"range": [60, 80], "color": "rgba(14,165,233,0.12)"},
                {"range": [80, 100], "color": "rgba(16,185,129,0.15)"},
            ],
            "threshold": {
                "line": {"color": FONT_CLR, "width": 2},
                "thickness": 0.75,
                "value": 60,
            },
        },
        number={
            "font": {"size": 48, "color": color, "family": "DM Mono, monospace"},
            "suffix": "",
        },
    ))
    fig.update_layout(
        paper_bgcolor=BG_CHART,
        plot_bgcolor=BG_PLOT,
        margin=dict(t=80, b=20, l=28, r=28),
        height=300,
        font={"family": "DM Sans, sans-serif", "color": FONT_CLR},
    )
    return fig


def _wealth_growth(metrics: FinancialMetrics, profile: FinancialProfile) -> go.Figure:
    if metrics.investable_surplus <= 0:
        fig = go.Figure()
        fig.add_annotation(
            text="No investable surplus to project",
            showarrow=False,
            font=dict(size=16, color=FONT_MUTED),
        )
        fig.update_layout(paper_bgcolor=BG_CHART, plot_bgcolor=BG_PLOT, height=380)
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
            line=dict(color=color, width=2.5, shape="spline"),
            fillcolor=hex_to_rgba(color, 0.12),
            hovertemplate=f"<b>{label}</b><br>Year %{{x}}<br>₹%{{y:,.0f}}<extra></extra>",
        ))

    layout = _chart_layout_defaults()
    layout["margin"]["b"] = 80
    layout["xaxis"]["title"] = "Years"
    layout["yaxis"]["title"] = "Portfolio Value (INR)"
    fig.update_layout(
        title=dict(
            text=f"Wealth Growth Projection  (\u20b9{monthly_invest:,.0f}/mo invested)",
            font=dict(size=15, color=FONT_CLR, family="DM Sans, sans-serif"),
            x=0.5,
        ),
        hovermode="x unified",
        height=420,
        **layout,
    )
    return fig


def _goal_feasibility_chart(goals: list[GoalPlan], metrics: FinancialMetrics) -> go.Figure:
    goal_names = [g.goal_name for g in goals]
    required = [g.required_monthly_saving for g in goals]
    available = [metrics.investable_surplus] * len(goals)

    fig = go.Figure()
    fig.add_trace(go.Bar(
        name="Required Monthly",
        y=goal_names,
        x=required,
        orientation="h",
        marker=dict(color=COLORS["warning"], opacity=0.85, line=dict(color=BG_PLOT, width=1.5)),
        text=[format_inr(r, compact=True) for r in required],
        textposition="auto",
        textfont=dict(color=FONT_CLR, size=11),
    ))
    fig.add_trace(go.Bar(
        name="Investable Surplus",
        y=goal_names,
        x=available,
        orientation="h",
        marker=dict(color=COLORS["success"], opacity=0.85, line=dict(color=BG_PLOT, width=1.5)),
        text=[format_inr(a, compact=True) for a in available],
        textposition="auto",
        textfont=dict(color=FONT_CLR, size=11),
    ))
    layout = _chart_layout_defaults()
    layout["margin"]["b"] = 80
    layout["xaxis"]["title"] = "Monthly Amount (INR)"
    fig.update_layout(
        title=dict(
            text="Goal Feasibility: Required vs Available Monthly Savings",
            font=dict(size=15, color=FONT_CLR, family="DM Sans, sans-serif"),
            x=0.5,
        ),
        barmode="group",
        bargap=0.25,
        height=max(300, 80 + len(goals) * 60),
        **layout,
    )
    return fig