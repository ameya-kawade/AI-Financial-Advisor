from __future__ import annotations

import os
from datetime import datetime

import streamlit as st
from dotenv import load_dotenv


load_dotenv()

from config.settings import APP_FOOTER, APP_ICON, APP_TITLE
from modules.apae_module import generate_advice, render_advice_sections
from modules.chat_module import ask_financial_advisor
from modules.dvd_module import generate_charts, render_dashboard
from modules.fhae_module import compute_metrics, render_metrics_dashboard
from modules.fpi_module import render_profile_form
from modules.gbipe_module import analyse_goals, render_goal_cards
from modules.ree_module import generate_report


PRIMARY        = "#0EA5E9"   # Sky blue — vivid, modern
PRIMARY_DARK   = "#0284C7"
SECONDARY      = "#8B5CF6"   # Violet accent
ACCENT         = "#10B981"   # Emerald green
ACCENT2        = "#F59E0B"   # Amber
BG             = "#060B18"   # Deep navy-black
BG2            = "#0D1526"   # Card background
BG3            = "#111E33"   # Elevated card
BORDER         = "#1E2E47"   # Subtle border
BORDER_BRIGHT  = "#2A3F5F"   # Brighter border for hover
TEXT_PRIMARY   = "#F0F6FF"   # Near-white
TEXT_SECONDARY = "#7A9CC0"   # Muted blue-grey
TEXT_MUTED     = "#415E80"   # Very muted
GLOW_BLUE      = "rgba(14,165,233,0.18)"
GLOW_VIOLET    = "rgba(139,92,246,0.15)"
GLOW_GREEN     = "rgba(16,185,129,0.15)"


CUSTOM_CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,300;0,9..40,400;0,9..40,500;0,9..40,600;0,9..40,700;0,9..40,800;1,9..40,400&family=DM+Mono:wght@400;500&display=swap');

html, body, [class*="css"] {{
    font-family: 'DM Sans', sans-serif !important;
    background-color: {BG} !important;
    color: {TEXT_PRIMARY} !important;
}}
::-webkit-scrollbar {{ width: 5px; height: 5px; }}
::-webkit-scrollbar-track {{ background: {BG2}; }}
::-webkit-scrollbar-thumb {{ background: {BORDER_BRIGHT}; border-radius: 4px; }}

.main .block-container {{
    padding-top: 1.5rem;
    padding-bottom: 3rem;
    max-width: 1240px;
    background: {BG} !important;
}}
p, span, div, label, li {{ color: {TEXT_PRIMARY}; }}

[data-testid="stSidebar"] {{
    background: {BG2} !important;
    border-right: 1px solid {BORDER} !important;
}}
[data-testid="stSidebar"] * {{ color: {TEXT_PRIMARY} !important; }}
[data-testid="stSidebar"] .stRadio label {{
    border-radius: 10px;
    padding: 10px 14px;
    margin: 2px 0;
    transition: all 0.2s ease;
    display: block;
    cursor: pointer;
    font-size: 13.5px;
    font-weight: 500;
    color: {TEXT_SECONDARY} !important;
    border: 1px solid transparent;
}}
[data-testid="stSidebar"] .stRadio label:hover {{
    background: {BG3} !important;
    color: {PRIMARY} !important;
    border-color: {BORDER} !important;
}}
[data-testid="stSidebar"] .stRadio [data-testid="stMarkdownContainer"] p {{ margin: 0; }}

.page-header {{
    background: linear-gradient(135deg, {BG3} 0%, {BG2} 100%);
    border: 1px solid {BORDER};
    border-radius: 20px;
    padding: 28px 32px;
    margin-bottom: 32px;
    display: flex;
    align-items: center;
    gap: 20px;
    position: relative;
    overflow: hidden;
}}
.page-header::before {{
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0; height: 1px;
    background: linear-gradient(90deg, transparent, {PRIMARY}60, transparent);
}}
.page-header::after {{
    content: '';
    position: absolute;
    top: -60px; right: -60px;
    width: 200px; height: 200px;
    background: radial-gradient(circle, {GLOW_BLUE} 0%, transparent 70%);
    pointer-events: none;
}}
.page-header-icon {{ font-size: 38px; line-height: 1; filter: drop-shadow(0 0 12px {GLOW_BLUE}); }}
.page-header-title {{
    font-size: 1.6rem; font-weight: 800; color: {TEXT_PRIMARY};
    margin: 0; line-height: 1.2; letter-spacing: -0.02em;
}}
.page-header-sub {{ font-size: 13px; color: {TEXT_SECONDARY}; margin: 5px 0 0; font-weight: 400; }}

