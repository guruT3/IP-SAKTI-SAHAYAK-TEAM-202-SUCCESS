import os
import sys
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY

def build_pdf(filename="IP_SAKTI_Sahayak_Triangle_Revisions.pdf"):
    doc = SimpleDocTemplate(
        filename,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()
    
    # Custom Palette
    NAVY = colors.HexColor("#0F172A")
    TEAL = colors.HexColor("#0F766E")
    RED_HEADER = colors.HexColor("#991B1B")
    RED_BG = colors.HexColor("#FEF2F2")
    RED_BORDER = colors.HexColor("#FCA5A5")
    GREEN_HEADER = colors.HexColor("#065F46")
    GREEN_BG = colors.HexColor("#ECFDF5")
    GREEN_BORDER = colors.HexColor("#6EE7B7")
    BLUE_BG = colors.HexColor("#EFF6FF")
    BLUE_BORDER = colors.HexColor("#BFDBFE")
    DARK_TEXT = colors.HexColor("#1E293B")
    SUB_TEXT = colors.HexColor("#475569")

    # Custom Typography Styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        textColor=NAVY,
        alignment=TA_LEFT,
        spaceAfter=4
    )
    
    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=11,
        leading=14,
        textColor=TEAL,
        alignment=TA_LEFT,
        spaceAfter=15
    )

    h2_style = ParagraphStyle(
        'SectionH2',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=13,
        leading=16,
        textColor=NAVY,
        spaceBefore=14,
        spaceAfter=8
    )

    body_style = ParagraphStyle(
        'BodyTextCustom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=13.5,
        textColor=DARK_TEXT,
        spaceAfter=6
    )

    body_bold = ParagraphStyle(
        'BodyBoldCustom',
        parent=body_style,
        fontName='Helvetica-Bold'
    )

    cell_style = ParagraphStyle(
        'TableCell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=11.5,
        textColor=DARK_TEXT
    )

    cell_bold = ParagraphStyle(
        'TableCellBold',
        parent=cell_style,
        fontName='Helvetica-Bold'
    )

    cell_header = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=12,
        textColor=colors.white,
        alignment=TA_LEFT
    )

    tier_title = ParagraphStyle(
        'TierTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=13,
        textColor=NAVY
    )

    story = []

    # 1. Header Banner
    story.append(Paragraph("IP-SAKTI SAHAYAK", title_style))
    story.append(Paragraph("Architecture Triangle Diagram — Feature Revision Blueprint (SIH 2026)", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=TEAL, spaceAfter=12))

    # 2. Executive Summary
    summary_text = (
        "<b>Executive Summary:</b> This document provides an authoritative guide on which features "
        "to <b>REMOVE</b> and <b>ADD</b> in the presentation triangle diagram for the <b>IP-SAKTI SAHAYAK</b> system. "
        "The revisions ensure the presentation accurately reflects the implemented hybrid Retrieval-Augmented Generation (RAG) "
        "architecture, the 5-Axis IP Risk Radar, statutory compliance engine, and legal evidence verification pipeline."
    )
    story.append(Paragraph(summary_text, body_style))
    story.append(Spacer(1, 10))

    # 3. Features to REMOVE Section
    story.append(Paragraph("1. Features to REMOVE / REPLACE from Current Diagram", h2_style))
    
    remove_data = [
        [
            Paragraph("Current Item", cell_header),
            Paragraph("Action Required", cell_header),
            Paragraph("Rationale & Project Alignment", cell_header)
        ],
        [
            Paragraph("<b>Human Expert Escalation</b>", cell_style),
            Paragraph("<font color='#BE123C'><b>REMOVE</b></font>", cell_style),
            Paragraph("IP-SAKTI SAHAYAK is a 100% automated AI assistant. Instead of human routing, the system enforces <b>Safe Abstention</b> (refusing to answer when statutory evidence is insufficient).", cell_style)
        ],
        [
            Paragraph("<b>Risk-Aware Guidance</b>", cell_style),
            Paragraph("<font color='#BE123C'><b>REMOVE / REPLACE</b></font>", cell_style),
            Paragraph("Too vague and redundant. Replace this entry with the concrete, flagship <b>5-Axis IP Risk Radar</b> assessment module.", cell_style)
        ],
        [
            Paragraph("<b>Version-Tracked Laws</b>", cell_style),
            Paragraph("<font color='#D97706'><b>RENAME</b></font>", cell_style),
            Paragraph("Rename to <b>Authoritative Source Registry & Regulatory Monitor</b> to accurately reflect the live source prioritisation pipeline (IP India, AYUSH, TKDL, WIPO, NBA).", cell_style)
        ]
    ]

    col_widths_rem = [120, 95, 325]
    t_remove = Table(remove_data, colWidths=col_widths_rem)
    t_remove.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), RED_HEADER),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('GRID', (0, 0), (-1, -1), 0.5, RED_BORDER),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [RED_BG, colors.white]),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(t_remove)
    story.append(Spacer(1, 14))

    # 4. Features to ADD Section
    story.append(Paragraph("2. Core Implemented Features to ADD to Diagram", h2_style))

    add_data = [
        [
            Paragraph("Feature Name", cell_header),
            Paragraph("Target Triangle Level", cell_header),
            Paragraph("Description & Implementation Value", cell_header)
        ],
        [
            Paragraph("<b>Innovation Analyzer & 5-Axis IP Risk Radar</b>", cell_style),
            Paragraph("<b>PRIMARY FUNCTIONS</b><br/>(Level 2)", cell_style),
            Paragraph("Flagship evaluation engine analyzing Traditional Knowledge (TK) overlap, Sec 3(d)/3(p) statutory novelty hurdles, and NBA/ABS compliance.", cell_style)
        ],
        [
            Paragraph("<b>Prior-Art Search Engine</b>", cell_style),
            Paragraph("<b>PRIMARY FUNCTIONS</b><br/>(Level 2)", cell_style),
            Paragraph("Hybrid FAISS (bge-m3) + BM25 search across IP India, WIPO, and TKDL databases with rank cross-encoders.", cell_style)
        ],
        [
            Paragraph("<b>Document Analyzer</b>", cell_style),
            Paragraph("<b>PRIMARY FUNCTIONS</b><br/>(Level 2)", cell_style),
            Paragraph("Deep analysis of uploaded patent specs and research papers for non-patentability and compliance warnings.", cell_style)
        ],
        [
            Paragraph("<b>Interactive Knowledge Graph</b>", cell_style),
            Paragraph("<b>PRIMARY FUNCTIONS</b><br/>(Level 2)", cell_style),
            Paragraph("Interactive visualization mapping connections between Ayurvedic formulations, plant species, and statutory sections.", cell_style)
        ],
        [
            Paragraph("<b>PDF / HTML Dossier & Report Generator</b>", cell_style),
            Paragraph("<b>MONITORING & SUPPORT</b><br/>(Level 4)", cell_style),
            Paragraph("Generates downloadable, audit-ready intelligence reports with full source citations and statutory legal disclaimers.", cell_style)
        ]
    ]

    col_widths_add = [135, 110, 295]
    t_add = Table(add_data, colWidths=col_widths_add)
    t_add.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), GREEN_HEADER),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('GRID', (0, 0), (-1, -1), 0.5, GREEN_BORDER),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [GREEN_BG, colors.white]),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(t_add)
    story.append(Spacer(1, 14))

    # 5. Recommended Revised Triangle Hierarchy Blueprint
    story.append(Paragraph("3. Recommended Revised Triangle Hierarchy Blueprint", h2_style))
    
    tier_data = [
        [
            Paragraph("Pyramid Tier Level", cell_bold),
            Paragraph("Recommended Components & Text for Presentation Diagram", cell_bold)
        ],
        [
            Paragraph("<b>APEX LAYER</b><br/>(Core Feature)", cell_style),
            Paragraph("<b>Citation-Grounded Ayurvedic IP & Regulatory AI Assistant</b>", cell_style)
        ],
        [
            Paragraph("<b>TIER 2</b><br/>(Primary Functions)", cell_style),
            Paragraph("• <b>Jurisdiction-Aware RAG</b><br/>• <b>Innovation Analyzer & 5-Axis IP Risk Radar</b><br/>• <b>Prior-Art Search Engine</b> (TKDL / WIPO / IP India)<br/>• <b>Document Analyzer & Interactive Knowledge Graph</b>", cell_style)
        ],
        [
            Paragraph("<b>TIER 3</b><br/>(Safety & Compliance)", cell_style),
            Paragraph("• <b>Source-Cited Answers</b> (Verified citations linked to evidence)<br/>• <b>Confidence Scoring + Safe Abstention Gate</b><br/>• <b>Statutory Legal Disclaimer & Secure Data Handling</b>", cell_style)
        ],
        [
            Paragraph("<b>TIER 4</b><br/>(Monitoring & Support)", cell_style),
            Paragraph("• <b>Authoritative Source Registry</b> (AYUSH / NBA / IP India / WIPO / WHO)<br/>• <b>Multilingual Chat Support</b> (English, Hindi, Odia)<br/>• <b>Source Freshness Monitoring</b><br/>• <b>PDF / HTML Intelligence Dossier Generator</b>", cell_style)
        ]
    ]

    t_tier = Table(tier_data, colWidths=[130, 410])
    t_tier.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), BLUE_BORDER),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('GRID', (0, 0), (-1, -1), 0.5, BLUE_BORDER),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [BLUE_BG, colors.white]),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(t_tier)

    story.append(Spacer(1, 15))
    story.append(HRFlowable(width="100%", thickness=0.5, color=SUB_TEXT, spaceAfter=8))
    footer_text = "<font color='#64748b' size='8'>Generated automatically for IP-SAKTI SAHAYAK (SIH 2026 · Problem Statement PS26045)</font>"
    story.append(Paragraph(footer_text, ParagraphStyle('Footer', alignment=TA_CENTER)))

    doc.build(story)
    print(f"Successfully generated PDF: {os.path.abspath(filename)}")

if __name__ == "__main__":
    out_pdf = "IP_SAKTI_Sahayak_Triangle_Revisions.pdf"
    if len(sys.argv) > 1:
        out_pdf = sys.argv[1]
    build_pdf(out_pdf)
