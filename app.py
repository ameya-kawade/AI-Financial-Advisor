"""
AI Financial Advisor — Main Streamlit Application Entry Point.
Orchestrates all 6 modules with navigation, session state, and workflow management.
"""

from __future__ import annotations

import os
from datetime import datetime

import streamlit as st
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from config.settings import APP_FOOTER, APP_ICON, APP_TITLE
from modules.apae_module import generate_advice, render_advice_sections
from modules.dvd_module import generate_charts, render_dashboard
from modules.fhae_module import compute_metrics, render_metrics_dashboard
from modules.fpi_module import render_profile_form
from modules.gbipe_module import analyse_goals, render_goal_cards
from modules.ree_module import generate_report

# ── Design Tokens — Minimal Warm Palette ──────────────────────────────────────
PRIMARY       = "#3B82F6"   # Softer, sky-tinged blue
SECONDARY     = "#818CF8"   # Muted indigo
ACCENT        = "#34D399"   # Soft emerald
BG            = "#F4F6F9"   # Warm grey-blue background
CARD_BG       = "#FFFFFF"
TEXT_PRIMARY  = "#1E293B"   # Slate-800 — readable but not harsh black
TEXT_SECONDARY= "#64748B"   # Slate-500
BORDER        = "#DDE3EC"   # Softer border
WARNING_CLR   = "#F59E0B"
DANGER_CLR    = "#F87171"   # Softer coral-red

# ── Custom CSS ─────────────────────────────────────────────────────────────────
CUSTOM_CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

html, body, [class*="css"] {{
    font-family: 'Inter', sans-serif !important;
    background-color: {BG} !important;
    color: {TEXT_PRIMARY} !important;
}}

/* ── Global text softening ─────────────────────────────────────────── */
p, span, div, label, li {{
    color: {TEXT_PRIMARY};
}}

/* ── Sidebar ──────────────────────────────────────────────────────── */
[data-testid="stSidebar"] {{
    background: {CARD_BG} !important;
    border-right: 1px solid {BORDER} !important;
}}
[data-testid="stSidebar"] * {{
    color: {TEXT_PRIMARY} !important;
}}
[data-testid="stSidebar"] .stRadio label {{
    border-radius: 8px;
    padding: 9px 14px;
    margin: 2px 0;
    transition: background 0.15s ease;
    display: block;
    cursor: pointer;
    font-size: 14px;
    font-weight: 500;
    color: {TEXT_SECONDARY} !important;
}}
[data-testid="stSidebar"] .stRadio label:hover {{
    background: {BG} !important;
    color: {PRIMARY} !important;
}}
[data-testid="stSidebar"] .stRadio [data-testid="stMarkdownContainer"] p {{
    margin: 0;
}}

/* ── Main container ────────────────────────────────────────────────── */
.main .block-container {{
    padding-top: 2rem;
    padding-bottom: 3rem;
    max-width: 1200px;
}}

/* ── Page header card ──────────────────────────────────────────────── */
.page-header {{
    background: {CARD_BG};
    border: 1px solid {BORDER};
    border-radius: 16px;
    padding: 24px 28px;
    margin-bottom: 28px;
    display: flex;
    align-items: center;
    gap: 16px;
    box-shadow: 0 1px 4px rgba(30,41,59,0.06);
}}
.page-header-icon {{
    font-size: 36px;
    line-height: 1;
}}
.page-header-title {{
    font-size: 1.55rem;
    font-weight: 700;
    color: {TEXT_PRIMARY};
    margin: 0;
    line-height: 1.2;
}}
.page-header-sub {{
    font-size: 13px;
    color: {TEXT_SECONDARY};
    margin: 4px 0 0;
    font-weight: 400;
}}