.kpi-card {{
    background: {BG3};
    border: 1px solid {BORDER};
    border-radius: 16px;
    padding: 22px 20px;
    position: relative;
    overflow: hidden;
    transition: all 0.25s ease;
    min-height: 106px;
}}
.kpi-card::before {{
    content: '';
    position: absolute;
    bottom: 0; left: 0; right: 0; height: 3px;
    background: var(--kpi-accent, {PRIMARY});
    border-radius: 0 0 16px 16px;
}}
.kpi-card:hover {{
    border-color: {BORDER_BRIGHT};
    transform: translateY(-2px);
    box-shadow: 0 8px 32px rgba(0,0,0,0.3);
}}
.kpi-value {{
    font-size: 1.75rem; font-weight: 800; color: {TEXT_PRIMARY};
    line-height: 1.1; margin-bottom: 5px;
    font-variant-numeric: tabular-nums; letter-spacing: -0.02em;
}}
.kpi-label {{
    font-size: 10.5px; font-weight: 600; color: {TEXT_MUTED};
    text-transform: uppercase; letter-spacing: 0.1em; margin-bottom: 4px;
}}
.kpi-sub {{ font-size: 12px; color: {TEXT_SECONDARY}; }}

.feature-card {{
    background: {BG3};
    border: 1px solid {BORDER};
    border-radius: 20px;
    padding: 32px 24px;
    text-align: center;
    transition: all 0.3s ease;
    height: 200px;
    position: relative;
    overflow: hidden;
}}
.feature-card::before {{
    content: '';
    position: absolute;
    top: 0; left: 50%; transform: translateX(-50%);
    width: 80%; height: 1px;
    background: linear-gradient(90deg, transparent, var(--fc-accent, {PRIMARY})80, transparent);
}}
.feature-card:hover {{
    transform: translateY(-4px);
    border-color: {BORDER_BRIGHT};
    box-shadow: 0 16px 48px rgba(0,0,0,0.4);
}}

.section-label {{
    font-size: 11px; font-weight: 700; color: {TEXT_MUTED};
    text-transform: uppercase; letter-spacing: 0.1em;
    margin: 28px 0 12px;
    display: flex; align-items: center; gap: 10px;
}}
.section-label::after {{
    content: ''; flex: 1; height: 1px;
    background: linear-gradient(90deg, {BORDER}, transparent);
}}

.form-card {{
    background: {BG3}; border: 1px solid {BORDER};
    border-radius: 14px; padding: 22px 20px; margin-bottom: 18px;
}}

.goal-card {{
    background: {BG3}; border: 1px solid {BORDER};
    border-radius: 18px; padding: 24px 22px; margin-bottom: 20px;
    transition: all 0.25s ease; position: relative; overflow: hidden;
}}
.goal-card:hover {{
    border-color: {BORDER_BRIGHT};
    box-shadow: 0 12px 40px rgba(0,0,0,0.35);
}}

.advice-card {{
    background: {BG3}; border: 1px solid {BORDER};
    border-radius: 14px; padding: 22px; margin-bottom: 16px;
}}

.action-mini-card {{
    background: {BG2}; border: 1px solid {BORDER};
    border-radius: 12px; padding: 16px; height: 100%;
}}
.action-mini-card h4 {{
    color: {PRIMARY}; margin: 0 0 10px;
    font-size: 12px; font-weight: 700;
    text-transform: uppercase; letter-spacing: 0.08em;
}}

