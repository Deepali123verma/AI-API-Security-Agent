from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.agents.gemini_client import GeminiClientError
from app.agents.models import AIAnalysisResult
from app.agents.security_agent import SecurityAgent
from app.core.config import settings
from app.models.endpoint import Endpoint
from app.models.finding import Finding
from app.models.scan import Scan
from app.schemas.ai_analysis import AIAnalysis, AIAnalysisResponse
from app.services.scan_service import get_scan_for_user


class AIAnalysisServiceError(Exception):
    """Controlled failure for AI analysis endpoints."""


def get_finding_for_scan(
    db: Session,
    scan_id: int,
    finding_id: int,
    user_id: int,
) -> Finding | None:
    if get_scan_for_user(db, scan_id, user_id) is None:
        return None

    return db.scalar(
        select(Finding)
        .options(selectinload(Finding.endpoint))
        .where(Finding.id == finding_id, Finding.scan_id == scan_id)
    )


def analyze_finding(
    db: Session,
    scan_id: int,
    finding_id: int,
    user_id: int,
    *,
    force_refresh: bool = False,
    agent: SecurityAgent | None = None,
) -> AIAnalysisResponse:
    finding = get_finding_for_scan(db, scan_id, finding_id, user_id)
    if finding is None:
        raise AIAnalysisServiceError("Finding not found")

    if finding.ai_summary and not force_refresh:
        return _to_response(finding, cached=True)

    scan = db.get(Scan, scan_id)
    if scan is None:
        raise AIAnalysisServiceError("Scan not found")

    security_agent = agent or SecurityAgent()
    try:
        analysis = security_agent.analyze_finding(
            finding=_finding_context(finding),
            endpoint=_endpoint_context(finding.endpoint),
            scan_metadata=_scan_metadata(scan),
            untrusted_openapi=_untrusted_openapi_context(finding.endpoint),
        )
    except GeminiClientError as exc:
        raise AIAnalysisServiceError(str(exc)) from exc

    _persist_ai_analysis(finding, analysis, security_agent.model_name)
    db.commit()
    db.refresh(finding)
    return _to_response(finding, cached=False)


def analyze_scan_findings(
    db: Session,
    scan_id: int,
    user_id: int,
    *,
    force_refresh: bool = False,
    limit: int | None = None,
    agent: SecurityAgent | None = None,
) -> tuple[list[AIAnalysisResponse], int, int, list[str]]:
    scan = get_scan_for_user(db, scan_id, user_id)
    if scan is None:
        raise AIAnalysisServiceError("Scan not found")

    max_items = limit if limit is not None else settings.gemini_max_bulk_findings
    findings = list(
        db.scalars(
            select(Finding)
            .options(selectinload(Finding.endpoint))
            .where(Finding.scan_id == scan_id)
            .order_by(Finding.risk_score.desc(), Finding.id)
        ).all()
    )

    security_agent = agent or SecurityAgent()
    results: list[AIAnalysisResponse] = []
    skipped_existing = 0
    errors: list[str] = []
    analyzed = 0

    for finding in findings:
        if finding.ai_summary and not force_refresh:
            skipped_existing += 1
            results.append(_to_response(finding, cached=True))
            continue

        if analyzed >= max_items:
            break

        try:
            analysis = security_agent.analyze_finding(
                finding=_finding_context(finding),
                endpoint=_endpoint_context(finding.endpoint),
                scan_metadata=_scan_metadata(scan),
                untrusted_openapi=_untrusted_openapi_context(finding.endpoint),
            )
            _persist_ai_analysis(finding, analysis, security_agent.model_name)
            db.commit()
            db.refresh(finding)
            results.append(_to_response(finding, cached=False))
            analyzed += 1
        except GeminiClientError as exc:
            db.rollback()
            errors.append(f"Finding {finding.id}: {exc}")

    return results, skipped_existing, analyzed, errors


def _finding_context(finding: Finding) -> dict[str, Any]:
    return {
        "id": finding.id,
        "title": finding.title,
        "description": finding.description,
        "severity": finding.severity,
        "confidence": finding.confidence,
        "risk_score": finding.risk_score,
        "risk_level": finding.risk_level,
        "category": finding.category,
        "owasp_category": finding.owasp_category,
        "evidence": finding.evidence,
        "structured_evidence": finding.structured_evidence,
        "risk_factors": finding.risk_factors,
        "remediation": finding.remediation,
    }


def _endpoint_context(endpoint: Endpoint | None) -> dict[str, Any] | None:
    if endpoint is None:
        return None
    return {
        "method": endpoint.method,
        "path": endpoint.path,
        "summary": endpoint.summary,
        "description": endpoint.description,
        "operation_id": endpoint.operation_id,
        "tags": endpoint.tags,
        "parameters": endpoint.parameters,
        "request_body": endpoint.request_body,
        "responses": endpoint.responses,
        "security_defined": endpoint.security_defined,
        "security_requirements": endpoint.security_requirements,
    }


def _scan_metadata(scan: Scan) -> dict[str, Any]:
    return {
        "scan_id": scan.id,
        "name": scan.name,
        "title": scan.title,
        "version": scan.version,
        "specification_version": scan.specification_version,
        "spec_metadata": scan.spec_metadata,
    }


def _untrusted_openapi_context(endpoint: Endpoint | None) -> dict[str, Any]:
    if endpoint is None:
        return {}
    return {
        "summary": endpoint.summary,
        "description": endpoint.description,
        "operation_id": endpoint.operation_id,
        "tags": endpoint.tags,
        "parameters": endpoint.parameters,
        "request_body": endpoint.request_body,
        "responses": endpoint.responses,
    }


def _persist_ai_analysis(
    finding: Finding,
    analysis: AIAnalysisResult,
    model_name: str,
) -> None:
    finding.ai_summary = analysis.summary
    finding.ai_why_it_matters = analysis.why_it_matters
    finding.ai_technical_reasoning = analysis.technical_reasoning
    finding.ai_validation_guidance = analysis.validation_guidance
    finding.ai_remediation = analysis.remediation
    finding.ai_priority = analysis.priority
    finding.ai_limitations = analysis.limitations
    finding.ai_model = model_name
    finding.ai_analyzed_at = datetime.now(UTC)


def _to_response(finding: Finding, *, cached: bool) -> AIAnalysisResponse:
    if not finding.ai_summary:
        raise AIAnalysisServiceError("AI analysis is unavailable for this finding")

    return AIAnalysisResponse(
        finding_id=finding.id,
        ai_analysis=AIAnalysis(
            summary=finding.ai_summary,
            why_it_matters=finding.ai_why_it_matters or "",
            technical_reasoning=finding.ai_technical_reasoning or "",
            validation_guidance=finding.ai_validation_guidance or "",
            remediation=finding.ai_remediation or "",
            priority=finding.ai_priority or "INFO",  # type: ignore[arg-type]
            limitations=finding.ai_limitations or "",
        ),
        model=finding.ai_model or settings.gemini_model,
        cached=cached,
        analyzed_at=finding.ai_analyzed_at,
    )
