from __future__ import annotations

import json
from datetime import datetime
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from app.reports.helpers import safe_text, truncate_text
from app.reports.models import ComparisonReportData, ScanReportData


def _styles():
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "ReportTitle",
            parent=base["Heading1"],
            fontSize=18,
            spaceAfter=6,
            textColor=colors.HexColor("#0f172a"),
            alignment=TA_CENTER,
        ),
        "subtitle": ParagraphStyle(
            "ReportSubtitle",
            parent=base["Normal"],
            fontSize=11,
            textColor=colors.HexColor("#334155"),
            alignment=TA_CENTER,
            spaceAfter=18,
        ),
        "heading": ParagraphStyle(
            "SectionHeading",
            parent=base["Heading2"],
            fontSize=13,
            spaceBefore=14,
            spaceAfter=8,
            textColor=colors.HexColor("#0f172a"),
        ),
        "subheading": ParagraphStyle(
            "SubHeading",
            parent=base["Heading3"],
            fontSize=11,
            spaceBefore=10,
            spaceAfter=4,
            textColor=colors.HexColor("#1e293b"),
        ),
        "body": ParagraphStyle(
            "Body",
            parent=base["Normal"],
            fontSize=9,
            leading=12,
            alignment=TA_LEFT,
            textColor=colors.HexColor("#1e293b"),
        ),
        "muted": ParagraphStyle(
            "Muted",
            parent=base["Normal"],
            fontSize=8,
            textColor=colors.HexColor("#64748b"),
            spaceAfter=4,
        ),
        "ai_label": ParagraphStyle(
            "AILabel",
            parent=base["Normal"],
            fontSize=9,
            textColor=colors.HexColor("#0369a1"),
            spaceBefore=6,
            spaceAfter=4,
            fontName="Helvetica-Bold",
        ),
    }


def _escape(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def _p(text: str, style) -> Paragraph:
    return Paragraph(_escape(text).replace("\n", "<br/>"), style)


def _kv_table(rows: list[tuple[str, str]], styles) -> Table:
    data = [[_p(k, styles["body"]), _p(v, styles["body"])] for k, v in rows]
    table = Table(data, colWidths=[2.1 * inch, 4.4 * inch])
    table.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 2),
                ("RIGHTPADDING", (0, 0), (-1, -1), 2),
                ("TOPPADDING", (0, 0), (-1, -1), 2),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
                ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#64748b")),
            ]
        )
    )
    return table


def _format_dt(value: datetime | None) -> str:
    if value is None:
        return "—"
    return value.strftime("%Y-%m-%d %H:%M:%S UTC")


def generate_scan_report_pdf(data: ScanReportData) -> bytes:
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=0.7 * inch,
        rightMargin=0.7 * inch,
        topMargin=0.65 * inch,
        bottomMargin=0.65 * inch,
        title=f"Security Report - Scan {data.scan_id}",
        author="AI API Security Agent",
    )
    styles = _styles()
    story: list = []

    story.append(_p("AI API SECURITY AGENT", styles["title"]))
    story.append(_p("Security Assessment Report", styles["subtitle"]))
    story.append(
        _p(
            "Deterministic scanners produce findings and risk scores. "
            "Gemini provides optional AI-assisted contextual analysis only.",
            styles["muted"],
        )
    )

    story.append(_p("Scan Information", styles["heading"]))
    story.append(
        _kv_table(
            [
                ("Scan Name", data.scan_name),
                ("Scan ID", str(data.scan_id)),
                ("Source File", data.source_filename),
                ("Status", data.status),
                ("Created", _format_dt(data.created_at)),
                ("Completed", _format_dt(data.completed_at)),
                ("Generated", _format_dt(data.generated_at)),
            ],
            styles,
        )
    )

    story.append(_p("Executive Summary", styles["heading"]))
    story.append(
        _kv_table(
            [
                ("Overall Risk Score", str(data.overall_risk_score)),
                ("Overall Risk Level", data.overall_risk_level),
                ("Endpoints", str(data.endpoint_count)),
                ("Findings", str(data.finding_count)),
                ("AI Analyses Present", str(data.ai_analysis_count)),
            ],
            styles,
        )
    )

    story.append(_p("Severity Distribution", styles["heading"]))
    story.append(
        _kv_table(
            [
                ("Critical", str(data.critical)),
                ("High", str(data.high)),
                ("Medium", str(data.medium)),
                ("Low", str(data.low)),
                ("Info", str(data.info)),
            ],
            styles,
        )
    )

    story.append(_p("Findings", styles["heading"]))
    if not data.findings:
        story.append(_p("No security findings were recorded for this scan.", styles["body"]))
    else:
        for index, finding in enumerate(data.findings, start=1):
            story.append(
                _p(
                    f"Finding {index}: {finding.title}",
                    styles["subheading"],
                )
            )
            story.append(
                _kv_table(
                    [
                        ("Category", finding.category),
                        ("Severity", finding.severity),
                        ("Risk Score", str(finding.risk_score)),
                        ("Risk Level", finding.risk_level),
                        ("Confidence", finding.confidence),
                        ("OWASP", safe_text(finding.owasp_category)),
                        ("Endpoint", safe_text(finding.endpoint_label)),
                        ("HTTP Method", safe_text(finding.method)),
                        ("Path", safe_text(finding.path)),
                    ],
                    styles,
                )
            )
            story.append(_p("Evidence (deterministic)", styles["muted"]))
            story.append(_p(truncate_text(finding.evidence), styles["body"]))
            if finding.risk_factors:
                story.append(_p("Risk Factors", styles["muted"]))
                story.append(
                    _p(
                        truncate_text(json.dumps(finding.risk_factors, indent=2), 2000),
                        styles["body"],
                    )
                )
            story.append(_p("Deterministic Remediation", styles["muted"]))
            story.append(_p(truncate_text(finding.remediation, 1500), styles["body"]))

            if finding.ai and finding.ai.summary:
                story.append(_p("AI-Assisted Analysis", styles["ai_label"]))
                story.append(
                    _p(
                        "The following content is contextual reasoning from Gemini. "
                        "It does not replace deterministic detection or risk scoring.",
                        styles["muted"],
                    )
                )
                ai_rows = [
                    ("Summary", finding.ai.summary),
                    ("Why It Matters", finding.ai.why_it_matters),
                    ("Technical Reasoning", finding.ai.technical_reasoning),
                    ("Validation Guidance", finding.ai.validation_guidance),
                    ("Remediation", finding.ai.remediation),
                    ("Priority", finding.ai.priority),
                    ("Limitations", finding.ai.limitations),
                    ("AI Model", finding.ai.model),
                    ("Analyzed At", _format_dt(finding.ai.analyzed_at)),
                ]
                for label, value in ai_rows:
                    if value:
                        story.append(_p(f"{label}: {truncate_text(str(value), 1500)}", styles["body"]))
            story.append(Spacer(1, 8))

    story.append(_p("Conclusion", styles["heading"]))
    conclusion = (
        f"This assessment identified {data.finding_count} finding(s) across "
        f"{data.endpoint_count} endpoint(s). Overall risk score is "
        f"{data.overall_risk_score} ({data.overall_risk_level}). "
        "Risk scores are produced by the deterministic Phase 5 scoring engine. "
        "AI-assisted analysis, when present, is explanatory only."
    )
    story.append(_p(conclusion, styles["body"]))

    doc.build(story)
    return buffer.getvalue()


