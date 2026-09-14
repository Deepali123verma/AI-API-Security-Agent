from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import settings
from app.core.database import get_db
from app.models.user import User
from app.schemas.ai_analysis import AIAnalysisResponse, BulkAIAnalysisResponse
from app.schemas.endpoint import EndpointHistoryItem, EndpointHistoryResponse
from app.schemas.finding import (
    FindingHistoryResponse,
    FindingResponse,
    FindingAIAnalysisSummary,
    SecurityScanResponse,
)
from app.schemas.regression import (
    RegressionFindingItem,
    RegressionResponse,
    RegressionScanInfo,
)
from app.schemas.scan import (
    ScanCreateResponse,
    ScanDetailResponse,
    ScanHistoryItem,
    ScanHistoryResponse,
    ScanSummary,
    SpecMetadataSummary,
)
from app.services.ai_analysis_service import (
    AIAnalysisServiceError,
    analyze_finding,
    analyze_scan_findings,
)
from app.services.regression_service import compare_scans
from app.services.report_service import (
    ReportServiceError,
    generate_comparison_report_pdf,
    generate_scan_pdf,
)
from app.services.scan_service import (
    build_spec_metadata_summary,
    create_scan_from_upload,
    delete_scan_for_user,
    get_scan_detail,
    get_scan_for_user,
    list_endpoints_for_scan,
    list_scans_for_user,
)
from app.services.security_scan_service import (
    format_finding_endpoint,
    list_findings_for_scan,
    run_security_scan,
)
from app.utils.openapi_parser import OpenAPIParserError

router = APIRouter(prefix="/api/v1/scans", tags=["scans"])

ALLOWED_CONTENT_TYPES = {
    "application/json",
    "application/yaml",
    "application/x-yaml",
    "text/yaml",
    "text/x-yaml",
    "text/plain",
    "application/octet-stream",
}
ALLOWED_EXTENSIONS = {".json", ".yaml", ".yml"}


