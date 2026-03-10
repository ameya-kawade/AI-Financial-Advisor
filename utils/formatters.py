def format_inr(amount: float, compact: bool = False) -> str:
    if compact:
        abs_amount = abs(amount)
        if abs_amount >= 10_000_000:
            return f"₹{amount / 10_000_000:.2f} Cr"
        elif abs_amount >= 100_000:
            return f"₹{amount / 100_000:.2f} L"
        elif abs_amount >= 1_000:
            return f"₹{amount / 1_000:.1f}K"
        else:
            return f"₹{amount:,.0f}"

    # Full format with Indian grouping
    return f"₹{_indian_format(amount)}"


def _indian_format(amount: float) -> str:
    """Format number with Indian comma placement (2,34,56,789)."""
    formatted = f"{abs(amount):.0f}"
    if len(formatted) <= 3:
        result = formatted
    else:
        last_three = formatted[-3:]
        rest = formatted[:-3]
        # Group remaining digits in twos
        groups = []
        while len(rest) > 2:
            groups.append(rest[-2:])
            rest = rest[:-2]
        if rest:
            groups.append(rest)
        groups.reverse()
        result = ",".join(groups) + "," + last_three

    return f"-{result}" if amount < 0 else result


def format_pct(value: float, decimals: int = 1) -> str:
    """Format a float as a percentage string."""
    return f"{value:.{decimals}f}%"


def format_months(months: int) -> str:
    """Convert months to years + months human-readable string."""
    if months is None:
        return "N/A"
    years = months // 12
    remaining = months % 12
    parts = []
    if years:
        parts.append(f"{years} yr{'s' if years > 1 else ''}")
    if remaining:
        parts.append(f"{remaining} mo")
    return " ".join(parts) if parts else "0 months"


def format_score_label(score: int) -> str:
    """Return status label for a financial health score."""
    if score >= 80:
        return "Excellent"
    elif score >= 60:
        return "Good"
    elif score >= 40:
        return "Needs Work"
    else:
        return "Critical"


def score_to_color(score: int) -> str:
    """Map health score to hex colour code (dark-theme vibrant)."""
    if score >= 80:
        return "#10B981"
    elif score >= 60:
        return "#0EA5E9"
    elif score >= 40:
        return "#F59E0B"
    else:
        return "#EF4444"
