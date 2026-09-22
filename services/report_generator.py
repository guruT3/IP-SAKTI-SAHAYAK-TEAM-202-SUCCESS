"""
IP-SAKTI SAHAYAK
Comprehensive IP Intelligence Dossier & Report Generator
=========================================================
Generates high-fidelity HTML and PDF reports for:
1. Standard Grounded Q&A Sessions
2. Comprehensive Innovation Analysis Dossiers (Flagship Feature)
3. Deep IP Research Reports

Includes:
- Executive Summary & Extracted Botanicals/Claims
- 5-Axis IP Risk Radar Breakdown
- Traditional Knowledge & Section 3(d)/3(p) Statutory Analysis
- Biological Diversity Act (NBA/ABS) Compliance Alerts
- Prior-Art Reference Register with Official URLs
- Mandatory Legal Disclaimers
"""

import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List

from config import settings
from database.db import get_session
from database.models import Message, Report, Citation

logger = logging.getLogger(__name__)

HTML_DOSSIER_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>IP-SAKTI SAHAYAK — IP & TK Intelligence Dossier</title>
  <style>
    body {{ font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, Roboto, sans-serif; max-width: 900px; margin: 40px auto; color: #1e293b; line-height: 1.6; background: #fff; padding: 0 20px; }}
    .header {{ border-bottom: 3px solid #0f766e; padding-bottom: 16px; margin-bottom: 24px; }}
    .header h1 {{ margin: 0; color: #0f766e; font-size: 24px; font-weight: 700; letter-spacing: -0.02em; }}
    .header .tagline {{ color: #64748b; font-size: 13px; margin-top: 4px; }}
    .meta-grid {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; background: #f8fafc; padding: 14px; border-radius: 8px; border: 1px solid #e2e8f0; font-size: 13px; margin-bottom: 24px; }}
    .meta-item strong {{ color: #0f766e; display: block; font-size: 11px; text-transform: uppercase; }}
    .section {{ margin-top: 28px; }}
    .section h2 {{ font-size: 16px; text-transform: uppercase; letter-spacing: 0.05em; color: #0f766e; border-bottom: 1px solid #e2e8f0; padding-bottom: 6px; margin-bottom: 12px; }}
    .radar-box {{ background: #f0fdfa; border: 1px solid #ccfbf1; padding: 16px; border-radius: 8px; margin-bottom: 20px; }}
    .radar-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 10px; margin-top: 10px; }}
    .radar-item {{ background: #fff; padding: 10px; border-radius: 6px; border: 1px solid #99f6e4; text-align: center; }}
    .radar-item .val {{ font-size: 18px; font-weight: bold; color: #0f766e; }}
    .radar-item .lbl {{ font-size: 11px; color: #64748b; }}
    .source-card {{ border-left: 3px solid #0f766e; background: #f8fafc; padding: 10px 14px; margin-bottom: 10px; border-radius: 0 6px 6px 0; font-size: 13px; }}
    .source-card strong {{ color: #0f766e; }}
    .disclaimer {{ margin-top: 40px; font-size: 12px; color: #64748b; border-top: 1px solid #e2e8f0; padding-top: 14px; line-height: 1.5; }}
    .pre-text {{ white-space: pre-wrap; font-family: inherit; font-size: 14px; color: #334155; }}
    .badge {{ display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 600; background: #e0f2fe; color: #0369a1; }}
  </style>
</head>
<body>
  <div class="header">
    <h1>IP-SAKTI SAHAYAK</h1>
    <div class="tagline">AI-Powered Intellectual Property, Ayurveda & Traditional Knowledge Intelligence Platform (SIH 2026 · PS26045)</div>
  </div>

  <div class="meta-grid">
    <div class="meta-item"><strong>Generated At</strong>{generated_at}</div>
    <div class="meta-item"><strong>Subject / Innovation</strong>{title}</div>
    <div class="meta-item"><strong>Jurisdiction</strong>{jurisdiction}</div>
    <div class="meta-item"><strong>Confidence Score</strong>{confidence_display}</div>
  </div>

  {radar_html}

  <div class="section">
    <h2>Intelligence Synthesis & Legal Findings</h2>
    <div class="pre-text">{content}</div>
  </div>

  <div class="section">
    <h2>Authoritative Statutory Sources & Evidence Register</h2>
    {sources_html}
  </div>

  <div class="disclaimer">
    <strong>STATUTORY LEGAL DISCLAIMER:</strong> This report is an automated AI-assisted research dossier compiled from official statutory databases, TKDL references, and IP office guidelines. It is provided for informational and academic evaluation purposes only and does not constitute a formal legal opinion, patentability certification, or substitute for consultation with a qualified Patent Agent or Legal Attorney.
  </div>
</body>
</html>"""


def _build_radar_html(radar_data: Optional[Dict[str, Any]]) -> str:
    if not radar_data or "scores" not in radar_data:
        return ""
    scores = radar_data["scores"]
    levels = radar_data.get("levels", {})
    return f"""
    <div class="radar-box">
      <strong>IP RISK RADAR ASSESSMENT (Composite Risk: {radar_data.get('composite_risk', 50)}%)</strong>
      <div class="radar-grid">
        <div class="radar-item"><div class="val">{scores.get('tk_overlap', 0)}%</div><div class="lbl">TK Overlap ({levels.get('tk_overlap', 'MED')})</div></div>
        <div class="radar-item"><div class="val">{scores.get('novelty_risk', 0)}%</div><div class="lbl">Novelty / Sec 3(d) ({levels.get('novelty_risk', 'MED')})</div></div>
        <div class="radar-item"><div class="val">{scores.get('abs_compliance', 0)}%</div><div class="lbl">NBA / ABS ({levels.get('abs_compliance', 'MED')})</div></div>
        <div class="radar-item"><div class="val">{scores.get('regulatory_complexity', 0)}%</div><div class="lbl">AYUSH Reg ({levels.get('regulatory_complexity', 'MED')})</div></div>
        <div class="radar-item"><div class="val">{scores.get('international_friction', 0)}%</div><div class="lbl">International ({levels.get('international_friction', 'MED')})</div></div>
      </div>
    </div>
    """


def _build_sources_html(sources: List[Dict[str, Any]]) -> str:
    if not sources:
        return "<p style='color:#64748b;font-size:13px;'>No specific external sources attached.</p>"
    parts = []
    for i, s in enumerate(sources):
        name = s.get("source_name") or s.get("authority") or "Authoritative Source"
        sec = s.get("section") or s.get("title") or "N/A"
        url = s.get("url") or s.get("source_url") or s.get("url_display") or "Official Gazette"
        parts.append(
            f'<div class="source-card">'
            f'<strong>[Source {i+1}] {name}</strong> &mdash; <em>{sec}</em><br>'
            f'<span style="color:#64748b;font-size:12px;">Reference: {url}</span>'
            f'</div>'
        )
    return "\n".join(parts)


def generate_report(
    message_id: Optional[str] = None,
    answer_payload: Optional[Dict[str, Any]] = None,
    fmt: str = "html",
) -> Dict[str, Any]:
    """Generates an authoritative HTML or PDF report."""
    title = "IP & Traditional Knowledge Research Report"
    content = ""
    jurisdiction = "India"
    confidence = 0.85
    confidence_level = "HIGH"
    sources = []
    radar_data = None

    if message_id:
        with get_session() as db:
            msg = db.get(Message, message_id)
            if msg:
                content = msg.content
                title = msg.domain or title
                jurisdiction = msg.jurisdiction or jurisdiction
                confidence = msg.confidence or confidence
                confidence_level = msg.confidence_level or confidence_level
                citations = db.query(Citation).filter(Citation.message_id == message_id).all()
                sources = [{"authority": c.source_name, "section": c.section, "url": c.url} for c in citations]
    elif answer_payload:
        title = answer_payload.get("innovation_name") or answer_payload.get("query") or title
        content = answer_payload.get("comprehensive_report") or answer_payload.get("answer") or answer_payload.get("dossier") or ""
        jurisdiction = answer_payload.get("target_jurisdiction") or answer_payload.get("jurisdiction") or jurisdiction
        confidence = answer_payload.get("confidence", 0.85)
        confidence_level = answer_payload.get("confidence_level", "HIGH")
        sources = answer_payload.get("prior_art_references") or answer_payload.get("sources") or []
        radar_data = answer_payload.get("risk_radar")

    html = HTML_DOSSIER_TEMPLATE.format(
        generated_at=datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
        title=title,
        jurisdiction=jurisdiction,
        confidence_display=f"{confidence_level} ({int(confidence * 100)}%)",
        radar_html=_build_radar_html(radar_data),
        content=content or "(No content recorded)",
        sources_html=_build_sources_html(sources),
    )

    report_dir = Path(settings.REPORTS_PATH)
    report_dir.mkdir(parents=True, exist_ok=True)
    file_id = uuid.uuid4().hex

    if fmt == "html":
        file_path = report_dir / f"report_{file_id}.html"
        file_path.write_text(html, encoding="utf-8")
    else:
        file_path = report_dir / f"report_{file_id}.pdf"
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.pdfgen import canvas
            from reportlab.lib.units import mm

            c = canvas.Canvas(str(file_path), pagesize=A4)
            width, height = A4
            y = height - 20 * mm

            # Draw header
            c.setFont("Helvetica-Bold", 14)
            c.drawString(20 * mm, y, "IP-SAKTI SAHAYAK — Research Report")
            y -= 6 * mm
            c.setFont("Helvetica", 9)
            c.drawString(20 * mm, y, f"Subject: {title[:70]} | Jurisdiction: {jurisdiction} | Date: {datetime.utcnow().strftime('%Y-%m-%d')}")
            y -= 8 * mm
            c.line(20 * mm, y, width - 20 * mm, y)
            y -= 6 * mm

            # Draw content lines
            c.setFont("Helvetica", 9)
            for line in content.split("\n"):
                if y < 20 * mm:
                    c.showPage()
                    y = height - 20 * mm
                    c.setFont("Helvetica", 9)
                while len(line) > 100:
                    c.drawString(20 * mm, y, line[:100])
                    line = line[100:]
                    y -= 4.5 * mm
                c.drawString(20 * mm, y, line)
                y -= 4.5 * mm

            c.save()
        except Exception as e:
            logger.warning("PDF export failed (%s); falling back to HTML.", e)
            file_path = report_dir / f"report_{file_id}.html"
            file_path.write_text(html, encoding="utf-8")
            fmt = "html"

    with get_session() as db:
        report_row = Report(message_id=message_id, format=fmt, file_path=str(file_path))
        db.add(report_row)
        db.flush()
        report_id = report_row.id

    return {
        "success": True,
        "report_id": report_id,
        "format": fmt,
        "file_path": str(file_path),
        "download_url": f"/api/reports/download/{file_path.name}",
    }


# =====================================================
# TEST
# =====================================================
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    rep = generate_report(answer_payload={"query": "Test query", "answer": "Test answer content."}, fmt="html")
    print("report_generator self-test passed:", rep)