@router.post("", response_model=ScanCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_scan(
    file: UploadFile = File(..., description="OpenAPI specification file (JSON or YAML)"),
    name: str | None = Form(None, description="Optional scan name"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ScanCreateResponse:
    validate_upload_file(file)

    content = await file.read()
    if len(content) > settings.max_upload_size_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Uploaded file exceeds the maximum allowed size",
        )

    try:
        scan = create_scan_from_upload(
            db=db,
            user=current_user,
            content=content,
            source_filename=file.filename,
            name=name,
        )
    except OpenAPIParserError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    return ScanCreateResponse(scan_id=scan.id, name=scan.name, status=scan.status)


@router.get("", response_model=ScanHistoryResponse)
def list_scans(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status_filter: str | None = Query(None, alias="status", description="Filter by scan status"),
    risk_level: str | None = Query(None, description="Filter by overall risk level"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ScanHistoryResponse:
    items, meta = list_scans_for_user(
        db,
        current_user.id,
        page=page,
        page_size=page_size,
        status=status_filter,
        risk_level=risk_level,
    )
    return ScanHistoryResponse(
        items=[
            ScanHistoryItem(
                id=scan.id,
                name=scan.name,
                status=scan.status,
                created_at=scan.created_at,
                updated_at=scan.updated_at,
                completed_at=scan.completed_at,
                spec_metadata=SpecMetadataSummary(**build_spec_metadata_summary(scan)),
                endpoint_count=endpoint_count,
                finding_count=finding_count,
                risk_level=scan.overall_risk_level,
                overall_risk_score=scan.overall_risk_score,
            )
            for scan, endpoint_count, finding_count in items
        ],
        **meta,
    )


@router.get("/{scan_id}", response_model=ScanDetailResponse)
def get_scan(
    scan_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ScanDetailResponse:
    result = get_scan_detail(db, scan_id, current_user.id)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scan not found",
        )

    scan, summary = result
    return ScanDetailResponse(
        id=scan.id,
        scan_id=scan.id,
        name=scan.name,
        source_filename=scan.source_filename,
        status=scan.status,
        created_at=scan.created_at,
        updated_at=scan.updated_at,
        completed_at=scan.completed_at,
        specification_version=scan.specification_version,
        title=scan.title,
        description=scan.description,
        version=scan.version,
        endpoint_count=summary.endpoint_count,
        spec_metadata=SpecMetadataSummary(**build_spec_metadata_summary(scan)),
        summary=ScanSummary(
            endpoint_count=summary.endpoint_count,
            finding_count=summary.finding_count,
            critical=summary.critical,
            high=summary.high,
            medium=summary.medium,
            low=summary.low,
            info=summary.info,
            overall_risk_score=summary.overall_risk_score,
            risk_level=summary.risk_level,
            ai_analysis_count=summary.ai_analysis_count,
        ),
    )


@router.get("/{scan_id}/endpoints", response_model=EndpointHistoryResponse)
def get_scan_endpoints(
    scan_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> EndpointHistoryResponse:
    result = list_endpoints_for_scan(
        db,
        scan_id,
        current_user.id,
        page=page,
        page_size=page_size,
    )
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scan not found",
        )

    items, meta = result
    return EndpointHistoryResponse(
        items=[
            EndpointHistoryItem(
                id=endpoint.id,
                method=endpoint.method,
                path=endpoint.path,
                summary=endpoint.summary,
                operation_id=endpoint.operation_id,
                finding_count=finding_count,
                security_defined=endpoint.security_defined,
                security_requirements=endpoint.security_requirements,
                tags=endpoint.tags or [],
            )
            for endpoint, finding_count in items
        ],
        **meta,
    )


@router.delete("/{scan_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_scan(
    scan_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    deleted = delete_scan_for_user(db, scan_id, current_user.id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scan not found",
        )


@router.post(
    "/{scan_id}/security-scan",
    response_model=SecurityScanResponse,
    summary="Run deterministic security scan",
)
def execute_security_scan(
    scan_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SecurityScanResponse:
    try:
        result = run_security_scan(db, scan_id, current_user.id)
    except Exception as exc:
        scan = get_scan_for_user(db, scan_id, current_user.id)
        if scan is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Scan not found",
            ) from exc
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Security scan failed",
        ) from exc

    if result is None:
        scan = get_scan_for_user(db, scan_id, current_user.id)
        if scan is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Scan not found",
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Security scan can only be run on PENDING, COMPLETED, or FAILED scans",
        )

    summary = result.summary
    return SecurityScanResponse(
        scan_id=scan_id,
        total_findings=summary.total_findings,
        findings_count=summary.total_findings,
        critical=summary.critical,
        high=summary.high,
        medium=summary.medium,
        low=summary.low,
        info=summary.info,
        overall_risk_score=summary.overall_risk_score,
        risk_level=summary.risk_level,
        findings=[_to_finding_response(finding) for finding in result.findings],
    )


@router.get(
    "/{scan_id}/findings",
    response_model=FindingHistoryResponse,
    summary="List security findings for a scan",
)
def get_scan_findings(
    scan_id: int,
    severity: str | None = Query(None, description="Filter by severity"),
    category: str | None = Query(None, description="Filter by category"),
    risk_level: str | None = Query(None, description="Filter by calculated risk level"),
    min_risk_score: int | None = Query(None, ge=0, le=100, description="Minimum risk score"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> FindingHistoryResponse:
    result = list_findings_for_scan(
        db,
        scan_id,
        current_user.id,
        severity=severity,
        category=category,
        risk_level=risk_level,
        min_risk_score=min_risk_score,
        page=page,
        page_size=page_size,
    )
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scan not found",
        )

    findings, meta = result
    return FindingHistoryResponse(
        items=[_to_finding_response(finding) for finding in findings],
        **meta,
    )


@router.post(
    "/{scan_id}/findings/{finding_id}/analyze",
    response_model=AIAnalysisResponse,
    summary="Analyze a finding with Gemini AI reasoning",
)
def analyze_finding_endpoint(
    scan_id: int,
    finding_id: int,
    force_refresh: bool = Query(
        False,
        description="Force a new Gemini analysis even if cached analysis exists",
    ),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AIAnalysisResponse:
    try:
        return analyze_finding(
            db,
            scan_id,
            finding_id,
            current_user.id,
            force_refresh=force_refresh,
        )
    except AIAnalysisServiceError as exc:
        detail = str(exc)
        if detail in {"Finding not found", "Scan not found"}:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=detail,
            ) from exc
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=detail,
        ) from exc


@router.post(
    "/{scan_id}/ai-analysis",
    response_model=BulkAIAnalysisResponse,
    summary="Analyze multiple findings with Gemini (capped)",
)
def analyze_scan_findings_endpoint(
    scan_id: int,
    force_refresh: bool = Query(
        False,
        description="Force refresh existing AI analyses",
    ),
    limit: int | None = Query(
        None,
        ge=1,
        le=50,
        description="Maximum number of new Gemini analyses in this request",
    ),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> BulkAIAnalysisResponse:
    try:
        results, skipped_existing, analyzed, errors = analyze_scan_findings(
            db,
            scan_id,
            current_user.id,
            force_refresh=force_refresh,
            limit=limit,
        )
    except AIAnalysisServiceError as exc:
        detail = str(exc)
        if detail == "Scan not found":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=detail,
            ) from exc
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=detail,
        ) from exc

    return BulkAIAnalysisResponse(
        scan_id=scan_id,
        analyzed_count=analyzed,
        skipped_existing_count=skipped_existing,
        failed_count=len(errors),
        results=results,
        errors=errors,
    )


@router.get(
    "/{scan_id}/report/pdf",
    summary="Download security assessment PDF report",
    responses={
        200: {
            "content": {"application/pdf": {}},
            "description": "PDF security report",
        }
    },
)
def download_scan_report_pdf(
    scan_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Response:
    try:
        result = generate_scan_pdf(db, scan_id, current_user.id)
    except ReportServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scan not found",
        )

    pdf_bytes, filename = result
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
        },
    )


