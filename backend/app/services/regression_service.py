from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.finding import Finding
from app.models.scan import Scan
from app.reports.helpers import extract_method_path, finding_fingerprint
from app.services.scan_service import get_scan_for_user
from app.services.scan_summary_service import build_scan_summary
from app.services.security_scan_service import format_finding_endpoint


@dataclass
class RegressionFindingItem:
    id: int
    title: str
    category: str
    severity: str
    risk_score: int
    risk_level: str
    endpoint: str | None
    method: str | None
    path: str | None
    fingerprint: str


@dataclass
class RegressionScanInfo:
    id: int
    name: str
    status: str
    overall_risk_score: int
    overall_risk_level: str
    finding_count: int


@dataclass
class RegressionResult:
    baseline_scan: RegressionScanInfo
    current_scan: RegressionScanInfo
    baseline_risk_score: int
    current_risk_score: int
    risk_score_change: int
    baseline_risk_level: str
    current_risk_level: str
    new_findings: list[RegressionFindingItem]
    resolved_findings: list[RegressionFindingItem]
    persistent_findings: list[RegressionFindingItem]
    new_critical_count: int
    resolved_critical_count: int
    posture: str
    summary: str


def _scan_info(scan: Scan, summary) -> RegressionScanInfo:
    return RegressionScanInfo(
        id=scan.id,
        name=scan.name,
        status=scan.status,
        overall_risk_score=summary.overall_risk_score,
        overall_risk_level=summary.risk_level,
        finding_count=summary.finding_count,
    )


def _to_item(finding: Finding) -> RegressionFindingItem:
    method, path = extract_method_path(finding)
    return RegressionFindingItem(
        id=finding.id,
        title=finding.title,
        category=finding.category,
        severity=finding.severity,
        risk_score=finding.risk_score,
        risk_level=finding.risk_level,
        endpoint=format_finding_endpoint(finding),
        method=method,
        path=path,
        fingerprint=finding_fingerprint(finding),
    )


def _load_findings(db: Session, scan_id: int) -> list[Finding]:
    return list(
        db.scalars(
            select(Finding)
            .options(selectinload(Finding.endpoint))
            .where(Finding.scan_id == scan_id)
            .order_by(Finding.risk_score.desc(), Finding.id)
        ).all()
    )


def classify_posture(risk_score_change: int) -> str:
    if risk_score_change < 0:
        return "IMPROVED"
    if risk_score_change > 0:
        return "WORSENED"
    return "UNCHANGED"


def build_posture_summary(
    posture: str,
    risk_score_change: int,
    new_count: int,
    resolved_count: int,
    persistent_count: int,
) -> str:
    if posture == "IMPROVED":
        headline = "Security Posture Improved"
        score_text = f"Risk score decreased by {abs(risk_score_change)} points"
    elif posture == "WORSENED":
        headline = "Security Posture Worsened"
        score_text = f"Risk score increased by {risk_score_change} points"
    else:
        headline = "Security Posture Unchanged"
        score_text = "Risk score is unchanged"

    return (
        f"{headline}. {resolved_count} finding(s) resolved, "
        f"{new_count} new finding(s) detected, "
        f"{persistent_count} finding(s) remain persistent. {score_text}."
    )


def compare_scans(
    db: Session,
    current_scan_id: int,
    baseline_scan_id: int,
    user_id: int,
) -> RegressionResult | None:
    """Compare current scan against baseline for the same authenticated user.

    Returns None when either scan is missing or not owned by the user.
    """
    if current_scan_id == baseline_scan_id:
        raise ValueError("Baseline and current scan must be different")

    current_scan = get_scan_for_user(db, current_scan_id, user_id)
    baseline_scan = get_scan_for_user(db, baseline_scan_id, user_id)
    if current_scan is None or baseline_scan is None:
        return None

    current_summary = build_scan_summary(db, current_scan)
    baseline_summary = build_scan_summary(db, baseline_scan)

    current_findings = _load_findings(db, current_scan.id)
    baseline_findings = _load_findings(db, baseline_scan.id)

    baseline_by_fp = {finding_fingerprint(f): f for f in baseline_findings}
    current_by_fp = {finding_fingerprint(f): f for f in current_findings}

    baseline_keys = set(baseline_by_fp)
    current_keys = set(current_by_fp)

    new_keys = current_keys - baseline_keys
    resolved_keys = baseline_keys - current_keys
    persistent_keys = baseline_keys & current_keys

    new_findings = [_to_item(current_by_fp[key]) for key in sorted(new_keys)]
    resolved_findings = [_to_item(baseline_by_fp[key]) for key in sorted(resolved_keys)]
    # Persistent: show current-scan finding details (current risk)
    persistent_findings = [_to_item(current_by_fp[key]) for key in sorted(persistent_keys)]

    risk_score_change = current_summary.overall_risk_score - baseline_summary.overall_risk_score
    posture = classify_posture(risk_score_change)

    new_critical_count = sum(1 for item in new_findings if item.risk_level == "CRITICAL")
    resolved_critical_count = sum(
        1 for item in resolved_findings if item.risk_level == "CRITICAL"
    )

    return RegressionResult(
        baseline_scan=_scan_info(baseline_scan, baseline_summary),
        current_scan=_scan_info(current_scan, current_summary),
        baseline_risk_score=baseline_summary.overall_risk_score,
        current_risk_score=current_summary.overall_risk_score,
        risk_score_change=risk_score_change,
        baseline_risk_level=baseline_summary.risk_level,
        current_risk_level=current_summary.risk_level,
        new_findings=new_findings,
        resolved_findings=resolved_findings,
        persistent_findings=persistent_findings,
        new_critical_count=new_critical_count,
        resolved_critical_count=resolved_critical_count,
        posture=posture,
        summary=build_posture_summary(
            posture,
            risk_score_change,
            len(new_findings),
            len(resolved_findings),
            len(persistent_findings),
        ),
    )
