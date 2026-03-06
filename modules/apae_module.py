"""
Module 4: AI-Powered Advice Engine (APAE)
Integrates with Google Gemini 2.0 Flash or a local Ollama model to generate
structured financial advice. Falls back to rule-based advice if all providers
are unavailable.

LLM provider is controlled by the MODEL_PROVIDER environment variable:
  - "gemini"  → calls Google Gemini API (requires GOOGLE_API_KEY)
  - "ollama"  → calls local Ollama REST API (requires Ollama daemon running)
"""

from __future__ import annotations

import json
import os
import re
import traceback

import streamlit as st
from tenacity import retry, stop_after_attempt, wait_exponential

from config.settings import (
    OLLAMA_BASE_URL,
    OLLAMA_MODEL,
    OLLAMA_TIMEOUT,
    MODEL_PROVIDER,
)
from models.financial_metrics import FinancialMetrics
from models.financial_profile import FinancialProfile
from models.goal_plan import GoalPlan
from prompts.advice_prompts import FALLBACK_ADVICE, build_advice_prompt, build_ollama_prompt


# ── Public API ────────────────────────────────────────────────────────────────

def generate_advice(
    profile: FinancialProfile,
    metrics: FinancialMetrics,
    goals: list[GoalPlan],
) -> dict:
    """
    Generate AI-powered financial advice.

    Routes to Gemini or Ollama based on MODEL_PROVIDER env var.
    Falls back to rule-based advice on any provider failure.

    Args:
        profile: Validated FinancialProfile.
        metrics: Computed FinancialMetrics.
        goals:   List of GoalPlan instances.

    Returns:
        Parsed advice dict matching OUTPUT_SCHEMA.
    """
    # Allow runtime override via env var (settings.MODEL_PROVIDER is the default)
    provider = os.getenv("MODEL_PROVIDER", MODEL_PROVIDER).strip().lower()

    try:
        if provider == "ollama":
            # Use the compact prompt designed for local 7B Q4 models
            prompt = build_ollama_prompt(profile, metrics, goals)
            raw = _call_ollama_api(prompt)
        else:
            # Default: Gemini — use the full detailed prompt
            prompt = build_advice_prompt(profile, metrics, goals)
            api_key = os.getenv("GOOGLE_API_KEY", "").strip()
            if not api_key or api_key == "your_gemini_api_key_here":
                st.session_state["api_error"] = True
                st.session_state["api_provider"] = "gemini"
                return _rule_based_advice(profile, metrics, goals)
            raw = _call_gemini_api(prompt, api_key)

        # Fill in any keys missing from the compact Ollama schema
        # using FALLBACK_ADVICE as a safe default
        merged = dict(FALLBACK_ADVICE)
        merged.update(raw)
        st.session_state["api_error"] = False
        st.session_state["api_provider"] = provider
        return merged

    except Exception as exc:  # noqa: BLE001
        st.session_state["api_error"] = True
        st.session_state["api_provider"] = provider
        provider_label = "Ollama" if provider == "ollama" else "Gemini"
        st.warning(
            f"⚠️ {provider_label} API unavailable ({type(exc).__name__}: {exc}). "
            "Showing rule-based advice. Check your connection / config."
        )
        traceback.print_exc()
        return _rule_based_advice(profile, metrics, goals)


# ── Provider: Gemini ─────────────────────────────────────────────────────────

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=8),
    reraise=True,
)
def _call_gemini_api(prompt: str, api_key: str) -> dict:
    """Make the Gemini API call with retry logic."""
    import google.generativeai as genai  # noqa: PLC0415

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(
        model_name="gemini-2.0-flash",
        generation_config={
            "temperature": 0.3,
            "top_p": 0.95,
            "top_k": 40,
            "max_output_tokens": 4096,
        },
    )
    response = model.generate_content(prompt)
    return _parse_llm_output(response.text)


# ── Provider: Ollama ──────────────────────────────────────────────────────────

