from __future__ import annotations

import logging
import os
from typing import TYPE_CHECKING, Callable

from config.settings import (
    OLLAMA_BASE_URL,
    OLLAMA_GEMINI_MODEL,
    OLLAMA_GEMINI_TIMEOUT,
    OLLAMA_MODEL,
    OLLAMA_TIMEOUT,
    MODEL_PROVIDER,
)

if TYPE_CHECKING:
    from models.financial_metrics import FinancialMetrics
    from models.financial_profile import FinancialProfile

logger = logging.getLogger(__name__)

_SYSTEM_INSTRUCTION = (
    "You are an expert Certified Financial Planner (CFP) specialising in the Indian financial market. "
    "Answer the user's question using the financial profile provided. "
    "Be concise, specific, and actionable. Use plain language. "
    "Reference Indian instruments (SIP, PPF, NPS, ELSS, FD) where relevant. "
    "All monetary values in INR unless stated otherwise. "
    "End with a one-sentence disclaimer that this is educational and not professional advice."
)


def _build_context(profile: "FinancialProfile", metrics: "FinancialMetrics") -> str:
    if profile.financial_goals:
        goals_text = "Financial Goals:\n" + "\n".join(
            f"  - {g.goal_name}: INR {g.target_amount:,.0f} in {g.target_months} months"
            for g in profile.financial_goals
        )
    else:
        goals_text = "Financial Goals: None specified"

    return (
        f"USER FINANCIAL PROFILE:\n"
        f"  Name: {profile.name} | Age: {profile.age} | Occupation: {profile.occupation}\n"
        f"  Monthly Income:    INR {profile.monthly_income:,.0f}\n"
        f"  Monthly Expenses:  INR {profile.monthly_expenses:,.0f}\n"
        f"  Debt Repayments:   INR {profile.monthly_debt_repayments:,.0f}/mo\n"
        f"  Outstanding Debt:  INR {profile.total_debt_outstanding:,.0f}\n"
        f"  Current Savings:   INR {profile.current_savings:,.0f}\n"
        f"  Risk Tolerance:    {profile.risk_tolerance.value.title()}\n"
        f"  Investment Horizon: {profile.investment_horizon.value.title()}\n"
        f"  Existing Investments: {', '.join(profile.existing_investments) or 'None'}\n"
        f"\nCOMPUTED METRICS:\n"
        f"  Net Monthly Surplus:    INR {metrics.net_monthly_surplus:,.0f}\n"
        f"  Savings Rate:           {metrics.savings_rate_pct:.1f}%\n"
        f"  Expense Ratio:          {metrics.expense_ratio_pct:.1f}%\n"
        f"  Debt-to-Income Ratio:   {metrics.dti_ratio_pct:.1f}%\n"
        f"  Emergency Fund:         {metrics.emergency_fund_months:.1f} months\n"
        f"  Financial Health Score: {metrics.financial_health_score}/100 "
        f"({metrics.overall_status.replace('_', ' ').title()})\n"
        f"  Investable Surplus:     INR {metrics.investable_surplus:,.0f}\n"
        f"\n{goals_text}"
    )


def _build_prompt(question: str, profile: "FinancialProfile", metrics: "FinancialMetrics") -> str:
    context = _build_context(profile, metrics)
    return (
        f"{_SYSTEM_INSTRUCTION}\n\n"
        f"{context}\n\n"
        f"USER QUESTION: {question}\n\n"
        f"Provide a clear, helpful answer (2-5 paragraphs) based on the profile above."
    )


