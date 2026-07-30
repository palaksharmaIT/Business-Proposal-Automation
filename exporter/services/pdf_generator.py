import io
from datetime import datetime
from django.core.files.base import ContentFile

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
)
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY


def generate_proposal_pdf(proposal):
    """
    Builds a professional PDF for the proposal using ReportLab
    and saves it to proposal.generated_pdf.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        topMargin=2.2 * cm, bottomMargin=2 * cm,
        leftMargin=2 * cm, rightMargin=2 * cm,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('TitleStyle', parent=styles['Title'], fontSize=20, textColor=colors.HexColor('#2c3e50'))
    subtitle_style = ParagraphStyle('SubtitleStyle', parent=styles['Normal'], fontSize=10, textColor=colors.HexColor('#777777'), alignment=TA_CENTER)
    heading_style = ParagraphStyle('HeadingStyle', parent=styles['Heading2'], fontSize=13, textColor=colors.HexColor('#2c3e50'), spaceBefore=14, spaceAfter=6)
    body_style = ParagraphStyle('BodyStyle', parent=styles['Normal'], fontSize=10, leading=15, alignment=TA_JUSTIFY)

    elements = []

    # Header
    elements.append(Paragraph("Business Proposal", title_style))
    elements.append(Paragraph(proposal.title or "", subtitle_style))
    elements.append(Paragraph(f"Prepared on {datetime.now().strftime('%B %d, %Y')}", subtitle_style))
    elements.append(Spacer(1, 16))

    # Summary box (cost / timeline / status)
    summary_data = [
        ["Estimated Cost", "Estimated Timeline", "Status"],
        [f"${proposal.estimated_cost or '-'}", f"{proposal.estimated_timeline_weeks or '-'} weeks", proposal.status],
    ]
    summary_table = Table(summary_data, colWidths=[5.5 * cm, 5.5 * cm, 5.5 * cm])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f4f6f7')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('FONTNAME', (0, 1), (-1, 1), 'Helvetica-Bold'),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#dddddd')),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    elements.append(summary_table)
    elements.append(Spacer(1, 18))

    def add_section(title, text):
        elements.append(Paragraph(title, heading_style))
        safe_text = (text or "").replace('\n', '<br/>')
        elements.append(Paragraph(safe_text, body_style))

    add_section("Executive Summary", proposal.executive_summary)
    add_section("Scope of Work", proposal.scope_of_work)
    add_section("Technology Stack", proposal.technology_stack)
    add_section("Deliverables", proposal.deliverables)

    # Cost breakdown table
    if proposal.cost_breakdown:
        elements.append(Paragraph("Cost Breakdown", heading_style))
        cost_data = [["Item", "Cost (USD)"]]
        for key, value in proposal.cost_breakdown.items():
            cost_data.append([str(key), f"${value}"])
        cost_data.append(["Total Estimated Cost", f"${proposal.estimated_cost}"])

        cost_table = Table(cost_data, colWidths=[11 * cm, 5 * cm])
        cost_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f4f6f7')),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#f4f6f7')),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#dddddd')),
            ('FONTSIZE', (0, 0), (-1, -1), 9.5),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ]))
        elements.append(cost_table)
        elements.append(Spacer(1, 12))

    # Timeline breakdown table
    if proposal.timeline_breakdown:
        elements.append(Paragraph("Timeline Breakdown", heading_style))
        timeline_data = [["Phase / Feature", "Duration (weeks)"]]
        for key, value in proposal.timeline_breakdown.items():
            timeline_data.append([str(key), str(value)])
        timeline_data.append(["Total Estimated Timeline", f"{proposal.estimated_timeline_weeks} weeks"])

        timeline_table = Table(timeline_data, colWidths=[11 * cm, 5 * cm])
        timeline_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f4f6f7')),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#f4f6f7')),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#dddddd')),
            ('FONTSIZE', (0, 0), (-1, -1), 9.5),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ]))
        elements.append(timeline_table)
        elements.append(Spacer(1, 12))

    add_section("Terms & Conditions", proposal.terms_and_conditions)

    elements.append(Spacer(1, 20))
    footer_style = ParagraphStyle('Footer', parent=styles['Normal'], fontSize=8, textColor=colors.HexColor('#999999'), alignment=TA_CENTER)
    elements.append(Paragraph("This proposal is confidential and intended solely for the recipient. Generated by AI Business Proposal Assistant.", footer_style))

    doc.build(elements)

    pdf_bytes = buffer.getvalue()
    buffer.close()

    filename = f"proposal_{proposal.id}_{(proposal.title or 'proposal')[:30].replace(' ', '_')}.pdf"
    proposal.generated_pdf.save(filename, ContentFile(pdf_bytes), save=True)

    return proposal.generated_pdf.path