@retry(
    stop=stop_after_attempt(2),
    wait=wait_exponential(multiplier=1, min=4, max=15),
    reraise=True,
)
def _call_ollama_api(prompt: str) -> dict:
    """
    Call the local Ollama REST API for inference.

    Uses the compact ollama prompt (~400 tokens) to avoid Ollama's internal
    generation timeout. Key settings:
      - num_ctx: 2048   — keeps context window small; prevents OOM/timeout
      - num_predict: 800 — cap output tokens; a 7B model is fast for short output
      - temperature: 0.2 — slightly lower for more deterministic JSON
      - stream: False    — wait for full response

    Requires: `ollama serve` running, model pulled via `ollama pull <model>`.
    """
    import requests  # noqa: PLC0415

    base_url = os.getenv("OLLAMA_BASE_URL", OLLAMA_BASE_URL).rstrip("/")
    model_name = os.getenv("OLLAMA_MODEL", OLLAMA_MODEL)
    timeout = int(os.getenv("OLLAMA_TIMEOUT", OLLAMA_TIMEOUT))

    payload = {
        "model": model_name,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.2,
            "num_predict": 800,   # cap output length — enough for brief JSON
            "num_ctx": 2048,      # small context window prevents Ollama 500s
            "stop": ["```"],      # stop generation if model wraps in code fence
        },
    }

    response = requests.post(
        f"{base_url}/api/generate",
        json=payload,
        timeout=timeout,
    )
    response.raise_for_status()
    response_json = response.json()

    raw_text = response_json.get("response", "").strip()
    if not raw_text:
        raise ValueError(
            f"Ollama returned an empty response. Full payload: {response_json}"
        )

    return _parse_llm_output(raw_text)


# ── Shared utilities ──────────────────────────────────────────────────────────

def _parse_llm_output(raw_text: str) -> dict:
    """
    Parse JSON from the raw LLM output string.
    Strips Markdown code fences (``` / ```json) if present.
    """
    text = raw_text.strip()

    # Strip opening ```json or ``` fence
    if text.startswith("```"):
        lines = text.split("\n")
        text = "\n".join(lines[1:])  # drop first line (``` or ```json)

    # Strip closing ``` fence
    if text.endswith("```"):
        text = text[: text.rfind("```")]

    return json.loads(text.strip())


# ── Fallback: rule-based advice ───────────────────────────────────────────────

def _rule_based_advice(
    profile: FinancialProfile,
    metrics: FinancialMetrics,
    goals: list[GoalPlan],
) -> dict:
    """
    Generate deterministic rule-based fallback advice.
    Used when all LLM providers are unavailable.
    """
    advice = dict(FALLBACK_ADVICE)

    score_label = _score_label(metrics.financial_health_score)
    advice["financial_health_summary"] = (
        f"Hello {profile.name}! Based on your financial profile, your Financial Health Score is "
        f"**{metrics.financial_health_score}/100** ({score_label}). Your monthly income is "
        f"₹{profile.monthly_income:,.0f} with ₹{profile.monthly_expenses:,.0f} in expenses and "
        f"₹{profile.monthly_debt_repayments:,.0f} in debt repayments, leaving you a net surplus of "
        f"₹{metrics.net_monthly_surplus:,.0f}/month. "
        f"Your savings rate is {metrics.savings_rate_pct:.1f}% and your emergency fund covers "
        f"{metrics.emergency_fund_months:.1f} months of expenses. "
        f"{'Prioritise building your emergency fund before investing.' if metrics.ef_status == 'insufficient' else ''}"
        f"{'Focus on debt reduction as a priority given your DTI ratio.' if metrics.dti_ratio_pct > 15 else ''}"
    )

    if goals:
        goal_roadmaps = []
        for g in goals:
            goal_roadmaps.append(
                {
                    "goal_name": g.goal_name,
                    "plan": (
                        f"Invest ₹{g.required_monthly_saving:,.0f}/month for {g.target_months} months "
                        f"at an expected {g.expected_return_rate}% annual return to reach "
                        f"₹{g.inflation_adjusted_target:,.0f} (inflation-adjusted target). "
                        f"Status: {g.feasibility_status.replace('_', ' ').title()}."
                    ),
                    "milestones": [
                        f"Month 3: Start SIP of ₹{g.required_monthly_saving / 2:,.0f} and build up",
                        f"Month 6: Review portfolio and rebalance per allocation plan",
                        f"Month {g.target_months // 2}: Mid-point check — assess progress toward ₹{g.target_amount:,.0f}",
                    ],
                }
            )
        advice["goal_roadmaps"] = goal_roadmaps

    return advice


