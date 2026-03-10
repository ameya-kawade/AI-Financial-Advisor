import math

import numpy as np


def compute_pmt(future_value: float, months: int, annual_rate_pct: float) -> float:
    if months <= 0:
        return future_value
    r = annual_rate_pct / 12 / 100
    if r == 0:
        return future_value / months
    pmt = future_value * r / ((1 + r) ** months - 1)
    return round(pmt, 2)


def compute_health_score(
    savings_rate: float,
    expense_ratio: float,
    dti: float,
    ef_months: float,
    net_surplus: float,
    income: float,
) -> int:
    sr_score = min(savings_rate / 20.0 * 100, 100.0)

    if expense_ratio <= 50:
        er_score = 100.0
    else:
        er_score = max((1 - (expense_ratio - 50) / 50.0) * 100, 0.0)

    dti_score = max((1 - dti / 36.0) * 100, 0.0)

    ef_score = min(ef_months / 6.0 * 100, 100.0)

    if income > 0:
        surplus_pct = net_surplus / income * 100
        surplus_score = min(max(surplus_pct * 5, 0.0), 100.0)
    else:
        surplus_score = 0.0

    score = (
        sr_score * 0.25
        + er_score * 0.20
        + dti_score * 0.25
        + ef_score * 0.20
        + surplus_score * 0.10
    )
    return max(0, min(100, round(score)))


def compute_inflation_adjusted(
    target: float, years: float, inflation_rate: float = 0.06
) -> float:
    return target * (1 + inflation_rate) ** years


def compute_adjusted_timeline(
    investable_surplus: float, target: float, annual_rate_pct: float
) -> int:
    if investable_surplus <= 0:
        return 480  # Max timeline

    r = annual_rate_pct / 12 / 100
    if r == 0:
        return int(math.ceil(target / investable_surplus))

    try:
        months = math.log(1 + (target * r / investable_surplus)) / math.log(1 + r)
        result = int(math.ceil(months))
        return min(result, 480)
    except (ValueError, ZeroDivisionError):
        return 480


def compute_future_value(monthly_pmt: float, months: int, annual_rate_pct: float) -> float:
    r = annual_rate_pct / 12 / 100
    if r == 0:
        return monthly_pmt * months
    return monthly_pmt * ((1 + r) ** months - 1) / r
