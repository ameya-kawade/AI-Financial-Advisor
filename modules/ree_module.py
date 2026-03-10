"""Report & Export Engine (REE) module."""

from __future__ import annotations

import io
from datetime import date
from typing import Any

from models.financial_metrics import FinancialMetrics
from models.financial_profile import FinancialProfile
from models.goal_plan import GoalPlan
from utils.formatters import format_inr, format_months, format_pct, format_score_label, score_to_color


# Colour constants (RGB tuples 0-1)
_NAVY = (0.122, 0.220, 0.392)
_BLUE = (0.180, 0.459, 0.714)
_GREEN = (0.118, 0.443, 0.271)
_AMBER = (0.961, 0.651, 0.137)
_RED = (0.753, 0.224, 0.169)
_LIGHT_BG = (0.922, 0.949, 0.980)
_WHITE = (1, 1, 1)
_GREY = (0.353, 0.353, 0.353)


def generate_report(
    profile: FinancialProfile,
    metrics: FinancialMetrics,
    goals: list[GoalPlan],
    advice: dict,
    charts: dict[str, Any],
) -> io.BytesIO:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.platypus import (
        SimpleDocTemplate,
        Paragraph,
        Spacer,
        Table,
        TableStyle,
        HRFlowable,
        PageBreak,
        Image,
    )
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=2.5 * cm,
        bottomMargin=2 * cm,
    )

    styles = _build_styles()
    story = []


    story.append(Spacer(1, 3 * cm))
    story.append(Paragraph("💰 AI Financial Advisor", styles["cover_title"]))
    story.append(Spacer(1, 0.5 * cm))
    story.append(Paragraph("Personalised Financial Report", styles["cover_subtitle"]))
    story.append(Spacer(1, 1 * cm))
    story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor("#2E75B6")))
    story.append(Spacer(1, 0.8 * cm))

    # Score badge area
    score = metrics.financial_health_score
    score_label = format_score_label(score)
    story.append(Paragraph(f"Prepared for: <b>{profile.name}</b>", styles["cover_info"]))
    story.append(Paragraph(f"Date: {date.today().strftime('%d %B %Y')}", styles["cover_info"]))
    story.append(Paragraph(f"Financial Health Score: <b>{score}/100 — {score_label}</b>", styles["cover_info"]))
    story.append(Spacer(1, 2 * cm))
    story.append(Paragraph(
        "⚠️ This report is for educational purposes only. Please consult a SEBI-registered "
        "financial advisor before making investment decisions.",
        styles["disclaimer"],
    ))
    story.append(PageBreak())


    story.append(Paragraph("Executive Summary", styles["section_title"]))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#2E75B6")))
    story.append(Spacer(1, 0.3 * cm))

    summary_text = advice.get("financial_health_summary", "")
    summary_text = _clean_text(summary_text)
    story.append(Paragraph(summary_text, styles["body"]))
    story.append(Spacer(1, 0.5 * cm))


    story.append(Paragraph("Financial Health Metrics", styles["section_title"]))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#2E75B6")))
    story.append(Spacer(1, 0.3 * cm))

    metrics_data = [
        ["Metric", "Your Value", "Benchmark", "Status"],
        ["Net Monthly Surplus", format_inr(metrics.net_monthly_surplus), "> ₹0",
         "✓" if metrics.net_monthly_surplus >= 0 else "✗"],
        ["Savings Rate", format_pct(metrics.savings_rate_pct), "≥ 20%",
         "✓" if metrics.savings_rate_pct >= 20 else ("≈" if metrics.savings_rate_pct >= 10 else "✗")],
        ["Expense Ratio", format_pct(metrics.expense_ratio_pct), "< 50%",
         "✓" if metrics.expense_ratio_pct < 50 else "✗"],
        ["Debt-to-Income (DTI)", format_pct(metrics.dti_ratio_pct), "< 15%",
         "✓" if metrics.dti_ratio_pct < 15 else "✗"],
        ["Emergency Fund", f"{metrics.emergency_fund_months:.1f} months", "3-6 months",
         "✓" if metrics.emergency_fund_months >= 3 else "✗"],
        ["Investable Surplus", format_inr(metrics.investable_surplus), "> ₹0",
         "✓" if metrics.investable_surplus > 0 else "✗"],
        ["Debt Payoff Timeline",
         format_months(metrics.debt_payoff_months) if metrics.debt_payoff_months else "No Debt",
         "< 36 months", ""],
        ["Health Score", f"{metrics.financial_health_score}/100",
         "60+ = Good", format_score_label(metrics.financial_health_score)],
    ]

    t = Table(metrics_data, colWidths=[5 * cm, 3.5 * cm, 3.5 * cm, 3 * cm])
    t.setStyle(_metrics_table_style())
    story.append(t)
    story.append(Spacer(1, 0.5 * cm))


    story.append(PageBreak())
    story.append(Paragraph("AI-Powered Recommendations", styles["section_title"]))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#2E75B6")))
    story.append(Spacer(1, 0.3 * cm))

    advice_sections = [
        ("Spending Optimisation", "spending_optimisation"),
        ("Savings Acceleration Strategy", "savings_acceleration"),
        ("Debt Management Roadmap", "debt_management_roadmap"),
    ]
    for title, key in advice_sections:
        story.append(Paragraph(title, styles["subsection_title"]))
        content = advice.get(key, "")
        if isinstance(content, list):
            for item in content:
                story.append(Paragraph(f"• {_clean_text(str(item))}", styles["body"]))
        else:
            story.append(Paragraph(_clean_text(str(content)), styles["body"]))
        story.append(Spacer(1, 0.3 * cm))

    # Investment Recommendations
    story.append(Paragraph("Investment Portfolio Recommendations", styles["subsection_title"]))
    inv = advice.get("investment_recommendations", {})
    if isinstance(inv, dict):
        story.append(Paragraph(_clean_text(str(inv.get("overview", ""))), styles["body"]))
        allocations = inv.get("allocations", [])
        if allocations:
            alloc_data = [["Instrument", "% Allocation", "Rationale"]]
            for a in allocations:
                alloc_data.append([
                    str(a.get("instrument", "")),
                    f"{a.get('percentage', 0)}%",
                    _clean_text(str(a.get("rationale", ""))),
                ])
            at = Table(alloc_data, colWidths=[4.5 * cm, 2.5 * cm, 8 * cm])
            at.setStyle(_basic_table_style())
            story.append(at)
    story.append(Spacer(1, 0.3 * cm))


    if goals:
        story.append(PageBreak())
        story.append(Paragraph("Goal Investment Roadmaps", styles["section_title"]))
        story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#2E75B6")))
        story.append(Spacer(1, 0.3 * cm))

        goal_data = [["Goal", "Target", "Timeline", "Monthly Req.", "Status"]]
        for g in goals:
            goal_data.append([
                g.goal_name,
                format_inr(g.target_amount, compact=True),
                format_months(g.target_months),
                format_inr(g.required_monthly_saving, compact=True),
                g.feasibility_status.title(),
            ])
        gt = Table(goal_data, colWidths=[4 * cm, 3 * cm, 3 * cm, 3.5 * cm, 2.5 * cm])
        gt.setStyle(_basic_table_style())
        story.append(gt)
        story.append(Spacer(1, 0.3 * cm))

        # Goal roadmaps from AI
        roadmaps = advice.get("goal_roadmaps", [])
        for roadmap in roadmaps:
            if isinstance(roadmap, dict):
                story.append(Paragraph(f"▶ {roadmap.get('goal_name', '')}", styles["subsection_title"]))
                story.append(Paragraph(_clean_text(roadmap.get("plan", "")), styles["body"]))
                for m in roadmap.get("milestones", []):
                    story.append(Paragraph(f"  ✓ {_clean_text(str(m))}", styles["body"]))
                story.append(Spacer(1, 0.2 * cm))


    story.append(PageBreak())
    story.append(Paragraph("30-60-90 Day Action Plan", styles["section_title"]))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#2E75B6")))
    story.append(Spacer(1, 0.3 * cm))

    action = advice.get("action_plan", {})
    if isinstance(action, dict):
        action_data = [["30 Days", "60 Days", "90 Days"]]
        days_30 = action.get("days_30", [])
        days_60 = action.get("days_60", [])
        days_90 = action.get("days_90", [])
        max_len = max(len(days_30), len(days_60), len(days_90), 1)
        for i in range(max_len):
            action_data.append([
                f"☐ {_clean_text(str(days_30[i]))}" if i < len(days_30) else "",
                f"☐ {_clean_text(str(days_60[i]))}" if i < len(days_60) else "",
                f"☐ {_clean_text(str(days_90[i]))}" if i < len(days_90) else "",
            ])
        at = Table(action_data, colWidths=[5 * cm, 5 * cm, 5 * cm])
        at.setStyle(_basic_table_style())
        story.append(at)


    story.append(Spacer(1, 1 * cm))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#CCCCCC")))
    story.append(Spacer(1, 0.3 * cm))
    story.append(Paragraph("Disclaimer", styles["subsection_title"]))
    disclaimer_text = advice.get("disclaimer", (
        "This report is generated by an AI system for educational purposes only and does not "
        "constitute professional financial advice. All calculations use assumed return rates "
        "and actual returns may vary. Consult a SEBI-registered financial advisor before making "
        "significant investment decisions."
    ))
    story.append(Paragraph(_clean_text(str(disclaimer_text)), styles["disclaimer"]))

    doc.build(story)
    buf.seek(0)
    return buf




