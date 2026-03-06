"""
Module 4: AI-Powered Advice Engine (APAE)
Integrates with Google Gemini (via Ollama cloud or direct API) or a local Ollama
model to generate structured financial advice. Falls back gracefully through a
three-tier waterfall to rule-based advice if all providers fail.

Waterfall order (MODEL_PROVIDER=auto):
  Tier 1 → Gemini cloud via Ollama  (gemini-3-flash-preview:cloud)
  Tier 2 → Google Gemini REST API   (requires GOOGLE_API_KEY)
  Tier 3 → Local Ollama model       (e.g. qwen2.5-7B-Q4)
  Final  → Deterministic rule-based advice

MODEL_PROVIDER env var values:
  "auto"          — full waterfall (default)
  "gemini_ollama" — Tier 1 only, then rule-based
  "gemini"        — Tier 2 only, then rule-based
  "ollama"        — Tier 3 only, then rule-based
"""

from __future__ import annotations

import json
import logging
import os
import re
import traceback
from typing import Any

import streamlit as st
from tenacity import retry, stop_after_attempt, wait_exponential

from config.settings import (
    OLLAMA_BASE_URL,
    OLLAMA_GEMINI_MODEL,
    OLLAMA_GEMINI_TIMEOUT,
    OLLAMA_MODEL,
    OLLAMA_TIMEOUT,
    MODEL_PROVIDER,
)
from models.financial_metrics import FinancialMetrics
from models.financial_profile import FinancialProfile
from models.goal_plan import GoalPlan
from prompts.advice_prompts import FALLBACK_ADVICE, build_advice_prompt, build_ollama_prompt

logger = logging.getLogger(__name__)


# ── Public API ─────────────────────────────────────────────────────────────────

def generate_advice(
    profile: FinancialProfile,
    metrics: FinancialMetrics,
    goals: list[GoalPlan],
) -> dict:
    """
    Generate AI-powered financial advice using the configured provider waterfall.

    Tier 1: Gemini cloud via Ollama  (gemini-3-flash-preview:cloud)
    Tier 2: Google Gemini REST API
    Tier 3: Local Ollama model
    Final:  Deterministic rule-based advice

    Args:
        profile: Validated FinancialProfile.
        metrics: Computed FinancialMetrics.
        goals:   List of GoalPlan instances.

    Returns:
        Parsed advice dict matching OUTPUT_SCHEMA.
    """
    provider = os.getenv("MODEL_PROVIDER", MODEL_PROVIDER).strip().lower()
    full_prompt = build_advice_prompt(profile, metrics, goals)
    compact_prompt = build_ollama_prompt(profile, metrics, goals)

    tiers: list[tuple[str, callable]] = []

    if provider in ("auto", "gemini_ollama"):
        tiers.append(("Gemini Cloud (Ollama)", lambda: _call_gemini_cloud_via_ollama(full_prompt)))

    if provider in ("auto", "gemini"):
        api_key = os.getenv("GOOGLE_API_KEY", "").strip()
        if api_key and api_key != "your_gemini_api_key_here":
            tiers.append(("Gemini API", lambda k=api_key: _call_gemini_api(full_prompt, k)))

    if provider in ("auto", "ollama"):
        tiers.append(("Ollama Local", lambda: _call_ollama_api(compact_prompt)))

    errors: list[str] = []
    for tier_label, tier_fn in tiers:
        try:
            raw = tier_fn()
            merged = dict(FALLBACK_ADVICE)
            merged.update(raw)
            st.session_state["api_error"] = False
            st.session_state["api_provider"] = tier_label
            st.session_state["api_error_msgs"] = []
            return merged
        except Exception as exc:  # noqa: BLE001
            msg = f"{tier_label}: {type(exc).__name__}: {exc}"
            errors.append(msg)
            logger.warning("Provider failed — %s", msg)

    # All tiers failed — use rule-based fallback
    st.session_state["api_error"] = True
    st.session_state["api_provider"] = provider
    st.session_state["api_error_msgs"] = errors
    return _rule_based_advice(profile, metrics, goals)


# ── Tier 1: Gemini Cloud via Ollama ───────────────────────────────────────────

