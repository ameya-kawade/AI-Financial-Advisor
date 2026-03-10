from typing import Dict, Optional

from pydantic import BaseModel, Field


class GoalPlan(BaseModel):
    """Investment plan computed for a single financial goal."""

    goal_name: str
    target_amount: float = Field(gt=0)
    target_months: int = Field(ge=1, le=480)
    inflation_adjusted_target: float
    required_monthly_saving: float
    feasibility_score: float          # 0–100+ ( >100 = surplus capacity)
    feasibility_status: str           # 'infeasible' | 'tight' | 'feasible'
    adjusted_timeline_months: Optional[int] = None  # alternate timeline if infeasible
    allocation_breakdown: Dict[str, int]              # {"Equity SIP": 45, ...}
    priority_score: float                             # higher = more urgent
    expected_return_rate: float                       # annual % based on risk profile
