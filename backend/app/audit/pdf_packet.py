"""ReportLab PDF audit packet generation."""

import io
from datetime import datetime, timezone

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch, cm
from reportlab.lib.colors import HexColor
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    HRFlowable,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT


EMERALD = HexColor("#10b981")
RED = HexColor("#dc2626")
AMBER = HexColor("#f59e0b")
ZINC_800 = HexColor("#27272a")
ZINC_200 = HexColor("#e4e4e7")
WHITE = HexColor("#ffffff")


def generate_audit_pdf(seal_packet: dict) -> bytes:
    """Generate a PDF audit packet from a seal packet dict."""
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "Title2", parent=styles["Title"], fontSize=20, textColor=ZINC_800
    )
    heading_style = ParagraphStyle(
        "Heading2b", parent=styles["Heading2"], textColor=ZINC_800
    )
    body_style = styles["BodyText"]
    small_style = ParagraphStyle(
        "Small", parent=body_style, fontSize=8, textColor=HexColor("#71717a")
    )
    seal_style = ParagraphStyle(
        "Seal",
        parent=body_style,
        fontSize=7,
        fontName="Courier",
        textColor=HexColor("#52525b"),
    )

    story = []

    # Header
    story.append(Paragraph("GHOSTGUARD SEALED AUDIT PACKET", title_style))
    story.append(Spacer(1, 0.3 * inch))

    meta = seal_packet
    story.append(Paragraph(f"<b>Company:</b> {meta.get('company', 'N/A')}", body_style))
    story.append(Paragraph(f"<b>Period:</b> {meta.get('period', 'N/A')}", body_style))
    story.append(
        Paragraph(f"<b>Generated:</b> {meta.get('generated_at', 'N/A')}", body_style)
    )
    story.append(
        Paragraph(f"<b>Generator:</b> {meta.get('generator', 'N/A')}", body_style)
    )
    story.append(Spacer(1, 0.2 * inch))

    # Summary
    story.append(HRFlowable(width="100%", thickness=1, color=ZINC_200))
    story.append(Spacer(1, 0.15 * inch))
    story.append(Paragraph("SUMMARY", heading_style))
    story.append(
        Paragraph(
            f"Anomalies detected: <b>{meta.get('anomaly_count', 0)}</b>", body_style
        )
    )
    story.append(
        Paragraph(
            f"Audit events recorded: <b>{meta.get('audit_event_count', 0)}</b>",
            body_style,
        )
    )
    story.append(Spacer(1, 0.2 * inch))

    # Anomalies table
    anomalies = meta.get("anomalies", [])
    if anomalies:
        story.append(Paragraph("ANOMALIES", heading_style))
        table_data = [["ID", "Employee", "Verdict", "Score", "Explanation"]]
        for a in anomalies:
            verdict = a.get("verdict", "")
            explanation = a.get("explanation", "")
            if len(explanation) > 80:
                explanation = explanation[:77] + "..."
            table_data.append(
                [
                    a.get("anomaly_id", ""),
                    a.get("employee_name", ""),
                    verdict,
                    str(a.get("total_score", 0)),
                    Paragraph(explanation, small_style),
                ]
            )

        t = Table(
            table_data, colWidths=[1.2 * cm, 3.5 * cm, 1.8 * cm, 1.2 * cm, 8 * cm]
        )
        verdict_colors = []
        for i, row in enumerate(table_data):
            if i == 0:
                continue
            v = row[2]
            if v == "BLOCK":
                verdict_colors.append(("TEXTCOLOR", (2, i), (2, i), RED))
            elif v == "FLAG":
                verdict_colors.append(("TEXTCOLOR", (2, i), (2, i), AMBER))
            else:
                verdict_colors.append(("TEXTCOLOR", (2, i), (2, i), EMERALD))

        t.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), ZINC_800),
                    ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
                    ("FONTSIZE", (0, 0), (-1, -1), 8),
                    ("GRID", (0, 0), (-1, -1), 0.5, ZINC_200),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ]
                + verdict_colors
            )
        )
        story.append(t)
        story.append(Spacer(1, 0.3 * inch))

    # Seal
    story.append(HRFlowable(width="100%", thickness=2, color=EMERALD))
    story.append(Spacer(1, 0.15 * inch))
    story.append(Paragraph("TAMPER-PROOF SEAL", heading_style))
    story.append(Paragraph(f"Chain hash: {meta.get('chain_hash', 'N/A')}", seal_style))
    story.append(Paragraph(f"Packet seal: {meta.get('seal', 'N/A')}", seal_style))
    story.append(Spacer(1, 0.1 * inch))
    story.append(
        Paragraph(
            "This audit packet is sealed with SHA-256. Any modification to the data "
            "will invalidate the seal. The chain hash links to all prior audit events.",
            small_style,
        )
    )

    doc.build(story)
    return buf.getvalue()