def _build_styles() -> dict:
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY

    return {
        "cover_title": ParagraphStyle(
            "cover_title",
            fontSize=28,
            fontName="Helvetica-Bold",
            textColor=colors.HexColor("#1F3864"),
            alignment=TA_CENTER,
            spaceAfter=8,
        ),
        "cover_subtitle": ParagraphStyle(
            "cover_subtitle",
            fontSize=16,
            fontName="Helvetica",
            textColor=colors.HexColor("#2E75B6"),
            alignment=TA_CENTER,
            spaceAfter=6,
        ),
        "cover_info": ParagraphStyle(
            "cover_info",
            fontSize=12,
            fontName="Helvetica",
            textColor=colors.HexColor("#1F3864"),
            alignment=TA_CENTER,
            spaceAfter=4,
        ),
        "section_title": ParagraphStyle(
            "section_title",
            fontSize=16,
            fontName="Helvetica-Bold",
            textColor=colors.HexColor("#1F3864"),
            spaceBefore=12,
            spaceAfter=4,
        ),
        "subsection_title": ParagraphStyle(
            "subsection_title",
            fontSize=13,
            fontName="Helvetica-Bold",
            textColor=colors.HexColor("#2E75B6"),
            spaceBefore=8,
            spaceAfter=4,
        ),
        "body": ParagraphStyle(
            "body",
            fontSize=10,
            fontName="Helvetica",
            textColor=colors.HexColor("#333333"),
            alignment=TA_JUSTIFY,
            spaceAfter=4,
            leading=14,
        ),
        "disclaimer": ParagraphStyle(
            "disclaimer",
            fontSize=9,
            fontName="Helvetica-Oblique",
            textColor=colors.HexColor("#666666"),
            alignment=TA_JUSTIFY,
            spaceAfter=4,
        ),
    }


def _metrics_table_style():
    from reportlab.lib import colors
    from reportlab.platypus import TableStyle

    return TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1F3864")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#EBF2FA"), colors.white]),
        ("ALIGN", (1, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#BDD7EE")),
        ("PADDING", (0, 0), (-1, -1), 6),
    ])


def _basic_table_style():
    from reportlab.lib import colors
    from reportlab.platypus import TableStyle

    return TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2E75B6")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#F8FAFD"), colors.white]),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CCCCCC")),
        ("PADDING", (0, 0), (-1, -1), 5),
        ("WORDWRAP", (0, 0), (-1, -1), 1),
    ])


def _clean_text(text: str) -> str:
    """Remove markdown formatting for PDF rendering (bold, italics, etc.)."""
    import re
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)   # **bold**
    text = re.sub(r"\*(.+?)\*", r"\1", text)         # *italic*
    text = re.sub(r"#{1,6}\s*", "", text)             # ## headings
    text = re.sub(r"`(.+?)`", r"\1", text)            # `code`
    return text.strip()
