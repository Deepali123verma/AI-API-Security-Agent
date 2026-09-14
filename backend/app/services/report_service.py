from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.finding import Finding
from app.reports.generator import generate_comparison_pdf, generate_scan_report_pdf
from app.reports.helpers import extract_method_path
from app.reports.models import (
    ComparisonReportData,
    ReportFinding,
    ReportFindingAI,
    ScanReportData,
)
from app.services.scan_service import get_scan_for_user
from app.services.scan_summary_service import build_scan_summary
from app.services.security_scan_service import format_finding_endpoint


class ReportServiceError(Exception):
    """Raised when report generation fails after ownership checks."""


def _to_report_finding(finding: Finding) -> ReportFinding:
    method, path = extract_method_path(finding)
    ai = None
    if finding.ai_summary:
        ai = ReportFindingAI(
            summary=finding.ai_summary,
            why_it_matters=finding.ai_why_it_matters,
            technical_reasoning=finding.ai_technical_reasoning,
            validation_guidance=finding.ai_validation_guidance,
            remediation=finding.ai_remediation,
            priority=finding.ai_priority,
            limitations=finding.ai_limitations,
            model=finding.ai_model,
            analyzed_at=finding.ai_analyzed_at,
        )
    return ReportFinding(
        id=finding.id,
        title=finding.title,
        category=finding.category,
        severity=finding.severity,
        risk_score=finding.risk_score,
        risk_level=finding.risk_level,
        confidence=finding.confidence,
        evidence=finding.evidence,
        remediation=finding.remediation,
        risk_factors=finding.risk_factors,
        endpoint_label=format_finding_endpoint(finding),
        method=method,
        path=path,
        owasp_category=finding.owasp_category,
        ai=ai,
    )


def build_scan_report_data(db: Session, scan_id: int, user_id: int) -> ScanReportData | None:
    scan = get_scan_for_user(db, scan_id, user_id)
    if scan is None:
        return None

    summary = build_scan_summary(db, scan)
    findings = list(
        db.scalars(
            select(Finding)
            .options(selectinload(Finding.endpoint))
            .where(Finding.scan_id == scan.id)
            .order_by(Finding.risk_score.desc(), Finding.id)
        ).all()
    )

    return ScanReportData(
        scan_id=scan.id,
        scan_name=scan.name,
        status=scan.status,
        generated_at=datetime.now(UTC),
        created_at=scan.created_at,
        completed_at=scan.completed_at,
        source_filename=scan.source_filename,
        overall_risk_score=summary.overall_risk_score,
        overall_risk_level=summary.risk_level,
        endpoint_count=summary.endpoint_count,
        finding_count=summary.finding_count,
        critical=summary.critical,
        high=summary.high,
        medium=summary.medium,
        low=summary.low,
        info=summary.info,
        ai_analysis_count=summary.ai_analysis_count,
        findings=[_to_report_finding(finding) for finding in findings],
    )


def generate_scan_pdf(db: Session, scan_id: int, user_id: int) -> tuple[bytes, str] | None:
    data = build_scan_report_data(db, scan_id, user_id)
    if data is None:
        return None
    try:
        pdf_bytes = generate_scan_report_pdf(data)
    except Exception as exc:  # pragma: no cover - defensive
        raise ReportServiceError("Failed to generate security report") from exc
    filename = f"security-report-{scan_id}.pdf"
    return pdf_bytes, filename


def generate_comparison_report_pdf(
    comparison,
) -> bytes:
    data = ComparisonReportData(
        baseline_scan_id=comparison.baseline_scan.id,
        baseline_scan_name=comparison.baseline_scan.name,
        baseline_risk_score=comparison.baseline_risk_score,
        baseline_risk_level=comparison.baseline_risk_level,
        current_scan_id=comparison.current_scan.id,
        current_scan_name=comparison.current_scan.name,
        current_risk_score=comparison.current_risk_score,
        current_risk_level=comparison.current_risk_level,
        risk_score_change=comparison.risk_score_change,
        posture=comparison.posture,
        new_count=len(comparison.new_findings),
        resolved_count=len(comparison.resolved_findings),
        persistent_count=len(comparison.persistent_findings),
        new_critical_count=comparison.new_critical_count,
        resolved_critical_count=comparison.resolved_critical_count,
        new_titles=[item.title for item in comparison.new_findings],
        resolved_titles=[item.title for item in comparison.resolved_findings],
        persistent_titles=[item.title for item in comparison.persistent_findings],
        generated_at=datetime.now(UTC),
    )
    try:
        return generate_comparison_pdf(data)
    except Exception as exc:  # pragma: no cover - defensive
        raise ReportServiceError("Failed to generate comparison report") from exc
