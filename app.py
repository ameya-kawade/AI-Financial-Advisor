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

# ── Custom CSS ────────────────────────────────────────────────────────────────
CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif !important;
}

/* Sidebar styling */
[data-testid="stSidebar"] {
    background: linear-gradient(160deg, #1F3864 0%, #2E75B6 100%) !important;
}
[data-testid="stSidebar"] * {
    color: white !important;
}
[data-testid="stSidebar"] .stRadio label {
    background: rgba(255,255,255,0.1);
    border-radius: 8px;
    padding: 8px 12px;
    margin: 3px 0;
    transition: background 0.2s;
    display: block;
    cursor: pointer;
}
[data-testid="stSidebar"] .stRadio label:hover {
    background: rgba(255,255,255,0.2) !important;
}

/* Main container */
.main .block-container {
    padding-top: 1.5rem;
    max-width: 1200px;
}

/* App header */
.app-header {
    background: linear-gradient(135deg, #1F3864, #2E75B6);
    color: white;
    padding: 16px 24px;
    border-radius: 12px;
    margin-bottom: 24px;
    display: flex;
    align-items: center;
    justify-content: space-between;
}

/* Metric cards */
.metric-card {
    background: #EBF2FA;
    border-radius: 10px;
    padding: 16px;
    border-left: 4px solid #2E75B6;
    margin-bottom: 12px;
}
.metric-value { font-size: 28px; font-weight: 700; color: #1F3864; }
.metric-label { font-size: 13px; color: #595959; text-transform: uppercase; }

/* Status colours */
.status-excellent { color: #1E7145; font-weight: 600; }
.status-good      { color: #2E75B6; font-weight: 600; }
.status-warning   { color: #F5A623; font-weight: 600; }
.status-critical  { color: #C0392B; font-weight: 600; }

/* Advice sections */
.advice-section {
    background: #FFFFFF;
    border: 1px solid #BDD7EE;
    border-radius: 8px;
    padding: 20px;
    margin-bottom: 16px;
}

/* Buttons */
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #1F3864, #2E75B6) !important;
    color: white !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    padding: 0.6rem 1.5rem !important;
    transition: opacity 0.2s !important;
}
.stButton > button[kind="primary"]:hover {
    opacity: 0.9 !important;
}

/* Progress bar */
.stProgress > div > div {
    background: linear-gradient(90deg, #2E75B6, #1E7145) !important;
}

/* Tab styling */
.stTabs [data-baseweb="tab-list"] {
    gap: 8px;
    background: #F8FAFD;
    border-radius: 10px;
    padding: 4px;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 8px;
    font-weight: 500;
}
.stTabs [aria-selected="true"] {
    background: white !important;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1) !important;
}

/* Expanders */
.streamlit-expanderHeader {
    font-weight: 600 !important;
    color: #1F3864 !important;
}

/* Footer */
.footer-text {
    text-align: center;
    color: #888;
    font-size: 12px;
    margin-top: 40px;
    padding: 16px;
    border-top: 1px solid #E0E0E0;
}

/* Number inputs */
.stNumberInput > div > div > input {
    border-radius: 6px !important;
}
</style>
"""


# ── Session State ─────────────────────────────────────────────────────────────

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


# ── Page Renderers ────────────────────────────────────────────────────────────

def render_home() -> None:
    """Home / landing page."""
    st.markdown(
        """
        <div style="text-align:center;padding:20px 0;">
            <div style="font-size:72px;margin-bottom:8px;">💰</div>
            <h1 style="color:#1F3864;font-size:2.5rem;font-weight:800;margin-bottom:0;">
                AI Financial Advisor
            </h1>
            <p style="color:#2E75B6;font-size:1.2rem;margin-top:8px;">
                Personalised financial planning powered by <b>Gemini 2.0 Flash</b>
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Feature cards
    c1, c2, c3 = st.columns(3)
    features = [
        ("🎯", "Goal-Based Planning", "Set financial goals and get customised investment roadmaps with monthly targets."),
        ("🤖", "AI-Powered Advice", "Gemini 2.0 Flash analyses your finances and generates personalised strategies."),
        ("📊", "Visual Dashboard", "8 interactive charts including health gauge, projections, and portfolio breakdown."),
    ]
    for col, (icon, title, desc) in zip([c1, c2, c3], features):
        with col:
            st.markdown(
                f"""
                <div style="
                    background: linear-gradient(135deg, #EBF2FA, #F8FAFD);
                    border-radius: 12px; padding: 24px 20px; text-align: center;
                    border: 1px solid #BDD7EE; height: 160px;
                    box-shadow: 0 2px 12px rgba(0,0,0,0.06);
                ">
                    <div style="font-size: 36px; margin-bottom: 8px;">{icon}</div>
                    <div style="font-weight: 700; color: #1F3864; font-size: 15px; margin-bottom: 6px;">{title}</div>
                    <div style="color: #595959; font-size: 13px;">{desc}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown("---")

    # How it works
    st.markdown("### 🚀 How It Works")
    steps = [
        ("1", "Fill Your Profile", "Enter income, expenses, savings, debt, and financial goals"),
        ("2", "Instant Analysis", "Get 8 financial health metrics computed in real-time"),
        ("3", "AI Advice", "Gemini generates personalised investment strategies and debt plans"),
        ("4", "Visualise & Export", "Interactive charts + downloadable PDF report"),
    ]
    cols = st.columns(4)
    for col, (num, title, desc) in zip(cols, steps):
        with col:
            st.markdown(
                f"""
                <div style="text-align:center;">
                    <div style="
                        width:48px;height:48px;border-radius:50%;
                        background:linear-gradient(135deg,#1F3864,#2E75B6);
                        color:white;font-size:20px;font-weight:800;
                        display:flex;align-items:center;justify-content:center;
                        margin:0 auto 10px;
                    ">{num}</div>
                    <div style="font-weight:700;color:#1F3864;font-size:14px;">{title}</div>
                    <div style="color:#595959;font-size:12px;margin-top:4px;">{desc}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown("---")
    st.info(
        "👈 **Get started!** Click **Financial Profile** in the sidebar to begin your analysis. "
        "Use **Load Sample Data** to see a pre-filled example instantly."
    )


def render_analysis_page() -> None:
    """Financial Health Analysis page."""
    profile = st.session_state.get("profile")
    if not profile:
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
        st.info("📋 Please complete your **Financial Profile** first.")
        return
    if not metrics:
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
        st.info("📋 Please complete your profile and view the **Health Analysis** first.")
        return

    if not st.session_state.get("advice"):
        with st.spinner("🤖 Generating your personalised AI financial advice... (may take a few seconds)"):
            advice = generate_advice(profile, metrics, goals)
            st.session_state["advice"] = advice
            st.session_state["current_step"] = max(st.session_state["current_step"], 4)

    render_advice_sections(st.session_state["advice"])

    # Regenerate button
    if st.button("🔄 Regenerate AI Advice", help="Generate fresh advice from Gemini"):
        st.session_state["advice"] = None
        st.rerun()


def render_dashboard_page() -> None:
    """Visualisation Dashboard page."""
    profile = st.session_state.get("profile")
    metrics = st.session_state.get("metrics")
    goals = st.session_state.get("goals") or []
    # Bug 5 fix: .get("advice", {}) returns None if the key exists but is None
    # (e.g. after clearing advice for regeneration). Use `or {}` to coerce both
    # missing-key and explicit-None cases to an empty dict.
    advice = st.session_state.get("advice") or {}

    if not profile or not metrics:
        st.info("📋 Please complete your profile and view the **Health Analysis** first.")
        return

    if not st.session_state.get("charts"):
        with st.spinner("📊 Generating your visualisation dashboard..."):
            charts = generate_charts(profile, metrics, goals, advice or {})
            st.session_state["charts"] = charts
            st.session_state["current_step"] = max(st.session_state["current_step"], 5)

    render_dashboard(profile, metrics, goals, st.session_state["charts"])

    # Refresh charts button
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

    st.markdown(
        """
        <h2 style='color:#1F3864;margin-bottom:4px;'>📄 Export Financial Report</h2>
        <p style='color:#595959;'>Download a professional PDF report with all analysis and recommendations.</p>
        """,
        unsafe_allow_html=True,
    )

    if not profile:
        st.info("📋 Please complete your **Financial Profile** first.")
        return

    if not metrics:
        st.info("📊 Please complete the **Health Analysis** step first.")
        return

    if not advice:
        st.warning(
            "⚠️ AI advice has not been generated yet. The report will use rule-based guidance. "
            "Visit **AI Advice** to generate personalised recommendations first."
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


# ── Sidebar ───────────────────────────────────────────────────────────────────

def render_sidebar() -> str:
    """Render the navigation sidebar. Returns selected page name."""
    with st.sidebar:
        st.markdown(
            """
            <div style="text-align:center;padding:16px 0 8px;">
                <div style="font-size:40px;">💰</div>
                <div style="font-size:18px;font-weight:700;color:white;">AI Financial Advisor</div>
                <div style="font-size:11px;color:rgba(255,255,255,0.7);margin-top:2px;">v1.0.0</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.divider()

        # Profile status badge
        profile = st.session_state.get("profile")
        if profile:
            st.markdown(
                f"""
                <div style="background:rgba(255,255,255,0.15);border-radius:8px;padding:10px 14px;margin-bottom:12px;">
                    <div style="font-size:12px;color:rgba(255,255,255,0.7);">CURRENT PROFILE</div>
                    <div style="font-size:15px;font-weight:700;color:white;">{profile.name}</div>
                    <div style="font-size:11px;color:rgba(255,255,255,0.6);">
                        {profile.occupation} · {profile.risk_tolerance.value.title()} Risk
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

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
        st.divider()
        st.markdown("<div style='color:rgba(255,255,255,0.7);font-size:12px;margin-bottom:4px;'>WORKFLOW PROGRESS</div>", unsafe_allow_html=True)
        st.progress(progress)
        st.markdown(f"<div style='color:white;font-size:11px;'>Step {step} of 6 complete</div>", unsafe_allow_html=True)

        st.divider()
        st.caption("⚠️ Educational use only. Not professional financial advice.")

    return page


# ── Main ──────────────────────────────────────────────────────────────────────

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
