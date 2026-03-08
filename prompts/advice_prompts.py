"""Prompt templates for the AI-Powered Advice Engine."""

import json

SYSTEM_PROMPT = """
You are an expert Certified Financial Planner (CFP) with 20+ years of experience
advising individuals across diverse income levels in the Indian financial market.
Your role is to provide personalised, actionable, evidence-based financial advice.

GUIDELINES:
- Always prioritise the user's financial safety and long-term wellbeing.
- Use plain language; explain financial terms when first introduced.
- Reference Indian financial instruments: SIP, PPF, NPS, ELSS, FD, RD, Gold ETF.
- All monetary values in INR unless currency_preference specifies otherwise.
- Never recommend speculative assets (crypto, leveraged products) to conservative users.
- Always include standard financial advice disclaimers.
- Structure response as valid JSON matching the OUTPUT_SCHEMA provided.
- Keep each section concise, specific, and actionable.
"""

USER_DATA_TEMPLATE = """
FINANCIAL PROFILE:
- Name: {name} | Age: {age} | Occupation: {occupation}
- Monthly Income: INR {income:,}
- Monthly Expenses: INR {expenses:,}
- Monthly Debt Repayments: INR {debt_repayments:,}
- Total Outstanding Debt: INR {total_debt:,}
- Current Savings: INR {savings:,}
- Risk Tolerance: {risk_tolerance}
- Investment Horizon: {investment_horizon}

COMPUTED METRICS:
- Net Monthly Surplus: INR {net_surplus:,}
- Savings Rate: {savings_rate:.1f}%
- Expense Ratio: {expense_ratio:.1f}%
- Debt-to-Income Ratio: {dti_ratio:.1f}%
- Emergency Fund Coverage: {ef_coverage:.1f} months
- Financial Health Score: {health_score}/100
- Investable Surplus: INR {investable_surplus:,}

FINANCIAL GOALS:
{goals_section}

EXISTING INVESTMENTS: {existing_investments}
"""

OUTPUT_SCHEMA = {
    "financial_health_summary": "string (150-200 words narrative)",
    "spending_optimisation": [
        "string (specific actionable tip 1)",
        "string (specific actionable tip 2)",
        "string (specific actionable tip 3)",
    ],
    "savings_acceleration": "string (200-250 words step-by-step plan)",
    "debt_management_roadmap": "string (150-250 words avalanche/snowball strategy)",
    "investment_recommendations": {
        "overview": "string (overview of investment strategy)",
        "allocations": [
            {
                "instrument": "string (e.g. Equity SIP)",
                "percentage": 0,
                "rationale": "string",
            }
        ],
    },
    "goal_roadmaps": [
        {
            "goal_name": "string",
            "plan": "string (monthly milestone plan)",
            "milestones": ["string (milestone 1)", "string (milestone 2)"],
        }
    ],
    "action_plan": {
        "days_30": ["string (action 1)", "string (action 2)"],
        "days_60": ["string (action 1)", "string (action 2)"],
        "days_90": ["string (action 1)", "string (action 2)"],
    },
    "risk_warnings": "string (50-100 words)",
    "disclaimer": "string (standard advisory disclaimer)",
}

