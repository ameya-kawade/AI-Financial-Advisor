"""
Module 1: Financial Profile Input (FPI)
Renders the profile input form and validates user data into a FinancialProfile model.
"""

from __future__ import annotations

import re
from typing import Any

import streamlit as st
from pydantic import ValidationError

from config.settings import SAMPLE_PROFILE
from models.financial_profile import FinancialProfile, GoalInput, InvestmentHorizon, RiskTolerance
from utils.validators import sanitise_text

GOAL_OPTIONS = [
    "Emergency Fund",
    "Home Purchase",
    "Retirement",
    "Child Education",
    "Travel",
    "Wealth Creation",
]

INVESTMENT_OPTIONS = ["FD", "Mutual Funds", "PPF", "NPS", "Stocks", "Gold", "None"]

OCCUPATION_OPTIONS = ["Student", "Salaried", "Self-Employed", "Retired"]

HORIZON_MAP = {
    "Short (<3yr)": InvestmentHorizon.SHORT,
    "Medium (3–7yr)": InvestmentHorizon.MEDIUM,
    "Long (>7yr)": InvestmentHorizon.LONG,
}

RISK_MAP = {
    "Conservative": RiskTolerance.CONSERVATIVE,
    "Moderate": RiskTolerance.MODERATE,
    "Aggressive": RiskTolerance.AGGRESSIVE,
}