/* ── KPI cards ─────────────────────────────────────────────────────── */
.kpi-card {{
    background: {CARD_BG};
    border: 1px solid {BORDER};
    border-radius: 12px;
    padding: 18px 16px;
    border-top: 3px solid {PRIMARY};
    box-shadow: 0 1px 3px rgba(30,41,59,0.05);
    transition: box-shadow 0.2s ease;
    min-height: 96px;
}}
.kpi-card:hover {{
    box-shadow: 0 4px 12px rgba(59,130,246,0.10);
}}
.kpi-value {{
    font-size: 1.6rem;
    font-weight: 700;
    color: {TEXT_PRIMARY};
    line-height: 1.1;
    margin-bottom: 4px;
}}
.kpi-label {{
    font-size: 11px;
    font-weight: 600;
    color: {TEXT_SECONDARY};
    text-transform: uppercase;
    letter-spacing: 0.06em;
    margin-bottom: 3px;
}}
.kpi-sub {{
    font-size: 12px;
    color: {TEXT_SECONDARY};
}}

/* ── Feature cards (home page) ─────────────────────────────────────── */
.feature-card {{
    background: {CARD_BG};
    border: 1px solid {BORDER};
    border-radius: 14px;
    padding: 26px 20px;
    text-align: center;
    box-shadow: 0 1px 3px rgba(30,41,59,0.05);
    transition: transform 0.2s ease, box-shadow 0.2s ease;
    height: 180px;
}}
.feature-card:hover {{
    transform: translateY(-2px);
    box-shadow: 0 6px 18px rgba(59,130,246,0.10);
}}

/* ── Section divider label ─────────────────────────────────────────── */
.section-label {{
    font-size: 12px;
    font-weight: 600;
    color: {TEXT_SECONDARY};
    text-transform: uppercase;
    letter-spacing: 0.07em;
    margin: 22px 0 10px;
    display: flex;
    align-items: center;
    gap: 8px;
}}
.section-label::after {{
    content: '';
    flex: 1;
    height: 1px;
    background: {BORDER};
}}

/* ── Form cards ────────────────────────────────────────────────────── */
.form-card {{
    background: {CARD_BG};
    border: 1px solid {BORDER};
    border-radius: 12px;
    padding: 20px 18px;
    margin-bottom: 16px;
    box-shadow: 0 1px 3px rgba(30,41,59,0.04);
}}

/* ── Goals card ────────────────────────────────────────────────────── */
.goal-card {{
    background: {CARD_BG};
    border: 1px solid {BORDER};
    border-radius: 14px;
    padding: 20px 18px;
    margin-bottom: 18px;
    box-shadow: 0 1px 5px rgba(30,41,59,0.05);
    transition: box-shadow 0.2s ease;
}}
.goal-card:hover {{
    box-shadow: 0 5px 16px rgba(30,41,59,0.09);
}}

/* ── Advice card ───────────────────────────────────────────────────── */
.advice-card {{
    background: {CARD_BG};
    border: 1px solid {BORDER};
    border-radius: 12px;
    padding: 18px;
    margin-bottom: 14px;
    box-shadow: 0 1px 3px rgba(30,41,59,0.04);
}}

/* ── Action plan mini-card ─────────────────────────────────────────── */
.action-mini-card {{
    background: {BG};
    border: 1px solid {BORDER};
    border-radius: 10px;
    padding: 14px;
    height: 100%;
}}
.action-mini-card h4 {{
    color: {PRIMARY};
    margin: 0 0 10px;
    font-size: 13px;
    font-weight: 600;
}}

