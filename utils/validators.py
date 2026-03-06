"""
Input validation utility functions.
"""

import re
from typing import Any


def is_valid_name(value: str) -> bool:
    """Check if name contains only valid characters."""
    return bool(re.match(r"^[a-zA-Z \-']{2,100}$", value.strip()))


def is_positive_number(value: Any) -> bool:
    """Check if value is a non-negative number."""
    try:
        return float(value) >= 0
    except (TypeError, ValueError):
        return False


def is_valid_age(value: Any) -> bool:
    """Check if age is a valid integer in range 16–100."""
    try:
        age = int(value)
        return 16 <= age <= 100
    except (TypeError, ValueError):
        return False


def is_valid_months(value: Any) -> bool:
    """Check if timeline months is a valid integer 1–480."""
    try:
        m = int(value)
        return 1 <= m <= 480
    except (TypeError, ValueError):
        return False


def sanitise_text(value: str, max_length: int = 200) -> str:
    """
    Strip special characters from user text for prompt safety.
    Keeps alphanumeric chars, spaces, apostrophes, hyphens.
    """
    sanitised = re.sub(r"[^a-zA-Z0-9 \-' ]", "", value)
    return sanitised[:max_length].strip()


def validate_goal_inputs(goals: list) -> list[str]:
    """
    Validate goal inputs list. Returns list of error messages (empty if valid).
    """
    errors = []
    for g in goals:
        if g.get("target_amount", 0) <= 0:
            errors.append(f"Goal '{g.get('goal_name', 'Unknown')}': Target amount must be > 0.")
        if not is_valid_months(g.get("target_months", 0)):
            errors.append(f"Goal '{g.get('goal_name', 'Unknown')}': Timeline must be 1–480 months.")
    return errors
