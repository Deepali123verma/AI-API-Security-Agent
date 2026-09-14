from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session, selectinload

from app.core.scan_status import COMPLETED, FAILED, PENDING, SECURITY_SCAN_ELIGIBLE
from app.models.finding import Finding
from app.models.scan import Scan
from app.scanner.engine import ScannerEngine
from app.scanner.models import ScanContext, ScannerFinding
from app.scoring.engine import RiskScoringEngine
from app.scoring.models import ScanRiskSummary
from app.services.scan_service import get_scan_for_user
from app.utils.pagination import normalize_pagination, offset_for, pagination_meta


@dataclass
class SecurityScanResult:
    scan: Scan
    findings: list[Finding]
    summary: ScanRiskSummary


def run_security_scan(db: Session, scan_id: int, user_id: int) -> SecurityScanResult | None:
    scan = db.scalar(
        select(Scan)
        .options(selectinload(Scan.endpoints))
        .where(Scan.id == scan_id, Scan.user_id == user_id)
    )
    if scan is None:
        return None

    if scan.status not in SECURITY_SCAN_ELIGIBLE:
        return None

    scan.status = PENDING
    scan.completed_at = None
    db.commit()

    try:
        db.execute(delete(Finding).where(Finding.scan_id == scan.id))
        db.flush()

        context = ScanContext(
            scan=scan,
            endpoints=list(scan.endpoints),
            spec_metadata=scan.spec_metadata or {},
        )
        endpoint_by_id = {endpoint.id: endpoint for endpoint in context.endpoints}
        scanner_findings = ScannerEngine().run(context)
        scoring_engine = RiskScoringEngine()

        for finding in scanner_findings:
            endpoint = endpoint_by_id.get(finding.endpoint_id) if finding.endpoint_id else None
            score_result = scoring_engine.score_finding(finding, endpoint)
            structured_evidence = scoring_engine.build_structured_evidence(finding, endpoint)
            _persist_finding(
                db,
                scan.id,
                finding,
                score_result.risk_score,
                score_result.risk_level,
                score_result.risk_factors,
                structured_evidence,
            )

        db.flush()

        refreshed_findings = list(
            db.scalars(
                select(Finding)
                .options(selectinload(Finding.endpoint))
                .where(Finding.scan_id == scan.id)
                .order_by(Finding.risk_score.desc(), Finding.id)
            ).all()
        )
        summary = scoring_engine.summarize_scan(
            [finding.risk_score for finding in refreshed_findings]
        )

        scan.status = COMPLETED
        scan.completed_at = datetime.now(UTC)
        scan.overall_risk_score = summary.overall_risk_score
        scan.overall_risk_level = summary.risk_level
        db.commit()
        db.refresh(scan)

        refreshed_findings = list(
            db.scalars(
                select(Finding)
                .options(selectinload(Finding.endpoint))
                .where(Finding.scan_id == scan.id)
                .order_by(Finding.risk_score.desc(), Finding.id)
            ).all()
        )

        return SecurityScanResult(scan=scan, findings=refreshed_findings, summary=summary)
    except Exception:
        db.rollback()
        failed_scan = get_scan_for_user(db, scan_id, user_id)
        if failed_scan is not None:
            failed_scan.status = FAILED
            failed_scan.completed_at = None
            db.commit()
        raise


def list_findings_for_scan(
    db: Session,
    scan_id: int,
    user_id: int,
    severity: str | None = None,
    category: str | None = None,
    risk_level: str | None = None,
    min_risk_score: int | None = None,
    *,
    page: int | None = None,
    page_size: int | None = None,
) -> tuple[list[Finding], dict[str, int]] | None:
    if get_scan_for_user(db, scan_id, user_id) is None:
        return None

    filters = [Finding.scan_id == scan_id]
    if severity:
        filters.append(Finding.severity == severity.upper())
    if category:
        filters.append(Finding.category == category)
    if risk_level:
        filters.append(Finding.risk_level == risk_level.upper())
    if min_risk_score is not None:
        filters.append(Finding.risk_score >= min_risk_score)

    total = int(db.scalar(select(func.count(Finding.id)).where(*filters)) or 0)

    query = (
        select(Finding)
        .options(selectinload(Finding.endpoint))
        .where(*filters)
        .order_by(Finding.risk_score.desc(), Finding.id)
    )

    if page is None and page_size is None:
        findings = list(db.scalars(query).all())
        return findings, pagination_meta(total, 1, total or 1)

    page_value, page_size_value = normalize_pagination(page or 1, page_size or 50)
    findings = list(
        db.scalars(
            query.offset(offset_for(page_value, page_size_value)).limit(page_size_value)
        ).all()
    )
    return findings, pagination_meta(total, page_value, page_size_value)


def _persist_finding(
    db: Session,
    scan_id: int,
    finding: ScannerFinding,
    risk_score: int,
    risk_level: str,
    risk_factors: dict,
    structured_evidence: dict,
) -> Finding:
    record = Finding(
        scan_id=scan_id,
        endpoint_id=finding.endpoint_id,
        title=finding.title,
        description=finding.description,
        severity=finding.severity,
        category=finding.category,
        owasp_category=finding.owasp_category,
        evidence=finding.evidence,
        remediation=finding.remediation,
        confidence=finding.confidence,
        structured_evidence=structured_evidence,
        risk_score=risk_score,
        risk_level=risk_level,
        risk_factors=risk_factors,
    )
    db.add(record)
    return record


def format_finding_endpoint(finding: Finding) -> str | None:
    if finding.endpoint is not None:
        return f"{finding.endpoint.method} {finding.endpoint.path}"
    return None