# ── UI Renderer ───────────────────────────────────────────────────────────────

def render_advice_sections(advice: dict) -> None:
    """
    Render all 8 AI advice sections using Streamlit expanders.

    Args:
        advice: Parsed advice dict from any provider or rule-based fallback.
    """
    # Provider / error banner
    provider = st.session_state.get("api_provider", "gemini")
    if st.session_state.get("api_error"):
        st.info(
            "ℹ️ Showing rule-based advice. "
            + (
                "Add your **GOOGLE_API_KEY** to `.env` for personalised AI insights from Gemini."
                if provider == "gemini"
                else "Ensure **Ollama** is running (`ollama serve`) with the required model pulled."
            )
        )
    else:
        provider_label = "Ollama (local)" if provider == "ollama" else "Gemini 2.0 Flash"
        st.success(f"✅ Advice generated by **{provider_label}**.")

    st.markdown(
        """
        <h2 style='color:#1F3864;margin-bottom:4px;'>🤖 AI Financial Advice</h2>
        <p style='color:#595959;'>Personalised recommendations powered by your selected AI provider.</p>
        """,
        unsafe_allow_html=True,
    )

    # Section 1: Health Summary
    with st.expander("📋 Financial Health Summary", expanded=True):
        st.markdown(advice.get("financial_health_summary", ""))

    # Section 2: Spending Optimisation
    with st.expander("💸 Spending Optimisation Recommendations", expanded=True):
        tips = advice.get("spending_optimisation", [])
        if isinstance(tips, list):
            for i, tip in enumerate(tips, 1):
                st.markdown(f"**{i}.** {tip}")
        else:
            st.markdown(tips)

    # Section 3: Savings Acceleration
    with st.expander("💰 Savings Acceleration Strategy"):
        st.markdown(advice.get("savings_acceleration", ""))

    # Section 4: Debt Management
    with st.expander("🏦 Debt Management Roadmap"):
        st.markdown(advice.get("debt_management_roadmap", ""))

    # Section 5: Investment Recommendations
    with st.expander("📈 Investment Portfolio Recommendations", expanded=True):
        inv = advice.get("investment_recommendations", {})
        if isinstance(inv, dict):
            st.markdown(inv.get("overview", ""))
            allocations = inv.get("allocations", [])
            if allocations:
                import pandas as pd
                df = pd.DataFrame(allocations)
                if "instrument" in df.columns:
                    df.columns = [c.title() for c in df.columns]
                    st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.markdown(str(inv))

    # Section 6: Goal Roadmaps
    with st.expander("🎯 Goal Achievement Roadmaps", expanded=True):
        roadmaps = advice.get("goal_roadmaps", [])
        if isinstance(roadmaps, list):
            for roadmap in roadmaps:
                if isinstance(roadmap, dict):
                    st.markdown(f"#### 🏁 {roadmap.get('goal_name', 'Goal')}")
                    st.markdown(roadmap.get("plan", ""))
                    milestones = roadmap.get("milestones", [])
                    if milestones:
                        st.markdown("**Milestones:**")
                        for m in milestones:
                            st.markdown(f"- ✓ {m}")
                    st.divider()

    # Section 7: 30-60-90 Day Action Plan
    with st.expander("⚡ 30-60-90 Day Action Plan", expanded=True):
        action = advice.get("action_plan", {})
        if isinstance(action, dict):
            c1, c2, c3 = st.columns(3)
            with c1:
                st.markdown("**🗓️ Next 30 Days**")
                for a in action.get("days_30", []):
                    st.markdown(f"☐ {a}")
            with c2:
                st.markdown("**🗓️ Days 31–60**")
                for a in action.get("days_60", []):
                    st.markdown(f"☐ {a}")
            with c3:
                st.markdown("**🗓️ Days 61–90**")
                for a in action.get("days_90", []):
                    st.markdown(f"☐ {a}")

    # Section 8: Risk Warnings & Disclaimer
    with st.expander("⚠️ Risk Warnings & Disclaimer"):
        st.warning(advice.get("risk_warnings", ""))
        st.caption(advice.get("disclaimer", ""))


def _score_label(score: int) -> str:
    if score >= 80:
        return "Excellent"
    elif score >= 60:
        return "Good"
    elif score >= 40:
        return "Needs Work"
    return "Critical"
