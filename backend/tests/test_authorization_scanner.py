from app.scanner.authorization_scanner import AuthorizationScanner
from tests.scanner_helpers import make_context, make_endpoint


def test_users_id_path_generates_bola_finding() -> None:
    endpoint = make_endpoint(1, "/users/{id}")
    findings = AuthorizationScanner().scan(make_context([endpoint]))

    assert len(findings) == 1
    assert findings[0].title == "Potential BOLA / IDOR Risk"
    assert "requiring authorization testing" in findings[0].description


def test_orders_order_id_path_generates_bola_finding() -> None:
    endpoint = make_endpoint(1, "/orders/{order_id}", method="GET")
    findings = AuthorizationScanner().scan(make_context([endpoint]))

    assert len(findings) == 1
    assert findings[0].endpoint_label == "GET /orders/{order_id}"


def test_endpoint_without_object_identifier_has_no_bola_finding() -> None:
    endpoint = make_endpoint(1, "/status")
    findings = AuthorizationScanner().scan(make_context([endpoint]))

    assert findings == []