def _build_ollama_prompt(question: str, profile: "FinancialProfile", metrics: "FinancialMetrics") -> str:
    return (
        "You are a financial advisor. Answer this question briefly (2-3 paragraphs) "
        "using the user's financial data. End with a short disclaimer.\n\n"
        f"Profile: {profile.name}, age {profile.age}, {profile.occupation}. "
        f"Income: INR {profile.monthly_income:,.0f}/mo | "
        f"Expenses: INR {profile.monthly_expenses:,.0f}/mo | "
        f"Surplus: INR {metrics.net_monthly_surplus:,.0f}/mo | "
        f"Savings: INR {profile.current_savings:,.0f} | "
        f"Debt EMI: INR {profile.monthly_debt_repayments:,.0f}/mo | "
        f"Health Score: {metrics.financial_health_score}/100 | "
        f"Risk: {profile.risk_tolerance.value} | "
        f"Horizon: {profile.investment_horizon.value}\n\n"
        f"Question: {question}"
    )


def _gemini_cloud_via_ollama(prompt: str) -> str:
    import requests

    base_url = os.getenv("OLLAMA_BASE_URL", OLLAMA_BASE_URL).rstrip("/")
    model_name = os.getenv("OLLAMA_GEMINI_MODEL", OLLAMA_GEMINI_MODEL)
    timeout = int(os.getenv("OLLAMA_GEMINI_TIMEOUT", OLLAMA_GEMINI_TIMEOUT))
    api_key = os.getenv("OLLAMA_API_KEY", "").strip()

    headers = {}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    payload = {
        "model": model_name,
        "messages": [{"role": "user", "content": prompt}],
        "stream": False,
    }

    response = requests.post(
        f"{base_url}/api/chat",
        json=payload,
        headers=headers,
        timeout=timeout,
    )
    response.raise_for_status()
    data = response.json()
    text = (
        data.get("message", {}).get("content", "")
        or data.get("response", "")
    ).strip()

    if not text:
        raise ValueError("Gemini cloud via Ollama returned an empty response.")
    return text


def _gemini_api(prompt: str, api_key: str) -> str:
    import google.generativeai as genai

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(
        model_name="gemini-2.0-flash",
        generation_config={
            "temperature": 0.5,
            "top_p": 0.95,
            "top_k": 40,
            "max_output_tokens": 1024,
        },
    )
    response = model.generate_content(prompt)
    return response.text.strip()


def _ollama_local(prompt: str) -> str:
    import requests

    base_url = os.getenv("OLLAMA_BASE_URL", OLLAMA_BASE_URL).rstrip("/")
    model_name = os.getenv("OLLAMA_MODEL", OLLAMA_MODEL)
    timeout = int(os.getenv("OLLAMA_TIMEOUT", OLLAMA_TIMEOUT))
    api_key = os.getenv("OLLAMA_API_KEY", "").strip()

    headers = {}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    payload = {
        "model": model_name,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.4,
            "num_predict": 600,
            "num_ctx": 2048,
        },
    }

    response = requests.post(
        f"{base_url}/api/generate",
        json=payload,
        headers=headers,
        timeout=timeout,
    )
    response.raise_for_status()
    text = response.json().get("response", "").strip()
    if not text:
        raise ValueError("Ollama returned an empty response.")
    return text


