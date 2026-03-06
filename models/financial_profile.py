"""
FinancialProfile Pydantic data model.
"""

from __future__ import annotations

import re
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator, model_validator


class RiskTolerance(str, Enum):
    CONSERVATIVE = "conservative"
    MODERATE = "moderate"
    AGGRESSIVE = "aggressive"


class InvestmentHorizon(str, Enum):
    SHORT = "short"    # < 3 years
    MEDIUM = "medium"  # 3–7 years
    LONG = "long"      # > 7 years


class GoalInput(BaseModel):
    """Individual financial goal with target amount and timeline."""
    goal_name: str = Field(min_length=1, max_length=100)
    target_amount: float = Field(gt=0, description="Target amount in INR")
    target_months: int = Field(ge=1, le=480, description="Timeline in months")


class FinancialProfile(BaseModel):
    """Complete validated financial profile for a user."""
    name: str = Field(min_length=2, max_length=100)
    age: int = Field(ge=16, le=100)
    occupation: str = Field(default="Salaried")
    monthly_income: float = Field(ge=0, description="Monthly gross income in INR")
    monthly_expenses: float = Field(ge=0, description="Monthly living expenses in INR")
    current_savings: float = Field(ge=0, description="Total liquid savings in INR")
    monthly_debt_repayments: float = Field(ge=0, description="Monthly EMI/loan payments in INR")
    total_debt_outstanding: float = Field(ge=0, default=0.0, description="Total outstanding debt in INR")
    risk_tolerance: RiskTolerance
    investment_horizon: InvestmentHorizon
    financial_goals: List[GoalInput] = Field(default_factory=list)
    existing_investments: List[str] = Field(default_factory=list)
    currency_preference: str = Field(default="INR")

    @field_validator("name")
    @classmethod
    def name_alphanumeric(cls, v: str) -> str:
        """Sanitise name: only alphabetic chars and spaces."""
        sanitised = re.sub(r"[^a-zA-Z \-']", "", v).strip()
        if len(sanitised) < 2:
            raise ValueError("Name must contain at least 2 alphabetic characters.")
        return sanitised[:50]  # Hard cap for prompt injection safety

    @field_validator("monthly_expenses")
    @classmethod
    def expenses_reasonable(cls, v: float) -> float:
        return v

    @model_validator(mode="after")
    def check_financial_sanity(self) -> "FinancialProfile":
        if self.monthly_income > 0 and self.monthly_expenses > self.monthly_income * 2:
            raise ValueError("Monthly expenses seem unusually high relative to income.")
        return self
