from pathlib import Path

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.core.scan_status import COMPLETED, FAILED, PARSING, PENDING
from app.models.endpoint import Endpoint
from app.models.finding import Finding
from app.models.scan import Scan
from app.models.user import User
from app.services.openapi_service import parse_openapi_document
from app.services.scan_summary_service import build_scan_summary, endpoint_finding_counts
from app.utils.openapi_parser import OpenAPIParserError, ParsedOpenAPI
from app.utils.pagination import normalize_pagination, offset_for, pagination_meta


def get_scan_for_user(db: Session, scan_id: int, user_id: int) -> Scan | None:
    return db.scalar(
        select(Scan).where(Scan.id == scan_id, Scan.user_id == user_id)
    )


def list_scans_for_user(
    db: Session,
    user_id: int,
    *,
    page: int = 1,
    page_size: int = 20,
    status: str | None = None,
    risk_level: str | None = None,
) -> tuple[list[tuple[Scan, int, int]], dict[str, int]]:
    page, page_size = normalize_pagination(page, page_size)

    endpoint_counts = (
        select(Endpoint.scan_id, func.count(Endpoint.id).label("endpoint_count"))
        .group_by(Endpoint.scan_id)
        .subquery()
    )
    finding_counts = (
        select(Finding.scan_id, func.count(Finding.id).label("finding_count"))
        .group_by(Finding.scan_id)
        .subquery()
    )

    filters = [Scan.user_id == user_id]
    if status:
        filters.append(Scan.status == status.upper())
    if risk_level:
        filters.append(Scan.overall_risk_level == risk_level.upper())

    total = int(db.scalar(select(func.count(Scan.id)).where(*filters)) or 0)

    rows = db.execute(
        select(
            Scan,
            func.coalesce(endpoint_counts.c.endpoint_count, 0),
            func.coalesce(finding_counts.c.finding_count, 0),
        )
        .outerjoin(endpoint_counts, Scan.id == endpoint_counts.c.scan_id)
        .outerjoin(finding_counts, Scan.id == finding_counts.c.scan_id)
        .where(*filters)
        .order_by(Scan.created_at.desc(), Scan.id.desc())
        .offset(offset_for(page, page_size))
        .limit(page_size)
    ).all()

    items = [
        (scan, int(endpoint_count), int(finding_count))
        for scan, endpoint_count, finding_count in rows
    ]
    return items, pagination_meta(total, page, page_size)


def get_scan_detail(db: Session, scan_id: int, user_id: int) -> tuple[Scan, object] | None:
    scan = get_scan_for_user(db, scan_id, user_id)
    if scan is None:
        return None
    return scan, build_scan_summary(db, scan)


def list_endpoints_for_scan(
    db: Session,
    scan_id: int,
    user_id: int,
    *,
    page: int = 1,
    page_size: int = 50,
) -> tuple[list[tuple[Endpoint, int]], dict[str, int]] | None:
    if get_scan_for_user(db, scan_id, user_id) is None:
        return None

    page, page_size = normalize_pagination(page, page_size)
    total = int(
        db.scalar(select(func.count(Endpoint.id)).where(Endpoint.scan_id == scan_id)) or 0
    )
    endpoints = list(
        db.scalars(
            select(Endpoint)
            .where(Endpoint.scan_id == scan_id)
            .order_by(Endpoint.path, Endpoint.method)
            .offset(offset_for(page, page_size))
            .limit(page_size)
        ).all()
    )
    counts = endpoint_finding_counts(db, scan_id)
    items = [(endpoint, counts.get(endpoint.id, 0)) for endpoint in endpoints]
    return items, pagination_meta(total, page, page_size)


def delete_scan_for_user(db: Session, scan_id: int, user_id: int) -> bool:
    scan = db.scalar(
        select(Scan)
        .options(selectinload(Scan.findings), selectinload(Scan.endpoints))
        .where(Scan.id == scan_id, Scan.user_id == user_id)
    )
    if scan is None:
        return False

    db.delete(scan)
    db.commit()
    return True


def create_scan_from_upload(
    db: Session,
    user: User,
    content: bytes,
    source_filename: str | None,
    name: str | None,
) -> Scan:
    scan_name = name or sanitize_display_name(source_filename)
    scan = Scan(
        user_id=user.id,
        name=scan_name,
        source_filename=sanitize_display_name(source_filename),
        status=PENDING,
    )
    db.add(scan)
    db.commit()
    db.refresh(scan)

    scan.status = PARSING
    db.commit()

    try:
        parsed = parse_openapi_document(content)
        _apply_parsed_spec(db, scan, parsed)
        # Parsed successfully and ready for deterministic security scanning.
        scan.status = PENDING
    except OpenAPIParserError:
        scan.status = FAILED
        db.commit()
        raise

    db.commit()
    db.refresh(scan)
    return scan


def _apply_parsed_spec(db: Session, scan: Scan, parsed: ParsedOpenAPI) -> None:
    scan.specification_version = parsed.specification_version
    scan.title = parsed.title
    scan.description = parsed.description
    scan.version = parsed.version
    scan.spec_metadata = parsed.spec_metadata

    for item in parsed.endpoints:
        db.add(
            Endpoint(
                scan_id=scan.id,
                path=item.path,
                method=item.method,
                summary=item.summary,
                description=item.description,
                operation_id=item.operation_id,
                tags=item.tags,
                parameters=item.parameters,
                request_body=item.request_body,
                responses=item.responses,
                security_defined=item.security_defined,
                security_requirements=item.security_requirements,
            )
        )


def sanitize_display_name(filename: str | None) -> str:
    if not filename:
        return "upload"

    cleaned = Path(filename).name.strip()
    return cleaned or "upload"


def build_spec_metadata_summary(scan: Scan) -> dict:
    return {
        "title": scan.title,
        "version": scan.version,
        "openapi_version": scan.specification_version,
        "description": scan.description,
    }