def render_profile_form() -> None:
    """Render the complete financial profile input form with validation."""

    # ── Page header ──────────────────────────────────────────────────────────
    st.markdown(
        """
        <div class="page-header">
            <div class="page-header-icon">📋</div>
            <div>
                <div class="page-header-title">Financial Profile</div>
                <div class="page-header-sub">Fill in your financial details to get personalised advice.</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ── Action buttons ───────────────────────────────────────────────────────
    col_sample, col_clear, _ = st.columns([1.1, 1, 5])
    with col_sample:
        if st.button("🎯 Load Sample", help="Pre-fill with Priya's demo profile"):
            _load_sample_data()
    with col_clear:
        if st.button("🗑️ Clear Form", help="Clear all form fields"):
            _clear_form()
            st.rerun()

    st.markdown("<div style='margin-top:16px;'></div>", unsafe_allow_html=True)

    # ── Section 1: Personal Information ──────────────────────────────────────
    st.markdown("<div class='section-label'>👤 Personal Information</div>", unsafe_allow_html=True)
    with st.container():
        c1, c2, c3 = st.columns(3)
        with c1:
            name = st.text_input(
                "Full Name *",
                value=st.session_state.get("form_name", ""),
                placeholder="e.g. Priya Sharma",
                key="form_name",
            )
        with c2:
            age = st.number_input(
                "Age *",
                min_value=16,
                max_value=100,
                value=st.session_state.get("form_age", 30),
                step=1,
                key="form_age",
            )
        with c3:
            occupation = st.selectbox(
                "Occupation *",
                OCCUPATION_OPTIONS,
                index=OCCUPATION_OPTIONS.index(st.session_state.get("form_occupation", "Salaried")),
                key="form_occupation",
            )

    # ── Section 2: Income & Expenses ─────────────────────────────────────────
    st.markdown("<div class='section-label'>💰 Income &amp; Expenses (INR / month)</div>", unsafe_allow_html=True)

    # Row 1: income, expenses, savings
    c1, c2, c3 = st.columns(3)
    with c1:
        monthly_income = st.number_input(
            "Monthly Income *",
            min_value=0.0,
            value=float(st.session_state.get("form_income", 0.0)),
            step=1000.0,
            format="%.0f",
            key="form_income",
            help="Gross monthly income before deductions",
        )
    with c2:
        monthly_expenses = st.number_input(
            "Monthly Expenses *",
            min_value=0.0,
            value=float(st.session_state.get("form_expenses", 0.0)),
            step=1000.0,
            format="%.0f",
            key="form_expenses",
            help="Total living expenses (rent, food, utilities, etc.)",
        )
    with c3:
        current_savings = st.number_input(
            "Current Savings *",
            min_value=0.0,
            value=float(st.session_state.get("form_savings", 0.0)),
            step=10000.0,
            format="%.0f",
            key="form_savings",
            help="Total liquid savings available right now",
        )

    # Row 2: debt columns
    c4, c5, _ = st.columns([1, 1, 1])
    with c4:
        monthly_debt = st.number_input(
            "Monthly Debt Repayments *",
            min_value=0.0,
            value=float(st.session_state.get("form_debt_monthly", 0.0)),
            step=500.0,
            format="%.0f",
            key="form_debt_monthly",
            help="Total EMI / loan payments per month",
        )
    with c5:
        total_debt = st.number_input(
            "Total Debt Outstanding",
            min_value=0.0,
            value=float(st.session_state.get("form_debt_total", 0.0)),
            step=10000.0,
            format="%.0f",
            key="form_debt_total",
            help="Total remaining principal across all loans (optional)",
        )

    # Overspending notice
    if monthly_income > 0 and (monthly_expenses + monthly_debt) > monthly_income * 0.95:
        st.info(
            "💡 Your expenses + debt repayments exceed 95% of your income. "
            "Consider reviewing your fixed costs to free up more savings capacity."
        )

    # ── Section 3: Investment Preferences ────────────────────────────────────
    st.markdown("<div class='section-label'>📊 Investment Preferences</div>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        risk_label = st.selectbox(
            "Risk Tolerance *",
            list(RISK_MAP.keys()),
            index=list(RISK_MAP.keys()).index(st.session_state.get("form_risk", "Moderate")),
            key="form_risk",
        )
        _risk_help = {
            "Conservative": "Prioritises capital safety; accepts lower returns.",
            "Moderate": "Balanced approach between growth and security.",
            "Aggressive": "Maximises growth potential; accepts higher volatility.",
        }
        st.caption(_risk_help[risk_label])

    with c2:
        horizon_label = st.selectbox(
            "Investment Horizon *",
            list(HORIZON_MAP.keys()),
            index=list(HORIZON_MAP.keys()).index(st.session_state.get("form_horizon", "Long (>7yr)")),
            key="form_horizon",
        )

    existing_investments = st.multiselect(
        "Existing Investments",
        INVESTMENT_OPTIONS,
        default=st.session_state.get("form_existing_investments", []),
        key="form_existing_investments",
    )

    # ── Section 4: Financial Goals ────────────────────────────────────────────
    st.markdown("<div class='section-label'>🎯 Financial Goals</div>", unsafe_allow_html=True)
    selected_goals = st.multiselect(
        "Select your goals *",
        GOAL_OPTIONS,
        default=st.session_state.get("form_goals", []),
        key="form_goals",
        help="Select at least one financial goal",
    )

    goal_inputs: list[dict] = []
    if selected_goals:
        st.markdown("#### Goal Details")
        for goal in selected_goals:
            with st.expander(f"📌 {goal}", expanded=True):
                gc1, gc2 = st.columns(2)
                amount_key = f"form_goal_amount_{goal}"
                months_key = f"form_goal_months_{goal}"
                with gc1:
                    amount = st.number_input(
                        "Target Amount (INR) *",
                        min_value=1.0,
                        value=float(st.session_state.get(amount_key, 100000.0)),
                        step=10000.0,
                        format="%.0f",
                        key=amount_key,
                    )
                with gc2:
                    months = st.number_input(
                        "Timeline (months) *",
                        min_value=1,
                        max_value=480,
                        value=int(st.session_state.get(months_key, 36)),
                        step=6,
                        key=months_key,
                        help="How many months until you need this amount? (max 480)",
                    )
                goal_inputs.append(
                    {"goal_name": goal, "target_amount": amount, "target_months": months}
                )

    # ── Submit ────────────────────────────────────────────────────────────────
    st.markdown("<div style='margin-top:8px;'></div>", unsafe_allow_html=True)
    st.divider()
    if st.button("🚀 Analyse My Finances", type="primary", use_container_width=True):
        _submit_form(
            name=name,
            age=int(age),
            occupation=occupation,
            monthly_income=monthly_income,
            monthly_expenses=monthly_expenses,
            current_savings=current_savings,
            monthly_debt=monthly_debt,
            total_debt=total_debt,
            risk_label=risk_label,
            horizon_label=horizon_label,
            existing_investments=existing_investments,
            goal_inputs=goal_inputs,
        )


def _submit_form(**kwargs: Any) -> None:
    """Validate form data and update session state with FinancialProfile."""
    name = kwargs["name"]
    goal_inputs = kwargs["goal_inputs"]

    errors: list[str] = []

    # Basic validations
    if not name or len(name.strip()) < 2:
        errors.append("Full Name must be at least 2 characters.")
    if not kwargs["goal_inputs"] and not st.session_state.get("form_goals"):
        errors.append("Please select at least one financial goal.")

    if errors:
        for e in errors:
            st.error(f"❌ {e}")
        return

    try:
        profile = validate_profile(
            {
                "name": sanitise_text(name, 100),
                "age": kwargs["age"],
                "occupation": kwargs["occupation"],
                "monthly_income": kwargs["monthly_income"],
                "monthly_expenses": kwargs["monthly_expenses"],
                "current_savings": kwargs["current_savings"],
                "monthly_debt_repayments": kwargs["monthly_debt"],
                "total_debt_outstanding": kwargs["total_debt"],
                "risk_tolerance": RISK_MAP[kwargs["risk_label"]],
                "investment_horizon": HORIZON_MAP[kwargs["horizon_label"]],
                "financial_goals": goal_inputs,
                "existing_investments": [
                    i for i in kwargs["existing_investments"] if i != "None"
                ],
            }
        )

        # Store in session state and compute next steps
        st.session_state["profile"] = profile
        st.session_state["current_step"] = 2
        st.session_state["metrics"] = None
        st.session_state["goals"] = []
        st.session_state["advice"] = None
        st.session_state["charts"] = {}

        st.success(
            f"✅ Profile saved for **{profile.name}**! Navigate to **Health Analysis** to see your metrics."
        )
        st.balloons()
        # Bug 3 fix: Without st.rerun() the sidebar profile badge doesn't update
        # until the next user interaction.
        st.rerun()

    except ValidationError as exc:
        for err in exc.errors():
            st.error(f"❌ {err['loc'][-1]}: {err['msg']}")
    except Exception as exc:  # noqa: BLE001
        st.error(f"❌ Unexpected error: {exc}")


def validate_profile(raw_data: dict) -> FinancialProfile:
    """
    Validate and structure raw form input into a FinancialProfile model.

    Args:
        raw_data: Dictionary of raw form values.

    Returns:
        Validated FinancialProfile instance.

    Raises:
        pydantic.ValidationError on invalid input.
    """
    goals = [
        GoalInput(
            goal_name=g["goal_name"],
            target_amount=float(g["target_amount"]),
            target_months=int(g["target_months"]),
        )
        for g in raw_data.pop("financial_goals", [])
    ]
    return FinancialProfile(**raw_data, financial_goals=goals)


def _load_sample_data() -> None:
    """Pre-fill session state with Priya's sample profile."""
    sp = SAMPLE_PROFILE
    st.session_state["form_name"] = sp["name"]
    st.session_state["form_age"] = sp["age"]
    st.session_state["form_occupation"] = sp["occupation"]
    st.session_state["form_income"] = sp["monthly_income"]
    st.session_state["form_expenses"] = sp["monthly_expenses"]
    st.session_state["form_debt_monthly"] = sp["monthly_debt_repayments"]
    st.session_state["form_debt_total"] = sp["total_debt_outstanding"]
    st.session_state["form_savings"] = sp["current_savings"]
    st.session_state["form_risk"] = sp["risk_tolerance"]
    st.session_state["form_horizon"] = sp["investment_horizon"]
    st.session_state["form_goals"] = sp["financial_goals"]
    st.session_state["form_existing_investments"] = sp["existing_investments"]
    for goal, details in sp["goal_targets"].items():
        st.session_state[f"form_goal_amount_{goal}"] = details["amount"]
        st.session_state[f"form_goal_months_{goal}"] = details["months"]
    st.rerun()


def _clear_form() -> None:
    """Clear all form-related keys from session state."""
    keys_to_clear = [k for k in st.session_state if k.startswith("form_")]
    for k in keys_to_clear:
        del st.session_state[k]
