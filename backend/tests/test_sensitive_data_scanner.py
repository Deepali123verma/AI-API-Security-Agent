from app.scanner.sensitive_data_scanner import SensitiveDataScanner
from tests.scanner_helpers import make_context, make_endpoint


def test_password_in_response_schema_generates_finding() -> None:
    endpoint = make_endpoint(
        1,
        "/users",
        responses={
            "200": {
                "description": "OK",
                "content": {
                    "application/json": {
                        "schema": {
                            "type": "object",
                            "properties": {"password": {"type": "string"}},
                        }
                    }
                },
            }
        },
    )
    findings = SensitiveDataScanner().scan(make_context([endpoint]))

    assert len(findings) == 1
    assert findings[0].severity == "HIGH"


def test_access_token_in_response_generates_finding() -> None:
    endpoint = make_endpoint(
        1,
        "/token",
        responses={
            "200": {
                "description": "OK",
                "content": {
                    "application/json": {
                        "schema": {
                            "type": "object",
                            "properties": {"access_token": {"type": "string"}},
                        }
                    }
                },
            }
        },
    )
    findings = SensitiveDataScanner().scan(make_context([endpoint]))

    assert len(findings) == 1
    assert "access_token" in findings[0].evidence


def test_sensitive_field_only_in_request_has_lower_severity() -> None:
    endpoint = make_endpoint(
        1,
        "/register",
        method="POST",
        request_body={
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {"password": {"type": "string"}},
                    }
                }
            }
        },
    )
    findings = SensitiveDataScanner().scan(make_context([endpoint]))

    assert len(findings) == 1
    assert findings[0].severity == "LOW"


def test_case_insensitive_field_detection() -> None:
    endpoint = make_endpoint(
        1,
        "/secrets",
        responses={
            "200": {
                "description": "OK",
                "content": {
                    "application/json": {
                        "schema": {
                            "type": "object",
                            "properties": {"API_KEY": {"type": "string"}},
                        }
                    }
                },
            }
        },
    )
    findings = SensitiveDataScanner().scan(make_context([endpoint]))

    assert len(findings) == 1
