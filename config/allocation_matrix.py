"""
Risk-based asset allocation matrix.
Keys: (horizon, risk_tolerance) → allocation percentages dict.
"""

# Horizon keys: 'short', 'medium', 'long'
# Risk keys: 'conservative', 'moderate', 'aggressive'

ALLOCATION_MATRIX = {
    ("short", "conservative"): {
        "Equity SIP": 10,
        "Debt/Bonds": 40,
        "Gold ETF": 10,
        "PPF/NPS": 20,
        "Liquid Fund": 10,
        "FD Reserve": 10,
    },
    ("short", "moderate"): {
        "Equity SIP": 20,
        "Debt/Bonds": 30,
        "Gold ETF": 10,
        "PPF/NPS": 20,
        "Liquid Fund": 10,
        "FD Reserve": 10,
    },
    ("short", "aggressive"): {
        "Equity SIP": 30,
        "Debt/Bonds": 20,
        "Gold ETF": 10,
        "PPF/NPS": 15,
        "Liquid Fund": 15,
        "FD Reserve": 10,
    },
    ("medium", "conservative"): {
        "Equity SIP": 30,
        "Debt/Bonds": 30,
        "Gold ETF": 10,
        "PPF/NPS": 20,
        "Liquid Fund": 5,
        "FD Reserve": 5,
    },
    ("medium", "moderate"): {
        "Equity SIP": 45,
        "Debt/Bonds": 25,
        "Gold ETF": 10,
        "PPF/NPS": 15,
        "Liquid Fund": 3,
        "FD Reserve": 2,
    },
    ("medium", "aggressive"): {
        "Equity SIP": 60,
        "Debt/Bonds": 15,
        "Gold ETF": 10,
        "PPF/NPS": 10,
        "Liquid Fund": 3,
        "FD Reserve": 2,
    },
    ("long", "conservative"): {
        "Equity SIP": 40,
        "Debt/Bonds": 25,
        "Gold ETF": 15,
        "PPF/NPS": 15,
        "Liquid Fund": 3,
        "FD Reserve": 2,
    },
    ("long", "moderate"): {
        "Equity SIP": 60,
        "Debt/Bonds": 15,
        "Gold ETF": 10,
        "PPF/NPS": 10,
        "Liquid Fund": 3,
        "FD Reserve": 2,
    },
    ("long", "aggressive"): {
        "Equity SIP": 75,
        "Debt/Bonds": 10,
        "Gold ETF": 5,
        "PPF/NPS": 7,
        "Liquid Fund": 2,
        "FD Reserve": 1,
    },
}


def get_allocation(horizon: str, risk_tolerance: str) -> dict:
    """
    Retrieve asset allocation percentages for given horizon and risk profile.

    Args:
        horizon: 'short', 'medium', or 'long'
        risk_tolerance: 'conservative', 'moderate', or 'aggressive'

    Returns:
        Dict of asset class → percentage allocations.
    """
    key = (horizon.lower(), risk_tolerance.lower())
    return ALLOCATION_MATRIX.get(key, ALLOCATION_MATRIX[("medium", "moderate")])