@router.get(
    "/{scan_id}/compare/{baseline_scan_id}",
    response_model=RegressionResponse,
    summary="Compare current scan against a baseline scan",
)
def compare_scan_with_baseline(
    scan_id: int,
    baseline_scan_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> RegressionResponse:
    if scan_id == baseline_scan_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Baseline and current scan must be different",
        )

    try:
        result = compare_scans(db, scan_id, baseline_scan_id, current_user.id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scan not found",
        )

    return _to_regression_response(result)


@router.get(
    "/{scan_id}/compare/{baseline_scan_id}/report/pdf",
    summary="Download regression comparison PDF report",
    responses={
        200: {
            "content": {"application/pdf": {}},
            "description": "PDF comparison report",
        }
    },
)
def download_comparison_report_pdf(
    scan_id: int,
    baseline_scan_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Response:
    if scan_id == baseline_scan_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Baseline and current scan must be different",
        )

    try:
        result = compare_scans(db, scan_id, baseline_scan_id, current_user.id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scan not found",
        )

    try:
        pdf_bytes = generate_comparison_report_pdf(result)
    except ReportServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc

    filename = f"comparison-report-{baseline_scan_id}-vs-{scan_id}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
        },
    )


def _to_regression_finding(item) -> RegressionFindingItem:
    return RegressionFindingItem(
        id=item.id,
        title=item.title,
        category=item.category,
        severity=item.severity,
        risk_score=item.risk_score,
        risk_level=item.risk_level,
        endpoint=item.endpoint,
        method=item.method,
        path=item.path,
        fingerprint=item.fingerprint,
    )


def _to_regression_response(result) -> RegressionResponse:
    return RegressionResponse(
        baseline_scan=RegressionScanInfo(
            id=result.baseline_scan.id,
            name=result.baseline_scan.name,
            status=result.baseline_scan.status,
            overall_risk_score=result.baseline_scan.overall_risk_score,
            overall_risk_level=result.baseline_scan.overall_risk_level,
            finding_count=result.baseline_scan.finding_count,
        ),
        current_scan=RegressionScanInfo(
            id=result.current_scan.id,
            name=result.current_scan.name,
            status=result.current_scan.status,
            overall_risk_score=result.current_scan.overall_risk_score,
            overall_risk_level=result.current_scan.overall_risk_level,
            finding_count=result.current_scan.finding_count,
        ),
        baseline_risk_score=result.baseline_risk_score,
        current_risk_score=result.current_risk_score,
        risk_score_change=result.risk_score_change,
        baseline_risk_level=result.baseline_risk_level,
        current_risk_level=result.current_risk_level,
        new_findings=[_to_regression_finding(item) for item in result.new_findings],
        resolved_findings=[_to_regression_finding(item) for item in result.resolved_findings],
        persistent_findings=[
            _to_regression_finding(item) for item in result.persistent_findings
        ],
        new_critical_count=result.new_critical_count,
        resolved_critical_count=result.resolved_critical_count,
        posture=result.posture,
        summary=result.summary,
    )


def _to_finding_response(finding) -> FindingResponse:
    return FindingResponse(
        id=finding.id,
        title=finding.title,
        severity=finding.severity,
        category=finding.category,
        owasp_category=finding.owasp_category,
        endpoint=format_finding_endpoint(finding),
        evidence=finding.evidence,
        structured_evidence=finding.structured_evidence,
        confidence=finding.confidence,
        remediation=finding.remediation,
        risk_score=finding.risk_score,
        risk_level=finding.risk_level,
        risk_factors=finding.risk_factors,
        ai_analysis=(
            FindingAIAnalysisSummary(
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
            if finding.ai_summary
            else None
        ),
    )


def validate_upload_file(file: UploadFile) -> None:
    if file.content_type and file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported file type",
        )

    if file.filename:
        extension = file.filename.lower().rsplit(".", maxsplit=1)
        if len(extension) == 2 and f".{extension[1]}" not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unsupported file type",
            )