def generate_comparison_pdf(data: ComparisonReportData) -> bytes:
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=0.7 * inch,
        rightMargin=0.7 * inch,
        topMargin=0.65 * inch,
        bottomMargin=0.65 * inch,
        title=f"Comparison Report - {data.baseline_scan_id} vs {data.current_scan_id}",
        author="AI API Security Agent",
    )
    styles = _styles()
    story: list = []

    story.append(_p("AI API SECURITY AGENT", styles["title"]))
    story.append(_p("Scan Regression Comparison Report", styles["subtitle"]))

    story.append(_p("Comparison Overview", styles["heading"]))
    story.append(
        _kv_table(
            [
                ("Baseline Scan", f"{data.baseline_scan_name} (#{data.baseline_scan_id})"),
                ("Current Scan", f"{data.current_scan_name} (#{data.current_scan_id})"),
                (
                    "Baseline Risk",
                    f"{data.baseline_risk_score} {data.baseline_risk_level}",
                ),
                (
                    "Current Risk",
                    f"{data.current_risk_score} {data.current_risk_level}",
                ),
                ("Risk Score Change", str(data.risk_score_change)),
                ("Posture", data.posture),
                ("Generated", _format_dt(data.generated_at)),
            ],
            styles,
        )
    )

    story.append(_p("Finding Changes", styles["heading"]))
    story.append(
        _kv_table(
            [
                ("New Findings", str(data.new_count)),
                ("Resolved Findings", str(data.resolved_count)),
                ("Persistent Findings", str(data.persistent_count)),
                ("New Critical", str(data.new_critical_count)),
                ("Resolved Critical", str(data.resolved_critical_count)),
            ],
            styles,
        )
    )

    def _list_section(title: str, items: list[str]) -> None:
        story.append(_p(title, styles["subheading"]))
        if not items:
            story.append(_p("None", styles["body"]))
            return
        for item in items:
            story.append(_p(f"• {item}", styles["body"]))

    _list_section("New Findings", data.new_titles)
    _list_section("Resolved Findings", data.resolved_titles)
    _list_section("Persistent Findings", data.persistent_titles)

    story.append(_p("Conclusion", styles["heading"]))
    direction = {
        "IMPROVED": "improved",
        "WORSENED": "worsened",
        "UNCHANGED": "remained unchanged",
    }.get(data.posture, data.posture.lower())
    story.append(
        _p(
            f"Security posture {direction}. Risk score change: {data.risk_score_change}. "
            f"{data.resolved_count} finding(s) resolved, {data.new_count} new, "
            f"{data.persistent_count} persistent. Matching is deterministic and does not use AI.",
            styles["body"],
        )
    )

    doc.build(story)
    return buffer.getvalue()