FALLBACK_ADVICE = {
    "financial_health_summary": (
        "Based on your financial profile, we have analysed your income, expenses, savings, "
        "and debt levels. Your financial health score reflects your current position across "
        "key dimensions including savings rate, debt management, and emergency fund adequacy. "
        "Review each metric below and focus on your most critical areas first."
    ),
    "spending_optimisation": [
        "Track all expenses for 30 days using a budgeting app to identify your top 3 discretionary spend categories.",
        "Apply the 50-30-20 rule: 50% needs, 30% wants, 20% savings and investments.",
        "Review all recurring subscriptions monthly — cancel any unused services immediately.",
        "Plan meals weekly to reduce food delivery expenses, which typically account for 10-15% of urban budgets.",
        "Negotiate better rates on utilities, internet, and insurance annually.",
    ],
    "savings_acceleration": (
        "To reach the 20% savings target, automate your savings on salary day. "
        "Set up standing instructions to transfer a fixed amount to a dedicated savings account "
        "before spending begins. Increase your SIP amount by INR 500 every six months. "
        "Use windfalls (bonuses, tax refunds) to make lump-sum investments rather than spending them."
    ),
    "debt_management_roadmap": (
        "List all debts with their interest rates. Prioritise paying the highest-interest debt first "
        "(Avalanche Method) to minimise total interest paid. Make minimum payments on all other debts. "
        "Once the highest-interest debt is cleared, redirect its payment to the next one. "
        "Avoid new EMIs until existing debt-to-income ratio falls below 15%."
    ),
    "investment_recommendations": {
        "overview": (
            "Build a balanced portfolio aligned with your risk profile and investment horizon. "
            "Start with tax-efficient instruments like ELSS for 80C benefits, then diversify "
            "across equity SIPs for growth and debt instruments for stability."
        ),
        "allocations": [
            {"instrument": "Equity SIP (ELSS/Index Funds)", "percentage": 50, "rationale": "Long-term wealth creation with tax benefits"},
            {"instrument": "PPF", "percentage": 20, "rationale": "Risk-free, tax-exempt returns with government backing"},
            {"instrument": "Debt Mutual Funds", "percentage": 20, "rationale": "Stability and liquidity for medium-term needs"},
            {"instrument": "Gold ETF", "percentage": 10, "rationale": "Inflation hedge and portfolio diversification"},
        ],
    },
    "goal_roadmaps": [
        {
            "goal_name": "Your Primary Goal",
            "plan": "Start investing the required monthly amount immediately. Review progress every quarter and adjust SIP amounts as income grows.",
            "milestones": [
                "Month 3: Establish consistent investment habit",
                "Month 6: Review allocation and rebalance if needed",
                "Month 12: Assess goal progress and increase contributions",
            ],
        }
    ],
    "action_plan": {
        "days_30": [
            "Open a savings account and set up auto-debit for monthly SIP",
            "Create a detailed monthly budget and track every expense",
            "Check credit score and resolve any discrepancies",
        ],
        "days_60": [
            "Start investing in PPF if not already done (max INR 1.5L per year for 80C)",
            "Review and cancel at least 2 unnecessary subscriptions",
            "Increase EMI payments by any available surplus to reduce loan tenure",
        ],
        "days_90": [
            "Review investment performance and rebalance portfolio if allocation drifts",
            "Evaluate health insurance coverage — ensure adequate sum insured",
            "Set up auto-increment for SIP amounts annually",
        ],
    },
    "risk_warnings": (
        "Investments are subject to market risks. Past performance is not a guarantee of future returns. "
        "Equity investments may lose value in the short term. Ensure you have adequate emergency funds "
        "before investing in market-linked instruments."
    ),
    "disclaimer": (
        "This advice is generated by an AI system for educational purposes only and does not constitute "
        "professional financial advice. Consult a SEBI-registered financial advisor before making "
        "significant investment decisions. All calculations use assumed return rates and actual returns may vary."
    ),
}