def _rule_based_response(question: str, profile: "FinancialProfile", metrics: "FinancialMetrics") -> str:
    q = question.lower()

    if any(w in q for w in ("debt", "loan", "emi", "repay")):
        return (
            f"**Debt Reduction Strategy for {profile.name}**\n\n"
            f"Your current debt-to-income ratio is **{metrics.dti_ratio_pct:.1f}%** "
            f"with monthly repayments of INR {profile.monthly_debt_repayments:,.0f}. "
            "Use the **Avalanche Method**: list all debts by interest rate (highest first) and direct "
            "every extra rupee of surplus toward the top-rate debt while paying minimums on others. "
            f"With a monthly surplus of INR {metrics.net_monthly_surplus:,.0f}, you could potentially "
            f"clear your outstanding balance in approximately {metrics.debt_payoff_months or 'N/A'} months "
            "at the current pace.\n\n"
            "*This is educational information only — not professional financial advice.*"
        )

    if any(w in q for w in ("invest", "sip", "mutual fund", "stock", "portfolio", "ppf", "elss")):
        return (
            f"**Investment Guidance for {profile.name}**\n\n"
            f"With a **{profile.risk_tolerance.value}** risk tolerance and a "
            f"**{profile.investment_horizon.value}-term** horizon, a starting allocation could be: "
            "50% Equity SIP (index funds/ELSS for 80C benefit), 20% PPF, 20% Debt Mutual Funds, "
            "10% Gold ETF. Start with your investable surplus of "
            f"INR {metrics.investable_surplus:,.0f}/month. Review and rebalance every 6 months.\n\n"
            "*This is educational information only — not professional financial advice.*"
        )

    if any(w in q for w in ("save", "saving", "savings rate", "emergency")):
        return (
            f"**Savings Strategy for {profile.name}**\n\n"
            f"Your current savings rate is **{metrics.savings_rate_pct:.1f}%** "
            f"and your emergency fund covers **{metrics.emergency_fund_months:.1f} months** of expenses "
            f"(target: 6 months = INR {profile.monthly_expenses * 6:,.0f}). "
            "Automate savings on salary day via standing instructions. "
            "Increase SIP amounts by INR 500 every 6 months. "
            "Use windfalls (bonuses, tax refunds) to top up your emergency fund first.\n\n"
            "*This is educational information only — not professional financial advice.*"
        )

    if any(w in q for w in ("budget", "expense", "spend", "cut")):
        return (
            f"**Budgeting Tips for {profile.name}**\n\n"
            f"Your expense ratio is **{metrics.expense_ratio_pct:.1f}%** of income. "
            "Apply the 50-30-20 rule: 50% on needs, 30% on wants, 20% on savings and investments. "
            "Track all expenses for 30 days to identify your top 3 discretionary categories. "
            "Review and cancel unused subscriptions monthly — this can free up INR 500–2,000/month.\n\n"
            "*This is educational information only — not professional financial advice.*"
        )

    return (
        f"**Financial Overview for {profile.name}**\n\n"
        f"Your Financial Health Score is **{metrics.financial_health_score}/100** "
        f"({metrics.overall_status.replace('_', ' ').title()}). "
        f"With monthly income of INR {profile.monthly_income:,.0f} and expenses of "
        f"INR {profile.monthly_expenses:,.0f}, your net surplus is "
        f"INR {metrics.net_monthly_surplus:,.0f}/month. "
        "Focus on building an emergency fund (6 months of expenses), reducing high-interest debt, "
        "and then investing your surplus systematically via SIP.\n\n"
        "For specific advice on your question, please ensure your AI provider (Gemini or Ollama) "
        "is configured and available.\n\n"
        "*This is educational information only — not professional financial advice.*"
    )


def ask_financial_advisor(
    question: str,
    profile: "FinancialProfile",
    metrics: "FinancialMetrics",
) -> tuple[str, str]:
    """Returns (answer, provider_label)."""
    provider = os.getenv("MODEL_PROVIDER", MODEL_PROVIDER).strip().lower()
    full_prompt = _build_prompt(question, profile, metrics)
    compact_prompt = _build_ollama_prompt(question, profile, metrics)

    tiers: list[tuple[str, Callable[[], str]]] = []

    if provider in ("auto", "gemini_ollama"):
        tiers.append(("Gemini Cloud (Ollama)", lambda: _gemini_cloud_via_ollama(full_prompt)))

    if provider in ("auto", "gemini"):
        api_key = os.getenv("GOOGLE_API_KEY", "").strip()
        if api_key and api_key != "your_gemini_api_key_here":
            tiers.append(("Gemini API", lambda k=api_key: _gemini_api(full_prompt, k)))

    if provider in ("auto", "ollama"):
        tiers.append(("Ollama Local", lambda: _ollama_local(compact_prompt)))

    for label, fn in tiers:
        try:
            return fn(), label
        except Exception as exc:  # noqa: BLE001
            logger.warning("Chat provider failed — %s: %s", label, exc)

    return _rule_based_response(question, profile, metrics), "Rule-based"
