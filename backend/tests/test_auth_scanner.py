from app.scanner.auth_scanner import AuthenticationScanner
from tests.scanner_helpers import make_context, make_endpoint


def test_sensitive_endpoint_without_security_generates_finding() -> None:
    endpoint = make_endpoint(1, "/admin/users", security_defined=False)
    findings = AuthenticationScanner().scan(make_context([endpoint]))

    assert len(findings) == 1
    assert findings[0].title == "Potential Missing Authentication"


def test_public_health_endpoint_has_no_finding() -> None:
    endpoint = make_endpoint(1, "/health", security_defined=False)
    findings = AuthenticationScanner().scan(make_context([endpoint]))

    assert findings == []


def test_endpoint_with_global_security_has_no_finding() -> None:
    endpoint = make_endpoint(1, "/users", security_defined=True)
    findings = AuthenticationScanner().scan(make_context([endpoint]))

    assert findings == []


def test_endpoint_with_operation_level_security_has_no_finding() -> None:
    endpoint = make_endpoint(
        1,
        "/users/{id}",
        security_defined=True,
        security_requirements=[{"bearerAuth": []}],
    )
    findings = AuthenticationScanner().scan(make_context([endpoint]))

    assert findings == []
