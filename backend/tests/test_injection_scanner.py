from app.scanner.injection_scanner import InjectionScanner
from tests.scanner_helpers import make_context, make_endpoint


def test_search_query_parameter_generates_injection_finding() -> None:
    endpoint = make_endpoint(
        1,
        "/items",
        parameters=[{"name": "search", "in": "query", "schema": {"type": "string"}}],
    )
    findings = InjectionScanner().scan(make_context([endpoint]))

    assert len(findings) == 1
    assert findings[0].title == "Potential Injection Risk"


def test_normal_numeric_parameter_has_no_injection_finding() -> None:
    endpoint = make_endpoint(
        1,
        "/items",
        parameters=[{"name": "id", "in": "query", "schema": {"type": "integer"}}],
    )
    findings = InjectionScanner().scan(make_context([endpoint]))

    assert findings == []
