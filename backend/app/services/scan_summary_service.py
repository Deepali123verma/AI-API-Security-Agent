from dataclasses import dataclass

from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from app.models.endpoint import Endpoint
from app.models.finding import Finding
from app.models.scan import Scan
from app.scoring.engine import RiskScoringEngine
from app.scoring.models import ScanRiskSummary


@dataclass
class ScanAggregateSummary:
    endpoint_count: int
    finding_count: int
    critical: int
    high: int
    medium: int
    low: int
    info: int
    overall_risk_score: int
    risk_level: str
    ai_analysis_count: int


def build_scan_summary(db: Session, scan: Scan) -> ScanAggregateSummary:
    endpoint_count = int(
        db.scalar(select(func.count(Endpoint.id)).where(Endpoint.scan_id == scan.id)) or 0
    )

    severity_rows = db.execute(
        select(
            Finding.risk_level,
            func.count(Finding.id),
        )
        .where(Finding.scan_id == scan.id)
        .group_by(Finding.risk_level)
    ).all()
    counts = {level: int(count) for level, count in severity_rows}
    finding_count = sum(counts.values())

    ai_analysis_count = int(
        db.scalar(
            select(func.count(Finding.id)).where(
                Finding.scan_id == scan.id,
                Finding.ai_summary.is_not(None),
            )
        )
        or 0
    )

    if scan.overall_risk_score is not None and scan.overall_risk_level is not None:
        overall_risk_score = scan.overall_risk_score
        risk_level = scan.overall_risk_level
    elif finding_count == 0:
        overall_risk_score = 0
        risk_level = "INFO"
    else:
        scores = list(
            db.scalars(select(Finding.risk_score).where(Finding.scan_id == scan.id)).all()
        )
        summary = RiskScoringEngine().summarize_scan(scores)
        overall_risk_score = summary.overall_risk_score
        risk_level = summary.risk_level

    return ScanAggregateSummary(
        endpoint_count=endpoint_count,
        finding_count=finding_count,
        critical=counts.get("CRITICAL", 0),
        high=counts.get("HIGH", 0),
        medium=counts.get("MEDIUM", 0),
        low=counts.get("LOW", 0),
        info=counts.get("INFO", 0),
        overall_risk_score=overall_risk_score,
        risk_level=risk_level,
        ai_analysis_count=ai_analysis_count,
    )


def risk_summary_from_persisted(scan: Scan, finding_scores: list[int]) -> ScanRiskSummary:
    if scan.overall_risk_score is not None and scan.overall_risk_level is not None:
        # Rebuild severity buckets from provided scores using Phase 5 thresholds.
        return RiskScoringEngine().summarize_scan(finding_scores)
    return RiskScoringEngine().summarize_scan(finding_scores)


def endpoint_finding_counts(db: Session, scan_id: int) -> dict[int, int]:
    rows = db.execute(
        select(Finding.endpoint_id, func.count(Finding.id))
        .where(Finding.scan_id == scan_id, Finding.endpoint_id.is_not(None))
        .group_by(Finding.endpoint_id)
    ).all()
    return {int(endpoint_id): int(count) for endpoint_id, count in rows}
