"""PDF report generator using ReportLab."""
from pathlib import Path
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
)


def generate_pdf_report(output_path: Path, summary):
    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("Title", parent=styles["Heading1"], fontSize=20, textColor=colors.HexColor("#6366f1"))
    h2_style = ParagraphStyle("H2", parent=styles["Heading2"], fontSize=14, textColor=colors.HexColor("#1e293b"))
    body_style = styles["BodyText"]
    body_style.fontSize = 10

    story = []

    # Header
    story.append(Paragraph("XenoGuard AI", title_style))
    story.append(Paragraph("Transaction Validation Report", h2_style))
    story.append(Paragraph(f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}", body_style))
    story.append(Paragraph(f"Session ID: {summary.session_id}", body_style))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#e2e8f0")))
    story.append(Spacer(1, 0.3 * cm))

    # Health Score
    score = float(summary.health_score or 0)
    score_color = colors.HexColor("#16a34a") if score >= 80 else (
        colors.HexColor("#d97706") if score >= 50 else colors.HexColor("#dc2626")
    )
    story.append(Paragraph(f"Dataset Health Score: <font color='#{score_color.hexval()[2:]}' size='18'><b>{score:.1f}/100</b></font>", body_style))
    story.append(Spacer(1, 0.3 * cm))

    # Summary table
    summary_data = [
        ["Metric", "Value"],
        ["Total Records", str(summary.total_rows)],
        ["Valid Records", str(summary.valid_rows)],
        ["Invalid Records", str(summary.invalid_rows)],
        ["Auto-Fixed Records", str(summary.fixed_rows)],
    ]
    t = Table(summary_data, colWidths=[8 * cm, 6 * cm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#6366f1")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
        ("ALIGN", (1, 0), (1, -1), "CENTER"),
    ]))
    story.append(t)
    story.append(Spacer(1, 0.5 * cm))

    # Error breakdown
    story.append(Paragraph("Error Breakdown by Category", h2_style))
    eb = summary.error_breakdown or {}
    if eb:
        eb_data = [["Category", "Count"]] + [[k, str(v)] for k, v in sorted(eb.items(), key=lambda x: -x[1])]
        t2 = Table(eb_data, colWidths=[8 * cm, 6 * cm])
        t2.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#334155")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
        ]))
        story.append(t2)
    story.append(Spacer(1, 0.5 * cm))

    # AI Insights
    story.append(Paragraph("AI-Generated Insights", h2_style))
    insights = summary.ai_insights or []
    for insight in insights:
        if isinstance(insight, dict):
            severity = insight.get("severity", "INFO")
            title = insight.get("title", "")
            body = insight.get("body", "")
            icon = {"CRITICAL": "🔴", "WARNING": "⚠️", "INFO": "💡"}.get(severity, "•")
            story.append(Paragraph(f"<b>{icon} {title}</b>", body_style))
            story.append(Paragraph(body, body_style))
            story.append(Spacer(1, 0.2 * cm))
        else:
            story.append(Paragraph(f"• {insight}", body_style))

    doc.build(story)
