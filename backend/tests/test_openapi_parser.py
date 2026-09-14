from pathlib import Path

import pytest

from app.utils.openapi_parser import OpenAPIParserError, parse_spec_content

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def test_parser_discovers_demo_store_endpoints() -> None:
    content = (FIXTURES_DIR / "demo_store.yaml").read_bytes()
    parsed = parse_spec_content(content)

    discovered = {(endpoint.method, endpoint.path) for endpoint in parsed.endpoints}
    assert parsed.title == "Demo Store API"
    assert len(parsed.endpoints) == 3
    assert discovered == {
        ("GET", "/users"),
        ("GET", "/users/{id}"),
        ("POST", "/login"),
    }


def test_parser_extracts_security_metadata() -> None:
    content = (FIXTURES_DIR / "security_metadata.yaml").read_bytes()
    parsed = parse_spec_content(content)
    endpoints = {f"{item.method} {item.path}": item for item in parsed.endpoints}

    assert endpoints["GET /public/status"].security_defined is False
    assert endpoints["GET /users"].security_defined is True
    assert endpoints["GET /admin/users"].security_defined is True
    assert endpoints["GET /admin/users"].security_requirements == [{"bearerAuth": ["admin"]}]


def test_parser_rejects_non_openapi_json() -> None:
    with pytest.raises(OpenAPIParserError, match="Not a valid OpenAPI"):
        parse_spec_content(b'{"hello": "world"}')