/* ── Status badges ─────────────────────────────────────────────────── */
.badge-excellent {{ background:#ECFDF5; color:#065F46; padding:3px 10px; border-radius:20px; font-size:12px; font-weight:600; border:1px solid #A7F3D0; }}
.badge-good      {{ background:#EFF6FF; color:#1D4ED8; padding:3px 10px; border-radius:20px; font-size:12px; font-weight:600; border:1px solid #BFDBFE; }}
.badge-warning   {{ background:#FFF7ED; color:#C2410C; padding:3px 10px; border-radius:20px; font-size:12px; font-weight:600; border:1px solid #FED7AA; }}
.badge-critical  {{ background:#FEF2F2; color:#B91C1C; padding:3px 10px; border-radius:20px; font-size:12px; font-weight:600; border:1px solid #FECACA; }}

/* ── Buttons ───────────────────────────────────────────────────────── */
.stButton > button[kind="primary"] {{
    background: {PRIMARY} !important;
    color: white !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    padding: 0.5rem 1.2rem !important;
    font-size: 14px !important;
    transition: background 0.18s ease, box-shadow 0.18s ease !important;
    box-shadow: 0 1px 4px rgba(59,130,246,0.22) !important;
}}
.stButton > button[kind="primary"]:hover {{
    background: #2563EB !important;
    box-shadow: 0 3px 10px rgba(59,130,246,0.30) !important;
}}
.stButton > button:not([kind="primary"]) {{
    border-radius: 8px !important;
    font-weight: 500 !important;
    font-size: 14px !important;
    border: 1px solid {BORDER} !important;
    background: {CARD_BG} !important;
    color: {TEXT_PRIMARY} !important;
    transition: background 0.15s ease !important;
}}
.stButton > button:not([kind="primary"]):hover {{
    background: {BG} !important;
    border-color: {PRIMARY} !important;
    color: {PRIMARY} !important;
}}

/* ── Progress bar ──────────────────────────────────────────────────── */
.stProgress > div > div {{
    background: linear-gradient(90deg, {PRIMARY}, {ACCENT}) !important;
    border-radius: 4px !important;
}}

/* ── Tabs ──────────────────────────────────────────────────────────── */
.stTabs [data-baseweb="tab-list"] {{
    gap: 4px;
    background: {CARD_BG};
    border-radius: 10px;
    padding: 4px;
    border: 1px solid {BORDER};
}}
.stTabs [data-baseweb="tab"] {{
    border-radius: 7px;
    font-weight: 500;
    font-size: 13px;
    color: {TEXT_SECONDARY};
}}
.stTabs [aria-selected="true"] {{
    background: {PRIMARY} !important;
    color: white !important;
    box-shadow: 0 1px 6px rgba(59,130,246,0.20) !important;
}}

/* ── Expanders ─────────────────────────────────────────────────────── */
.streamlit-expanderHeader {{
    font-weight: 600 !important;
    color: {TEXT_PRIMARY} !important;
    font-size: 14px !important;
    border-radius: 8px !important;
}}
[data-testid="stExpander"] {{
    border: 1px solid {BORDER} !important;
    border-radius: 10px !important;
    margin-bottom: 8px !important;
    overflow: hidden !important;
}}

/* ── Inputs ────────────────────────────────────────────────────────── */
.stNumberInput > div > div > input,
.stTextInput > div > div > input {{
    border-radius: 8px !important;
    border-color: {BORDER} !important;
    font-size: 14px !important;
    color: {TEXT_PRIMARY} !important;
    background: {CARD_BG} !important;
}}
.stSelectbox > div > div {{
    border-radius: 8px !important;
}}

/* ── Metrics ────────────────────────────────────────────────────────── */
[data-testid="stMetric"] {{
    background: {CARD_BG};
    border: 1px solid {BORDER};
    border-radius: 10px;
    padding: 12px 14px;
}}
[data-testid="stMetricValue"] {{
    color: {TEXT_PRIMARY} !important;
}}
[data-testid="stMetricLabel"] {{
    color: {TEXT_SECONDARY} !important;
}}

/* ── Dataframe ──────────────────────────────────────────────────────── */
[data-testid="stDataFrame"] {{
    border-radius: 10px;
    overflow: hidden;
    border: 1px solid {BORDER};
}}

/* ── Alert/info boxes — remove yellow, use muted blue ──────────────── */
.stAlert[data-baseweb="notification"][kind="warning"] {{
    background: #FFF7ED !important;
    border-color: #FED7AA !important;
    color: #92400E !important;
}}
.stAlert[data-baseweb="notification"][kind="info"] {{
    background: #EFF6FF !important;
    border-color: #BFDBFE !important;
    color: #1E40AF !important;
}}

/* ── Sidebar brand area ─────────────────────────────────────────────── */
.sidebar-brand {{
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 12px 4px 16px;
    border-bottom: 1px solid {BORDER};
    margin-bottom: 16px;
}}
.sidebar-brand-icon {{
    font-size: 26px;
    line-height: 1;
}}
.sidebar-brand-name {{
    font-size: 15px;
    font-weight: 700;
    color: {TEXT_PRIMARY};
    line-height: 1.2;
}}
.sidebar-brand-version {{
    font-size: 11px;
    color: {TEXT_SECONDARY};
}}

/* ── Profile badge (sidebar) ────────────────────────────────────────── */
.profile-badge {{
    background: {BG};
    border: 1px solid {BORDER};
    border-radius: 9px;
    padding: 9px 12px;
    margin-bottom: 12px;
}}
.profile-badge-label {{
    font-size: 10px;
    font-weight: 600;
    color: {TEXT_SECONDARY};
    text-transform: uppercase;
    letter-spacing: 0.07em;
    margin-bottom: 2px;
}}
.profile-badge-name {{
    font-size: 13px;
    font-weight: 700;
    color: {TEXT_PRIMARY};
}}
.profile-badge-sub {{
    font-size: 11px;
    color: {TEXT_SECONDARY};
    margin-top: 1px;
}}

/* ── Footer ─────────────────────────────────────────────────────────── */
.footer-text {{
    text-align: center;
    color: {TEXT_SECONDARY};
    font-size: 12px;
    margin-top: 48px;
    padding: 14px;
    border-top: 1px solid {BORDER};
}}

/* ── Sidebar nav label ──────────────────────────────────────────────── */
.sidebar-nav-label {{
    font-size: 10px;
    font-weight: 600;
    color: {TEXT_SECONDARY};
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin: 4px 0 6px 2px;
}}

/* ── Step circle ────────────────────────────────────────────────────── */
.step-circle {{
    width: 42px; height: 42px;
    border-radius: 50%;
    background: linear-gradient(135deg, {PRIMARY}, {SECONDARY});
    color: white;
    font-size: 17px;
    font-weight: 800;
    display: flex;
    align-items: center;
    justify-content: center;
    margin: 0 auto 10px;
    box-shadow: 0 2px 6px rgba(59,130,246,0.22);
}}
</style>
"""


# ── Helpers ────────────────────────────────────────────────────────────────────

def page_header(icon: str, title: str, subtitle: str) -> None:
    """Render a consistent page header card."""
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


# ── Session State ──────────────────────────────────────────────────────────────

def init_session_state() -> None:
    """Initialise all session state keys with defaults."""
    defaults = {
        "profile": None,
        "metrics": None,
        "goals": [],
        "advice": None,
        "charts": {},
        "current_step": 1,
        "theme": "light",
        "last_updated": None,
        "api_error": False,
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


# ── Page Renderers ─────────────────────────────────────────────────────────────

def render_home() -> None:
    """Home / landing page."""
    st.markdown(
        f"""
        <div style="text-align:center;padding:36px 0 28px;">
            <div style="font-size:64px;margin-bottom:12px;line-height:1;">💰</div>
            <h1 style="
                font-size:2.6rem;font-weight:800;margin-bottom:8px;
                background:linear-gradient(135deg,{PRIMARY},{SECONDARY});
                -webkit-background-clip:text;-webkit-text-fill-color:transparent;
                background-clip:text;
            ">AI Financial Advisor</h1>
            <p style="color:{TEXT_SECONDARY};font-size:1.1rem;margin-top:8px;max-width:520px;margin-left:auto;margin-right:auto;">
                Personalised financial planning powered by <strong style="color:{PRIMARY};">AI</strong>
                &mdash; Gemini &amp; Ollama
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Feature cards
    c1, c2, c3 = st.columns(3)
    features = [
        ("🎯", "Goal-Based Planning", f"Set financial goals and get customised investment roadmaps with monthly targets.", PRIMARY),
        ("🤖", "AI-Powered Advice", f"AI analyses your finances and generates personalised strategies via Gemini or Ollama.", SECONDARY),
        ("📊", "Visual Dashboard", f"8 interactive charts: health gauge, projections, portfolio breakdown, and more.", ACCENT),
    ]
    for col, (icon, title, desc, accent_color) in zip([c1, c2, c3], features):
        with col:
            st.markdown(
                f"""
                <div class="feature-card">
                    <div style="font-size:36px;margin-bottom:12px;">{icon}</div>
                    <div style="font-weight:700;color:{TEXT_PRIMARY};font-size:15px;margin-bottom:8px;">{title}</div>
                    <div style="color:{TEXT_SECONDARY};font-size:13px;line-height:1.5;">{desc}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown("<div style='margin-top:32px;'></div>", unsafe_allow_html=True)
    st.markdown(
        f"<div class='section-label'>🚀 How It Works</div>",
        unsafe_allow_html=True,
    )

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
                <div style="text-align:center;padding:16px 8px;">
                    <div class="step-circle">{num}</div>
                    <div style="font-weight:700;color:{TEXT_PRIMARY};font-size:14px;margin-bottom:4px;">{title}</div>
                    <div style="color:{TEXT_SECONDARY};font-size:12px;line-height:1.4;">{desc}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown("<div style='margin-top:24px;'></div>", unsafe_allow_html=True)
    st.info(
        "👈 **Get started!** Click **Financial Profile** in the sidebar to begin your analysis. "
        "Use **Load Sample Data** to see a pre-filled example instantly."
    )


def render_analysis_page() -> None:
    """Financial Health Analysis page."""
    profile = st.session_state.get("profile")
    if not profile:
        page_header("📊", "Health Analysis", "Your 8-metric financial health dashboard.")
        st.info("📋 Please complete your **Financial Profile** first to see your health analysis.")
        return

    # Auto-compute metrics if not yet done
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

    # Auto-compute goals if not yet done
    if not st.session_state.get("goals"):
        with st.spinner("🎯 Analysing your financial goals..."):
            goals = analyse_goals(profile, metrics)
            st.session_state["goals"] = goals
            st.session_state["current_step"] = max(st.session_state["current_step"], 3)

    render_goal_cards(st.session_state["goals"], metrics)


def render_advice_page() -> None:
    """AI Advice page."""
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

    # Regenerate button
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

    # Refresh charts button
    st.markdown("<div style='margin-top:8px;'></div>", unsafe_allow_html=True)
    if st.button("🔄 Refresh Charts"):
        st.session_state["charts"] = {}
        st.rerun()


def render_export_page() -> None:
    """PDF Export page."""
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

    # Report preview
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
            st.markdown(f"**{sec_id}** | **{title}** — {desc}")

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


# ── Sidebar ────────────────────────────────────────────────────────────────────

def render_sidebar() -> str:
    """Render the navigation sidebar. Returns selected page name."""
    with st.sidebar:
        # Brand
        st.markdown(
            f"""
            <div class="sidebar-brand">
                <div class="sidebar-brand-icon">💰</div>
                <div>
                    <div class="sidebar-brand-name">AI Financial Advisor</div>
                    <div class="sidebar-brand-version">v1.0.0 · Educational</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Profile status badge
        profile = st.session_state.get("profile")
        if profile:
            st.markdown(
                f"""
                <div class="profile-badge">
                    <div class="profile-badge-label">Active Profile</div>
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
            "📈 Dashboard",
            "📄 Export Report",
        ]

        page = st.radio("Navigation", pages, label_visibility="collapsed")

        # Workflow progress
        step = st.session_state.get("current_step", 1)
        progress = min((step - 1) / 5, 1.0)
        st.markdown("<div style='margin-top:24px;'></div>", unsafe_allow_html=True)
        st.markdown(
            f"<div class='sidebar-nav-label'>Workflow Progress &nbsp; Step {step} / 6</div>",
            unsafe_allow_html=True,
        )
        st.progress(progress)

        st.markdown("<div style='margin-top:20px;'></div>", unsafe_allow_html=True)
        st.markdown(
            f"<div style='color:{TEXT_SECONDARY};font-size:11px;text-align:center;padding:4px 0;line-height:1.5;'>"
            "Educational use only · Not professional financial advice"
            "</div>",
            unsafe_allow_html=True,
        )

    return page


# ── Main ───────────────────────────────────────────────────────────────────────

def main() -> None:
    """Main application entrypoint."""
    st.set_page_config(
        page_title=APP_TITLE,
        page_icon=APP_ICON,
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # Apply custom CSS
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

    # Initialise session state
    init_session_state()

    # Render navigation
    page = render_sidebar()

    # Route to correct page
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
    elif page == "📈 Dashboard":
        render_dashboard_page()
    elif page == "📄 Export Report":
        render_export_page()

    # Footer
    st.markdown(
        f'<div class="footer-text">{APP_FOOTER}</div>',
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