def _call_gemini_cloud_via_ollama(prompt: str) -> dict:
    """
    Call Gemini cloud model routed through Ollama's /api/chat endpoint.

    Requires:
      - Ollama running: `ollama serve`
      - Model pulled:  `ollama pull gemini-3-flash-preview:cloud`
    """
    import requests  # noqa: PLC0415

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

    try:
        response = requests.post(
            f"{base_url}/api/chat",
            json=payload,
            headers=headers,
            timeout=timeout,
        )
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        if hasattr(e.response, "status_code") and e.response.status_code == 401:
            raise ValueError("Ollama Tier 1: 401 Unauthorized. Check your OLLAMA_API_KEY.") from e
        if hasattr(e.response, "status_code") and e.response.status_code == 404:
            raise ValueError(f"Ollama Tier 1: 404 Model '{model_name}' not found. Did you run 'ollama pull {model_name}'?") from e
        raise

    response_json = response.json()
    raw_text = (
        response_json.get("message", {}).get("content", "")
        or response_json.get("response", "")
    ).strip()

    if not raw_text:
        raise ValueError(
            f"Gemini cloud via Ollama returned an empty response. Full payload: {response_json}"
        )

    return _parse_llm_output(raw_text)


# ── Tier 2: Gemini REST API ────────────────────────────────────────────────────

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=8),
    reraise=True,
)
def _call_gemini_api(prompt: str, api_key: str) -> dict:
    """Call the Google Gemini REST API with retry logic."""
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


# ── Tier 3: Local Ollama ───────────────────────────────────────────────────────

@retry(
    stop=stop_after_attempt(2),
    wait=wait_exponential(multiplier=1, min=4, max=15),
    reraise=True,
)
def _call_ollama_api(prompt: str) -> dict:
    """Call the local Ollama REST API for inference."""
    import requests  # noqa: PLC0415

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
            "temperature": 0.2,
            "num_predict": 800,
            "num_ctx": 2048,
            "stop": ["```"],
        },
    }

    response = requests.post(
        f"{base_url}/api/generate",
        json=payload,
        headers=headers,
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


# ── Shared utilities ───────────────────────────────────────────────────────────

def _parse_llm_output(raw_text: str) -> dict:
    """Parse JSON from the raw LLM output string. Strips Markdown code fences if present."""
    text = raw_text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        text = "\n".join(lines[1:])
    if text.endswith("```"):
        text = text[: text.rfind("```")]
    return json.loads(text.strip())


# ── Fallback: rule-based advice ────────────────────────────────────────────────

def _rule_based_advice(
    profile: FinancialProfile,
    metrics: FinancialMetrics,
    goals: list[GoalPlan],
) -> dict:
    """Generate deterministic rule-based fallback advice."""
    advice: dict[str, Any] = dict(FALLBACK_ADVICE)

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


# ── UI Renderer ────────────────────────────────────────────────────────────────

def render_advice_sections(advice: dict) -> None:
    """
    Render all 8 AI advice sections using Streamlit expanders.

    Args:
        advice: Parsed advice dict from any provider or rule-based fallback.
    """
    provider = st.session_state.get("api_provider", "")
    has_error = st.session_state.get("api_error", False)
    error_msgs = st.session_state.get("api_error_msgs", [])

    # ── Page header ──────────────────────────────────────────────────────────
    st.markdown(
        """
        <div class="page-header">
            <div class="page-header-icon">🤖</div>
            <div>
                <div class="page-header-title">AI Financial Advice</div>
                <div class="page-header-sub">Personalised recommendations powered by your selected AI provider.</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ── Provider status banner ───────────────────────────────────────────────
    if has_error:
        detail = ""
        if error_msgs:
            detail = " | ".join(error_msgs[:2])
        st.info(
            f"ℹ️ Showing rule-based advice (all AI providers unavailable). "
            + (f"Details: {detail}" if detail else "")
        )
    else:
        tier_icons = {
            "Gemini Cloud (Ollama)": "☁️",
            "Gemini API": "✨",
            "Ollama Local": "🖥️",
        }
        icon = tier_icons.get(provider, "🤖")
        st.success(f"✅ Advice generated by {icon} **{provider}**.")

    st.markdown("<div style='margin-top:8px;'></div>", unsafe_allow_html=True)

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
                st.markdown(
                    """<div class="action-mini-card"><h4>🗓️ Next 30 Days</h4>""",
                    unsafe_allow_html=True,
                )
                for a in action.get("days_30", []):
                    st.markdown(f"☐ {a}")
                st.markdown("</div>", unsafe_allow_html=True)

            with c2:
                st.markdown(
                    """<div class="action-mini-card"><h4>🗓️ Days 31–60</h4>""",
                    unsafe_allow_html=True,
                )
                for a in action.get("days_60", []):
                    st.markdown(f"☐ {a}")
                st.markdown("</div>", unsafe_allow_html=True)

            with c3:
                st.markdown(
                    """<div class="action-mini-card"><h4>🗓️ Days 61–90</h4>""",
                    unsafe_allow_html=True,
                )
                for a in action.get("days_90", []):
                    st.markdown(f"☐ {a}")
                st.markdown("</div>", unsafe_allow_html=True)

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
