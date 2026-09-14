from app.scanner.engine import ScannerEngine
from tests.scanner_helpers import make_context, make_endpoint


def test_engine_runs_all_scanners_on_demo_like_endpoints() -> None:
    endpoints = [
        make_endpoint(1, "/users", security_defined=False),
        make_endpoint(2, "/users/{id}", security_defined=False),
        make_endpoint(3, "/login", method="POST", summary="Login", security_defined=False),
    ]
    findings = ScannerEngine().run(make_context(endpoints))

    categories = {finding.category for finding in findings}
    assert "Authentication" in categories
    assert "Authorization" in categories
    assert "Rate Limiting" in categories
