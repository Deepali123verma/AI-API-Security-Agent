from app.models.endpoint import Endpoint
from app.models.scan import Scan
from app.scanner.models import ScanContext


def make_endpoint(
    endpoint_id: int,
    path: str,
    method: str = "GET",
    *,
    security_defined: bool = False,
    security_requirements: list | None = None,
    summary: str | None = None,
    operation_id: str | None = None,
    parameters: list | None = None,
    request_body: dict | None = None,
    responses: dict | None = None,
) -> Endpoint:
    return Endpoint(
        id=endpoint_id,
        scan_id=1,
        path=path,
        method=method,
        summary=summary,
        operation_id=operation_id,
        parameters=parameters,
        request_body=request_body,
        responses=responses,
        security_defined=security_defined,
        security_requirements=security_requirements,
    )


def make_context(
    endpoints: list[Endpoint],
    spec_metadata: dict | None = None,
) -> ScanContext:
    scan = Scan(
        id=1,
        user_id=1,
        name="Test Scan",
        source_filename="test.yaml",
        status="completed",
        spec_metadata=spec_metadata,
    )
    return ScanContext(
        scan=scan,
        endpoints=endpoints,
        spec_metadata=spec_metadata or {},
    )