def build_advice_prompt(profile, metrics, goals: list) -> str:
    """
    Assemble the full prompt for Gemini (large-context cloud model).

    Args:
        profile: FinancialProfile instance.
        metrics: FinancialMetrics instance.
        goals: List of GoalPlan instances.

    Returns:
        Complete prompt string ready for Gemini API.
    """
    goals_section = "\n".join(
        [
            f"- {g.goal_name}: Target INR {g.target_amount:,.0f} in {g.target_months} months "
            f"(Inflation-adjusted: INR {g.inflation_adjusted_target:,.0f}, "
            f"Required monthly: INR {g.required_monthly_saving:,.0f}, "
            f"Status: {g.feasibility_status})"
            for g in goals
        ]
    ) or "None specified"

    user_data = USER_DATA_TEMPLATE.format(
        name=profile.name[:50],
        age=profile.age,
        occupation=profile.occupation,
        income=int(profile.monthly_income),
        expenses=int(profile.monthly_expenses),
        debt_repayments=int(profile.monthly_debt_repayments),
        total_debt=int(profile.total_debt_outstanding),
        savings=int(profile.current_savings),
        risk_tolerance=profile.risk_tolerance.value.title(),
        investment_horizon=profile.investment_horizon.value.title(),
        net_surplus=int(metrics.net_monthly_surplus),
        savings_rate=metrics.savings_rate_pct,
        expense_ratio=metrics.expense_ratio_pct,
        dti_ratio=metrics.dti_ratio_pct,
        ef_coverage=metrics.emergency_fund_months,
        health_score=metrics.financial_health_score,
        investable_surplus=int(metrics.investable_surplus),
        goals_section=goals_section,
        existing_investments=", ".join(profile.existing_investments) or "None",
    )

    schema_str = json.dumps(OUTPUT_SCHEMA, indent=2)
    return (
        f"{SYSTEM_PROMPT}\n\n{user_data}\n\n"
        f"Respond ONLY with valid JSON matching this schema exactly:\n{schema_str}"
    )


# Compact Ollama prompt
# 7B Q4 models (≈4GB RAM) need short prompts to avoid internal timeouts.
# We request only 5 essential keys and keep each value brief.

_OLLAMA_SCHEMA = {
    "financial_health_summary": "2-3 sentence summary of financial health",
    "spending_optimisation": ["tip 1", "tip 2", "tip 3"],
    "savings_acceleration": "1 paragraph step-by-step plan",
    "investment_recommendations": {
        "overview": "1 paragraph investment strategy",
        "allocations": [
            {"instrument": "name", "percentage": 0, "rationale": "brief reason"}
        ],
    },
    "action_plan": {
        "days_30": ["action 1", "action 2"],
        "days_60": ["action 1", "action 2"],
        "days_90": ["action 1", "action 2"],
    },
}


def build_ollama_prompt(profile, metrics, goals: list) -> str:
    """
    Build a COMPACT prompt for local Ollama 7B Q4 models.

    Keeps token count low (~400 tokens total) so inference completes before
    Ollama's internal generation deadline. Only requests 5 JSON keys instead
    of 8. Values are brief (1 paragraph max each).

    Args:
        profile: FinancialProfile instance.
        metrics: FinancialMetrics instance.
        goals: List of GoalPlan instances.

    Returns:
        Compact prompt string suitable for local 7B models.
    """
    goals_brief = ", ".join(
        f"{g.goal_name} (INR {g.target_amount:,.0f} in {g.target_months}mo, {g.feasibility_status})"
        for g in goals
    ) or "None"

    schema_str = json.dumps(_OLLAMA_SCHEMA, indent=2)

    return (
        "You are a financial advisor. Analyse this profile and respond ONLY with valid JSON.\n"
        "Keep responses brief — 1-3 sentences per text field.\n\n"
        f"Profile: {profile.name}, age {profile.age}, {profile.occupation}.\n"
        f"Income: INR {int(profile.monthly_income):,}/mo | Expenses: INR {int(profile.monthly_expenses):,}/mo | "
        f"Debt EMI: INR {int(profile.monthly_debt_repayments):,}/mo | Savings: INR {int(profile.current_savings):,}\n"
        f"Health Score: {metrics.financial_health_score}/100 | Surplus: INR {int(metrics.net_monthly_surplus):,}/mo | "
        f"Savings Rate: {metrics.savings_rate_pct:.1f}% | DTI: {metrics.dti_ratio_pct:.1f}% | "
        f"Emergency Fund: {metrics.emergency_fund_months:.1f} months\n"
        f"Risk: {profile.risk_tolerance.value} | Horizon: {profile.investment_horizon.value}\n"
        f"Goals: {goals_brief}\n\n"
        f"Respond ONLY with valid JSON matching this schema:\n{schema_str}"
    )
