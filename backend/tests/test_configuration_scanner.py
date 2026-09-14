from app.scanner.configuration_scanner import ConfigurationScanner
from tests.scanner_helpers import make_context, make_endpoint


def test_missing_security_configuration_generates_finding() -> None:
    metadata = {
        "security_schemes": {"bearerAuth": {"type": "http", "scheme": "bearer"}},
        "global_security": None,
    }
    endpoint = make_endpoint(1, "/status", security_defined=False)
    findings = ConfigurationScanner().scan(make_context([endpoint], metadata))

    assert any("Security schemes exist" in finding.evidence for finding in findings)


def test_proper_bearer_security_scheme_is_recognized_without_false_positive() -> None:
    metadata = {
        "security_schemes": {"bearerAuth": {"type": "http", "scheme": "bearer"}},
        "global_security": [{"bearerAuth": []}],
    }
    endpoint = make_endpoint(1, "/users", security_defined=True)
    findings = ConfigurationScanner().scan(make_context([endpoint], metadata))

    assert findings == []


def test_insecure_http_server_generates_finding() -> None:
    metadata = {"servers": [{"url": "http://api.example.com"}]}
    findings = ConfigurationScanner().scan(make_context([], metadata))

    assert len(findings) == 1
    assert "HTTP" in findings[0].evidence
