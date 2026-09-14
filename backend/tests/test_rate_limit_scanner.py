from app.scanner.rate_limit_scanner import RateLimitScanner
from tests.scanner_helpers import make_context, make_endpoint


def test_login_without_documented_rate_limiting_generates_finding() -> None:
    endpoint = make_endpoint(1, "/login", method="POST", summary="Login")
    findings = RateLimitScanner().scan(make_context([endpoint]))

    assert len(findings) == 1
    assert findings[0].title == "Potential Missing Rate Limiting"


def test_normal_get_endpoint_has_no_rate_limit_finding() -> None:
    endpoint = make_endpoint(1, "/items", method="GET")
    findings = RateLimitScanner().scan(make_context([endpoint]))

    assert findings == []