.badge-excellent {{ background: rgba(16,185,129,0.15); color: #34D399; padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: 700; border: 1px solid rgba(16,185,129,0.3); letter-spacing: 0.04em; }}
.badge-good      {{ background: rgba(14,165,233,0.15); color: #38BDF8; padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: 700; border: 1px solid rgba(14,165,233,0.3); letter-spacing: 0.04em; }}
.badge-warning   {{ background: rgba(245,158,11,0.15); color: #FCD34D; padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: 700; border: 1px solid rgba(245,158,11,0.3); letter-spacing: 0.04em; }}
.badge-critical  {{ background: rgba(239,68,68,0.15);  color: #F87171; padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: 700; border: 1px solid rgba(239,68,68,0.3); letter-spacing: 0.04em; }}

.stButton > button[kind="primary"] {{
    background: linear-gradient(135deg, {PRIMARY}, {PRIMARY_DARK}) !important;
    color: white !important; border: none !important;
    border-radius: 10px !important; font-weight: 700 !important;
    padding: 0.55rem 1.4rem !important; font-size: 14px !important;
    font-family: 'DM Sans', sans-serif !important;
    transition: all 0.2s ease !important;
    box-shadow: 0 4px 14px rgba(14,165,233,0.35) !important;
}}
.stButton > button[kind="primary"]:hover {{
    transform: translateY(-1px) !important;
    box-shadow: 0 6px 20px rgba(14,165,233,0.5) !important;
}}
.stButton > button:not([kind="primary"]) {{
    border-radius: 10px !important; font-weight: 600 !important;
    font-size: 13.5px !important; font-family: 'DM Sans', sans-serif !important;
    border: 1px solid {BORDER_BRIGHT} !important;
    background: {BG3} !important; color: {TEXT_SECONDARY} !important;
    transition: all 0.2s ease !important;
}}
.stButton > button:not([kind="primary"]):hover {{
    background: {BG3} !important; border-color: {PRIMARY}80 !important;
    color: {PRIMARY} !important;
}}

.stProgress > div > div > div {{
    background: linear-gradient(90deg, {PRIMARY}, {SECONDARY}) !important;
    border-radius: 6px !important;
}}
.stProgress > div > div {{
    background: {BORDER} !important; border-radius: 6px !important;
}}

.stTabs [data-baseweb="tab-list"] {{
    gap: 4px; background: {BG2}; border-radius: 12px;
    padding: 5px; border: 1px solid {BORDER};
}}
.stTabs [data-baseweb="tab"] {{
    border-radius: 9px; font-weight: 600; font-size: 13px;
    color: {TEXT_SECONDARY}; font-family: 'DM Sans', sans-serif; padding: 8px 16px;
}}
.stTabs [aria-selected="true"] {{
    background: linear-gradient(135deg, {PRIMARY}22, {SECONDARY}22) !important;
    color: {PRIMARY} !important; border: 1px solid {PRIMARY}50 !important;
}}

.streamlit-expanderHeader {{
    font-weight: 600 !important; color: {TEXT_PRIMARY} !important;
    font-size: 14px !important; border-radius: 10px !important;
    background: {BG3} !important;
}}
[data-testid="stExpander"] {{
    border: 1px solid {BORDER} !important; border-radius: 12px !important;
    margin-bottom: 10px !important; overflow: hidden !important;
    background: {BG3} !important;
}}
[data-testid="stExpander"] > div:last-child {{ background: {BG2} !important; }}

.stNumberInput > div > div > input,
.stTextInput > div > div > input {{
    border-radius: 10px !important; border: 1px solid {BORDER_BRIGHT} !important;
    font-size: 14px !important; font-family: 'DM Sans', sans-serif !important;
    color: {TEXT_PRIMARY} !important; background: {BG2} !important;
    transition: border-color 0.2s !important;
}}
.stNumberInput > div > div > input:focus,
.stTextInput > div > div > input:focus {{
    border-color: {PRIMARY} !important;
    box-shadow: 0 0 0 3px {PRIMARY}20 !important;
}}
.stSelectbox > div > div,
.stMultiSelect > div > div {{
    border-radius: 10px !important; border-color: {BORDER_BRIGHT} !important;
    background: {BG2} !important;
}}
label[data-baseweb="label"],
.stTextInput label, .stNumberInput label, .stSelectbox label,
.stMultiSelect label, .stSlider label {{
    color: {TEXT_SECONDARY} !important; font-size: 13px !important;
    font-weight: 600 !important; letter-spacing: 0.03em !important;
}}

[data-testid="stMetric"] {{
    background: {BG3}; border: 1px solid {BORDER};
    border-radius: 12px; padding: 14px 16px;
}}
[data-testid="stMetricValue"] {{
    color: {TEXT_PRIMARY} !important; font-family: 'DM Mono', monospace !important;
}}
[data-testid="stMetricLabel"] {{ color: {TEXT_SECONDARY} !important; }}

[data-testid="stDataFrame"] {{
    border-radius: 12px; overflow: hidden;
    border: 1px solid {BORDER}; background: {BG3};
}}

.stAlert {{ border-radius: 12px !important; border: none !important; }}

.sidebar-brand {{
    display: flex; align-items: center; gap: 14px;
    padding: 16px 4px 20px; border-bottom: 1px solid {BORDER}; margin-bottom: 20px;
}}
.sidebar-brand-icon {{
    width: 42px; height: 42px; border-radius: 12px;
    background: linear-gradient(135deg, {PRIMARY}30, {SECONDARY}30);
    border: 1px solid {PRIMARY}40;
    display: flex; align-items: center; justify-content: center;
    font-size: 22px; box-shadow: 0 0 20px {GLOW_BLUE};
}}
.sidebar-brand-name {{
    font-size: 15px; font-weight: 800; color: {TEXT_PRIMARY};
    line-height: 1.2; letter-spacing: -0.01em;
}}
.sidebar-brand-version {{ font-size: 10.5px; color: {TEXT_MUTED}; font-weight: 500; margin-top: 1px; }}

.profile-badge {{
    background: linear-gradient(135deg, {BG3}, {BG2});
    border: 1px solid {BORDER}; border-radius: 12px;
    padding: 12px 14px; margin-bottom: 14px;
    position: relative; overflow: hidden;
}}
.profile-badge::before {{
    content: ''; position: absolute; top: 0; left: 0; right: 0; height: 1px;
    background: linear-gradient(90deg, {PRIMARY}60, {SECONDARY}60);
}}
.profile-badge-label {{
    font-size: 9.5px; font-weight: 700; color: {PRIMARY};
    text-transform: uppercase; letter-spacing: 0.1em; margin-bottom: 3px;
}}
.profile-badge-name {{ font-size: 14px; font-weight: 700; color: {TEXT_PRIMARY}; letter-spacing: -0.01em; }}
.profile-badge-sub {{ font-size: 11px; color: {TEXT_SECONDARY}; margin-top: 2px; }}

.footer-text {{
    text-align: center; color: {TEXT_MUTED}; font-size: 11.5px;
    margin-top: 52px; padding: 16px;
    border-top: 1px solid {BORDER};
}}

.sidebar-nav-label {{
    font-size: 9.5px; font-weight: 700; color: {TEXT_MUTED};
    text-transform: uppercase; letter-spacing: 0.12em; margin: 6px 0 8px 2px;
}}

.step-circle {{
    width: 48px; height: 48px; border-radius: 50%;
    background: linear-gradient(135deg, {PRIMARY}30, {SECONDARY}30);
    border: 2px solid {PRIMARY}60; color: {PRIMARY};
    font-size: 18px; font-weight: 800;
    display: flex; align-items: center; justify-content: center;
    margin: 0 auto 12px;
    box-shadow: 0 0 20px {GLOW_BLUE};
    font-family: 'DM Mono', monospace;
}}

.hero-gradient {{
    background: linear-gradient(135deg, {PRIMARY} 0%, {SECONDARY} 50%, {ACCENT} 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}}

.stat-pill {{
    display: inline-flex; align-items: center; gap: 6px;
    background: {BG3}; border: 1px solid {BORDER};
    border-radius: 20px; padding: 5px 12px;
    font-size: 12px; font-weight: 600; color: {TEXT_SECONDARY};
}}
.stat-pill-dot {{
    width: 7px; height: 7px; border-radius: 50%;
    background: {ACCENT}; box-shadow: 0 0 8px {ACCENT};
}}

.stCaption, [data-testid="stCaptionContainer"] {{
    color: {TEXT_MUTED} !important; font-size: 12px !important;
}}
hr {{ border-color: {BORDER} !important; }}

.chat-response-card {{
    background: {BG3};
    border: 1px solid {BORDER};
    border-left: 3px solid {PRIMARY};
    border-radius: 14px;
    padding: 24px 22px;
    margin-top: 20px;
    line-height: 1.75;
    font-size: 14px;
}}
.chat-response-card p {{ margin-bottom: 12px; }}

.chat-context-strip {{
    background: {BG3};
    border: 1px solid {BORDER};
    border-radius: 12px;
    padding: 14px 18px;
    margin-bottom: 20px;
    display: flex;
    gap: 24px;
    flex-wrap: wrap;
    align-items: center;
}}
.chat-ctx-item {{
    display: flex;
    flex-direction: column;
    gap: 2px;
}}
.chat-ctx-label {{
    font-size: 9.5px;
    font-weight: 700;
    color: {TEXT_MUTED};
    text-transform: uppercase;
    letter-spacing: 0.1em;
}}
.chat-ctx-value {{
    font-size: 13px;
    font-weight: 700;
    color: {TEXT_PRIMARY};
}}
</style>
"""


def page_header(icon: str, title: str, subtitle: str) -> None:
    st.markdown(
        f"""
        <div class="page-header">
            <div class="page-header-icon">{icon}</div>
            <div>
                <div class="page-header-title">{title}</div>
                <div class="page-header-sub">{subtitle}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def init_session_state() -> None:
    """Initialise all session state keys with defaults."""
    defaults = {
        "profile": None,
        "metrics": None,
        "goals": [],
        "advice": None,
        "charts": {},
        "current_step": 1,
        "theme": "dark",
        "last_updated": None,
        "api_error": False,
        "chat_response": None,
        "chat_question": "",
        "chat_provider": "",
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


def render_home() -> None:
    """Home / landing page."""
    st.markdown(
        f"""
        <div style="text-align:center;padding:52px 0 36px;position:relative;">
            <div style="
                position:absolute;top:0;left:50%;transform:translateX(-50%);
                width:500px;height:300px;
                background:radial-gradient(ellipse at center, {GLOW_BLUE} 0%, transparent 70%);
                pointer-events:none;
            "></div>
            <div style="
                display:inline-flex;align-items:center;justify-content:center;
                width:80px;height:80px;border-radius:22px;
                background:linear-gradient(135deg, {PRIMARY}25, {SECONDARY}25);
                border:1px solid {PRIMARY}50;
                font-size:40px;margin-bottom:20px;
                box-shadow:0 0 40px {GLOW_BLUE};
            ">💰</div>
            <h1 class="hero-gradient" style="
                font-size:3rem;font-weight:900;margin-bottom:10px;line-height:1.1;
                letter-spacing:-0.04em;
            ">AI Financial Advisor</h1>
            <p style="color:{TEXT_SECONDARY};font-size:1.05rem;margin-top:12px;max-width:480px;margin-left:auto;margin-right:auto;line-height:1.6;font-weight:400;">
                Institutional-grade financial planning powered by
                <span style="color:{PRIMARY};font-weight:600;">AI</span>
                &mdash; built for Gemini &amp; Ollama
            </p>
            <div style="display:flex;gap:10px;justify-content:center;margin-top:20px;flex-wrap:wrap;">
                <span class="stat-pill"><span class="stat-pill-dot"></span>8 Health Metrics</span>
                <span class="stat-pill"><span class="stat-pill-dot" style="background:{SECONDARY};box-shadow:0 0 8px {SECONDARY};"></span>AI-Powered Advice</span>
                <span class="stat-pill"><span class="stat-pill-dot" style="background:{ACCENT2};box-shadow:0 0 8px {ACCENT2};"></span>PDF Export</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    c1, c2, c3 = st.columns(3)
    features = [
        ("🎯", "Goal-Based Planning", "Set financial goals and get customised investment roadmaps with monthly targets.", PRIMARY, GLOW_BLUE),
        ("🤖", "AI-Powered Advice", "AI analyses your finances and generates personalised strategies via Gemini or Ollama.", SECONDARY, GLOW_VIOLET),
        ("📊", "Visual Dashboard", "8 interactive charts: health gauge, projections, portfolio breakdown, and more.", ACCENT, GLOW_GREEN),
    ]
    for col, (icon, title, desc, accent_color, glow) in zip([c1, c2, c3], features):
        with col:
            st.markdown(
                f"""
                <div class="feature-card" style="--fc-accent:{accent_color};">
                    <div style="
                        display:inline-flex;align-items:center;justify-content:center;
                        width:54px;height:54px;border-radius:16px;
                        background:linear-gradient(135deg, {accent_color}20, {accent_color}10);
                        border:1px solid {accent_color}40;
                        font-size:28px;margin-bottom:14px;
                    ">{icon}</div>
                    <div style="font-weight:700;color:{TEXT_PRIMARY};font-size:15px;margin-bottom:8px;letter-spacing:-0.02em;">{title}</div>
                    <div style="color:{TEXT_SECONDARY};font-size:13px;line-height:1.55;">{desc}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown("<div style='margin-top:40px;'></div>", unsafe_allow_html=True)
    st.markdown(f"<div class='section-label'>🚀 How It Works</div>", unsafe_allow_html=True)

    steps = [
        ("1", "Fill Your Profile", "Enter income, expenses, savings, debt, and goals"),
        ("2", "Instant Analysis", "Get 8 financial health metrics computed in real-time"),
        ("3", "AI Advice", "AI generates personalised investment strategies & debt plans"),
        ("4", "Visualise & Export", "Interactive charts + downloadable PDF report"),
    ]
    cols = st.columns(4)
    for col, (num, title, desc) in zip(cols, steps):
        with col:
            st.markdown(
                f"""
                <div style="text-align:center;padding:20px 8px;">
                    <div class="step-circle">{num}</div>
                    <div style="font-weight:700;color:{TEXT_PRIMARY};font-size:14px;margin-bottom:6px;letter-spacing:-0.01em;">{title}</div>
                    <div style="color:{TEXT_SECONDARY};font-size:12.5px;line-height:1.5;">{desc}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown("<div style='margin-top:28px;'></div>", unsafe_allow_html=True)
    st.info(
        "👈 **Get started!** Click **Financial Profile** in the sidebar to begin your analysis. "
        "Use **Load Sample Data** to see a pre-filled example instantly."
    )


def render_analysis_page() -> None:
    profile = st.session_state.get("profile")
    if not profile:
        page_header("📊", "Health Analysis", "Your 8-metric financial health dashboard.")
        st.info("📋 Please complete your **Financial Profile** first to see your health analysis.")
        return

    if not st.session_state.get("metrics"):
        with st.spinner("⚙️ Computing your financial health metrics..."):
            metrics = compute_metrics(profile)
            st.session_state["metrics"] = metrics
            st.session_state["current_step"] = max(st.session_state["current_step"], 2)

    render_metrics_dashboard(st.session_state["metrics"], profile)


def render_goals_page() -> None:
    """Goal planning page."""
    profile = st.session_state.get("profile")
    metrics = st.session_state.get("metrics")

    if not profile:
        page_header("🎯", "Goal Planning", "Investment roadmaps for your financial goals.")
        st.info("📋 Please complete your **Financial Profile** first.")
        return
    if not metrics:
        page_header("🎯", "Goal Planning", "Investment roadmaps for your financial goals.")
        st.info("📊 Please visit **Health Analysis** first to compute your metrics.")
        return

    if not st.session_state.get("goals"):
        with st.spinner("🎯 Analysing your financial goals..."):
            goals = analyse_goals(profile, metrics)
            st.session_state["goals"] = goals
            st.session_state["current_step"] = max(st.session_state["current_step"], 3)

    render_goal_cards(st.session_state["goals"], metrics)


def render_advice_page() -> None:
    profile = st.session_state.get("profile")
    metrics = st.session_state.get("metrics")
    goals = st.session_state.get("goals", [])

    if not profile or not metrics:
        page_header("🤖", "AI Advice", "Personalised recommendations powered by AI.")
        st.info("📋 Please complete your profile and view the **Health Analysis** first.")
        return

    if not st.session_state.get("advice"):
        with st.spinner("🤖 Generating your personalised AI financial advice... (may take a few seconds)"):
            advice = generate_advice(profile, metrics, goals)
            st.session_state["advice"] = advice
            st.session_state["current_step"] = max(st.session_state["current_step"], 4)

    render_advice_sections(st.session_state["advice"])

    st.markdown("<div style='margin-top:16px;'></div>", unsafe_allow_html=True)
    if st.button("🔄 Regenerate AI Advice", help="Generate fresh advice from your AI provider"):
        st.session_state["advice"] = None
        st.rerun()


def render_dashboard_page() -> None:
    """Visualisation Dashboard page."""
    profile = st.session_state.get("profile")
    metrics = st.session_state.get("metrics")
    goals = st.session_state.get("goals") or []
    advice = st.session_state.get("advice") or {}

    if not profile or not metrics:
        page_header("📈", "Dashboard", "Interactive visualisation of your financial data.")
        st.info("📋 Please complete your profile and view the **Health Analysis** first.")
        return

    if not st.session_state.get("charts"):
        with st.spinner("📊 Generating your visualisation dashboard..."):
            charts = generate_charts(profile, metrics, goals, advice or {})
            st.session_state["charts"] = charts
            st.session_state["current_step"] = max(st.session_state["current_step"], 5)

    render_dashboard(profile, metrics, goals, st.session_state["charts"])

    st.markdown("<div style='margin-top:8px;'></div>", unsafe_allow_html=True)
    if st.button("🔄 Refresh Charts"):
        st.session_state["charts"] = {}
        st.rerun()



def render_chat_page() -> None:
    """AI Chat page — free-form financial Q&A."""
    profile = st.session_state.get("profile")
    metrics = st.session_state.get("metrics")

    page_header(
        "🗨️",
        "AI Chat",
        "Ask any financial question — the AI responds using your personal financial data.",
    )

    if not profile:
        st.info("📋 Please complete your **Financial Profile** first so the AI can personalise its answers.")
        return

    # Compute metrics on demand if not yet done
    if not metrics:
        with st.spinner("⚙️ Computing your financial metrics first..."):
            metrics = compute_metrics(profile)
            st.session_state["metrics"] = metrics

    # Financial context strip
    score = metrics.financial_health_score
    score_color = (
        ACCENT if score >= 80 else PRIMARY if score >= 60 else ACCENT2 if score >= 40 else "#F87171"
    )
    st.markdown(
        f"""
        <div class="chat-context-strip">
            <div class="chat-ctx-item">
                <div class="chat-ctx-label">Health Score</div>
                <div class="chat-ctx-value" style="color:{score_color};">{score}/100</div>
            </div>
            <div class="chat-ctx-item">
                <div class="chat-ctx-label">Monthly Surplus</div>
                <div class="chat-ctx-value">₹{metrics.net_monthly_surplus:,.0f}</div>
            </div>
            <div class="chat-ctx-item">
                <div class="chat-ctx-label">Savings Rate</div>
                <div class="chat-ctx-value">{metrics.savings_rate_pct:.1f}%</div>
            </div>
            <div class="chat-ctx-item">
                <div class="chat-ctx-label">DTI Ratio</div>
                <div class="chat-ctx-value">{metrics.dti_ratio_pct:.1f}%</div>
            </div>
            <div class="chat-ctx-item">
                <div class="chat-ctx-label">Emergency Fund</div>
                <div class="chat-ctx-value">{metrics.emergency_fund_months:.1f} months</div>
            </div>
            <div style="margin-left:auto;">
                <span style="font-size:11px;color:{TEXT_MUTED};">Context: {profile.name} · {profile.occupation} · {profile.risk_tolerance.value.title()} Risk</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Question input
    question = st.text_area(
        "Your question",
        value=st.session_state.get("chat_question", ""),
        placeholder="e.g. How should I reduce my debt fastest? What SIP amount should I start with?",
        height=90,
        label_visibility="collapsed",
        key="chat_input",
    )

    col_btn, col_clear = st.columns([1, 5])
    with col_btn:
        send_clicked = st.button("✨ Ask", type="primary", use_container_width=True)
    with col_clear:
        if st.session_state.get("chat_response") and st.button("🗑️ Clear", use_container_width=False):
            st.session_state["chat_response"] = None
            st.session_state["chat_question"] = ""
            st.session_state["chat_provider"] = ""
            st.rerun()

    if send_clicked:
        q = question.strip()
        if not q:
            st.warning("Please type a question before clicking Ask.")
        else:
            st.session_state["chat_question"] = q
            with st.spinner("🤖 Thinking..."):
                try:
                    answer, provider_label = ask_financial_advisor(q, profile, metrics)
                    st.session_state["chat_response"] = answer
                    st.session_state["chat_provider"] = provider_label
                except Exception as exc:
                    st.session_state["chat_response"] = None
                    st.error(f"❌ Could not get a response: {exc}")

    # Response display
    response = st.session_state.get("chat_response")
    if response:
        provider_label = st.session_state.get("chat_provider", "")
        tier_icons = {
            "Gemini Cloud (Ollama)": "☁️",
            "Gemini API": "✨",
            "Ollama Local": "🖥️",
            "Rule-based": "⚙️",
        }
        icon = tier_icons.get(provider_label, "🤖")
        st.markdown(
            f"<div style='font-size:12px;color:{TEXT_MUTED};margin-top:16px;'>"
            f"{icon} <strong style='color:{TEXT_SECONDARY};'>{provider_label}</strong>&nbsp;&nbsp;·&nbsp;&nbsp;"
            f"<em style='color:{TEXT_MUTED};'>Based on your live financial profile</em></div>",
            unsafe_allow_html=True,
        )
        st.markdown(
            f"<div class='chat-response-card'>{response}</div>",
            unsafe_allow_html=True,
        )


def render_export_page() -> None:
    profile = st.session_state.get("profile")
    metrics = st.session_state.get("metrics")
    goals = st.session_state.get("goals", [])
    advice = st.session_state.get("advice")
    charts = st.session_state.get("charts", {})

    page_header("📄", "Export Report", "Download a professional PDF report with all analysis and recommendations.")

    if not profile:
        st.info("📋 Please complete your **Financial Profile** first.")
        return

    if not metrics:
        st.info("📊 Please complete the **Health Analysis** step first.")
        return

    if not advice:
        st.info(
            "💡 AI advice hasn't been generated yet — the report will include rule-based guidance. "
            "Visit **AI Advice** first for personalised recommendations."
        )
        from prompts.advice_prompts import FALLBACK_ADVICE
        advice = FALLBACK_ADVICE

    with st.expander("📋 Report Sections Preview", expanded=True):
        sections = [
            ("REE-R01", "Cover Page", "User name, date, financial health score badge"),
            ("REE-R02", "Executive Summary", "AI-generated 3-paragraph overview"),
            ("REE-R03", "Financial Metrics Table", "All 8 metrics with benchmarks"),
            ("REE-R04", "AI Recommendations", "Investment, savings, debt strategies"),
            ("REE-R05", "Goal Investment Plans", "Per-goal roadmaps and timelines"),
            ("REE-R07", "30-60-90 Action Plan", "Prioritised immediate actions"),
            ("REE-R08", "Disclaimer", "Standard financial advisory disclaimer"),
        ]
        for sec_id, title, desc in sections:
            st.markdown(
                f"""
                <div style="display:flex;align-items:center;gap:12px;padding:10px 0;border-bottom:1px solid {BORDER};">
                    <span style="font-family:'DM Mono',monospace;font-size:11px;color:{TEXT_MUTED};min-width:72px;">{sec_id}</span>
                    <span style="font-weight:600;color:{TEXT_PRIMARY};font-size:13px;min-width:180px;">{title}</span>
                    <span style="color:{TEXT_SECONDARY};font-size:12px;">{desc}</span>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.divider()

    filename = f"AI_Financial_Report_{profile.name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.pdf"

    if st.button("📥 Generate & Download PDF Report", type="primary", use_container_width=True):
        with st.spinner("📄 Compiling your report... (up to 5 seconds)"):
            try:
                pdf_buf = generate_report(profile, metrics, goals, advice, charts)
                st.download_button(
                    label="⬇️ Click to Download Report",
                    data=pdf_buf,
                    file_name=filename,
                    mime="application/pdf",
                    use_container_width=True,
                )
                st.success(f"✅ Report ready! File: `{filename}`")
                st.session_state["current_step"] = 6
            except Exception as e:
                st.error(f"❌ PDF generation failed: {e}. Please try again.")


def render_sidebar() -> str:
    """Render the navigation sidebar. Returns selected page name."""
    with st.sidebar:
        st.markdown(
            f"""
            <div class="sidebar-brand">
                <div class="sidebar-brand-icon">💰</div>
                <div>
                    <div class="sidebar-brand-name">FinanceAI</div>
                    <div class="sidebar-brand-version">v1.0.0 · Educational</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        profile = st.session_state.get("profile")
        if profile:
            st.markdown(
                f"""
                <div class="profile-badge">
                    <div class="profile-badge-label">● Active Profile</div>
                    <div class="profile-badge-name">{profile.name}</div>
                    <div class="profile-badge-sub">{profile.occupation} · {profile.risk_tolerance.value.title()} Risk</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.markdown("<div class='sidebar-nav-label'>Navigation</div>", unsafe_allow_html=True)

        pages = [
            "🏠 Home",
            "📋 Financial Profile",
            "📊 Health Analysis",
            "🎯 Goal Planning",
            "🤖 AI Advice",
            "🗨️ AI Chat",
            "📈 Dashboard",
            "📄 Export Report",
        ]

        page = st.radio("Navigation", pages, label_visibility="collapsed")

        step = st.session_state.get("current_step", 1)
        progress = min((step - 1) / 5, 1.0)
        st.markdown("<div style='margin-top:28px;'></div>", unsafe_allow_html=True)
        st.markdown(
            f"<div class='sidebar-nav-label'>Workflow &nbsp;·&nbsp; Step {step} of 6</div>",
            unsafe_allow_html=True,
        )
        st.progress(progress)

        step_labels = ["Profile", "Analysis", "Goals", "Advice", "Dashboard", "Export"]
        for i, label in enumerate(step_labels, 1):
            done = i < step
            active = i == step
            color = PRIMARY if active else (ACCENT if done else TEXT_MUTED)
            icon = "✓" if done else ("●" if active else "○")
            st.markdown(
                f"<div style='font-size:11px;color:{color};padding:2px 0 2px 4px;font-weight:{'700' if active else '500'};'>"
                f"<span style='font-family:monospace;margin-right:6px;'>{icon}</span>{label}</div>",
                unsafe_allow_html=True,
            )

        st.markdown("<div style='margin-top:24px;'></div>", unsafe_allow_html=True)
        st.markdown(
            f"<div style='color:{TEXT_MUTED};font-size:10.5px;text-align:center;padding:12px 0 4px;line-height:1.6;border-top:1px solid {BORDER};'>"
            "Educational use only<br>Not professional financial advice"
            "</div>",
            unsafe_allow_html=True,
        )

    return page

def main() -> None:
    """Main application entrypoint."""
    st.set_page_config(
        page_title=APP_TITLE,
        page_icon=APP_ICON,
        layout="wide",
        initial_sidebar_state="expanded",
    )

    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
    init_session_state()
    page = render_sidebar()

    if page == "🏠 Home":
        render_home()
    elif page == "📋 Financial Profile":
        render_profile_form()
    elif page == "📊 Health Analysis":
        render_analysis_page()
    elif page == "🎯 Goal Planning":
        render_goals_page()
    elif page == "🤖 AI Advice":
        render_advice_page()
    elif page == "🗨️ AI Chat":
        render_chat_page()
    elif page == "📈 Dashboard":
        render_dashboard_page()
    elif page == "📄 Export Report":
        render_export_page()

    st.markdown(
        f'<div class="footer-text">{APP_FOOTER}</div>',
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
