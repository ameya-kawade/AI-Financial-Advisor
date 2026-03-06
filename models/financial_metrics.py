"""
FinancialMetrics Pydantic data model.
"""

from typing import Optional

from pydantic import BaseModel, Field


class FinancialMetrics(BaseModel):
    """All computed financial health metrics for a user profile."""

    # Core computed values
    net_monthly_surplus: float
    savings_rate_pct: float
    expense_ratio_pct: float
    dti_ratio_pct: float
    emergency_fund_months: float
    financial_health_score: int = Field(ge=0, le=100)
    investable_surplus: float
    debt_payoff_months: Optional[int] = None

    # Status labels
    savings_rate_status: str   # 'poor' | 'moderate' | 'healthy'
    dti_status: str            # 'low' | 'manageable' | 'high'
    ef_status: str             # 'insufficient' | 'adequate' | 'strong'
    expense_ratio_status: str  # 'excellent' | 'good' | 'high'
    overall_status: str        # 'critical' | 'needs_work' | 'good' | 'excellent'
