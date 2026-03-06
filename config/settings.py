"""
App-wide constants and configuration settings.
"""

import os

# === App Metadata ===
APP_TITLE = "AI Financial Advisor"
APP_ICON = "💰"
APP_VERSION = "1.0.0"
APP_FOOTER = (
    "⚠️ This tool provides educational financial guidance only. "
    "Consult a qualified CFP for personalised advice."
)

# === AI Configuration ===
GEMINI_MODEL = "gemini-2.0-flash"
GEMINI_TEMPERATURE = 0.3
GEMINI_TOP_P = 0.95
GEMINI_TOP_K = 40
GEMINI_MAX_OUTPUT_TOKENS = 4096

# === LLM Provider Configuration ===
# Options: "gemini" | "ollama"
# Override via MODEL_PROVIDER environment variable in .env
MODEL_PROVIDER: str = os.getenv("MODEL_PROVIDER", "gemini")

# Ollama local inference settings
OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL: str = os.getenv(
    "OLLAMA_MODEL", "qcwind/qwen2.5-7B-instruct-Q4_K_M:latest"
)
# 300s timeout — 7B Q4 models on CPU take 3-5 min for ~800 token output.
# The previous 120s was hitting Ollama's own internal generation deadline.
OLLAMA_TIMEOUT: int = 300

# === Financial Constants ===
INFLATION_RATE = 0.06          # 6% annual default
EMERGENCY_BUFFER_RATE = 0.10  # 10% of net surplus reserved for emergencies

# === Expected Annual Return Rates by Risk Profile (%) ===
EXPECTED_RETURN_RATES = {
    "conservative": 7.0,
    "moderate": 10.0,
    "aggressive": 12.0,
}

# === Financial Health Score Thresholds ===
SCORE_CRITICAL_THRESHOLD = 40
SCORE_NEEDS_WORK_THRESHOLD = 60
SCORE_GOOD_THRESHOLD = 80

# === Benchmark Thresholds ===
SAVINGS_RATE_POOR = 10.0
SAVINGS_RATE_HEALTHY = 20.0
EXPENSE_RATIO_EXCELLENT = 50.0
EXPENSE_RATIO_HIGH = 70.0
DTI_LOW = 15.0
DTI_HIGH = 36.0
EF_INSUFFICIENT = 3.0
EF_ADEQUATE = 6.0

# === Design Tokens ===
COLOR_PRIMARY = "#1F3864"
COLOR_ACCENT = "#2E75B6"
COLOR_SUCCESS = "#1E7145"
COLOR_WARNING = "#F5A623"
COLOR_DANGER = "#C0392B"
COLOR_BACKGROUND = "#F8FAFD"
COLOR_CARD_BG = "#EBF2FA"

# === Sample Profile (Priya) ===
# Bug #2 fixed: existing_investments was ["MF"] — not in INVESTMENT_OPTIONS.
# Changed to ["Mutual Funds"] to match the multiselect widget options.
SAMPLE_PROFILE = {
    "name": "Priya Sharma",
    "age": 32,
    "occupation": "Salaried",
    "monthly_income": 90000.0,
    "monthly_expenses": 45000.0,
    "monthly_debt_repayments": 12000.0,
    "total_debt_outstanding": 360000.0,
    "current_savings": 150000.0,
    "risk_tolerance": "Moderate",
    "investment_horizon": "Long (>7yr)",
    "financial_goals": ["Home Purchase", "Retirement"],
    "goal_targets": {
        "Home Purchase": {"amount": 3000000.0, "months": 60},
        "Retirement": {"amount": 20000000.0, "months": 300},
    },
    "existing_investments": ["Mutual Funds"],  # Fixed: was "MF", not in INVESTMENT_OPTIONS
    "currency_preference": "INR",
}
