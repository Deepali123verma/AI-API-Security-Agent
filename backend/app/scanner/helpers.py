import re
from typing import Any, Iterator

from app.models.endpoint import Endpoint

HTTP_METHODS = frozenset({"GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"})

PUBLIC_PATH_TERMS = (
    "/health",
    "/healthz",
    "/ready",
    "/live",
    "/docs",
    "/swagger",
    "/openapi",
    "/login",
    "/register",
    "/signin",
    "/signup",
)

SENSITIVE_PATH_TERMS = (
    "/admin",
    "/users",
    "/accounts",
    "/profile",
    "/orders",
    "/payments",
    "/password",
    "/settings",
)

OBJECT_ID_PATH_PATTERN = re.compile(
    r"\{(id|user_id|userid|order_id|orderid|account_id|accountid|resource_id)\}",
    re.IGNORECASE,
)

OBJECT_ID_PARAM_NAMES = frozenset(
    {
        "id",
        "user_id",
        "userid",
        "order_id",
        "orderid",
        "account_id",
        "accountid",
        "resource_id",
    }
)

SENSITIVE_FIELD_NAMES = frozenset(
    {
        "password",
        "password_hash",
        "token",
        "access_token",
        "refresh_token",
        "api_key",
        "secret",
        "client_secret",
        "authorization",
        "credit_card",
        "card_number",
        "cvv",
        "ssn",
        "private_key",
    }
)

RATE_LIMIT_PATH_TERMS = (
    "/login",
    "/register",
    "/otp",
    "/verify-otp",
    "/password-reset",
    "/forgot-password",
)

INJECTION_PARAM_NAMES = frozenset(
    {
        "query",
        "search",
        "filter",
        "sort",
        "order",
        "command",
        "filename",
        "url",
        "redirect",
        "template",
        "expression",
    }
)

RATE_LIMIT_INDICATORS = (
    "x-ratelimit",
    "x-rate-limit",
    "rate limit",
    "rate-limit",
    "ratelimit",
)


def endpoint_label(endpoint: Endpoint) -> str:
    return f"{endpoint.method} {endpoint.path}"


def is_public_endpoint(endpoint: Endpoint) -> bool:
    path = endpoint.path.lower()
    operation_id = (endpoint.operation_id or "").lower()
    summary = (endpoint.summary or "").lower()

    if any(term in path for term in PUBLIC_PATH_TERMS):
        return True
    if endpoint.method == "POST" and any(term in path for term in ("/login", "/register")):
        return True
    if "login" in operation_id or "register" in operation_id:
        return True
    if "login" in summary or "register" in summary:
        return True
    return False


def is_sensitive_endpoint(endpoint: Endpoint) -> bool:
    path = endpoint.path.lower()
    return any(term in path for term in SENSITIVE_PATH_TERMS)


def has_object_identifier(endpoint: Endpoint) -> bool:
    if OBJECT_ID_PATH_PATTERN.search(endpoint.path):
        return True

    for parameter in endpoint.parameters or []:
        if not isinstance(parameter, dict):
            continue
        name = str(parameter.get("name", "")).lower()
        location = str(parameter.get("in", "")).lower()
        if location == "path" and name in OBJECT_ID_PARAM_NAMES:
            return True

    return False


def iter_schema_fields(schema: Any, location: str) -> Iterator[tuple[str, str, str]]:
    if not isinstance(schema, dict):
        return

    properties = schema.get("properties")
    if isinstance(properties, dict):
        for field_name, field_schema in properties.items():
            yield location, field_name, str(field_schema.get("type", "object"))
            if isinstance(field_schema, dict):
                yield from iter_schema_fields(field_schema, f"{location}.{field_name}")

    for key in ("allOf", "anyOf", "oneOf"):
        items = schema.get(key)
        if isinstance(items, list):
            for item in items:
                yield from iter_schema_fields(item, location)

    items_schema = schema.get("items")
    if isinstance(items_schema, dict):
        yield from iter_schema_fields(items_schema, f"{location}[]")


def iter_endpoint_response_fields(endpoint: Endpoint) -> Iterator[tuple[str, str, str]]:
    for status_code, response in (endpoint.responses or {}).items():
        if not isinstance(response, dict):
            continue
        location_prefix = f"response {status_code}"

        schema = response.get("schema")
        if isinstance(schema, dict):
            yield from iter_schema_fields(schema, location_prefix)

        content = response.get("content")
        if isinstance(content, dict):
            for media_type, media_object in content.items():
                if not isinstance(media_object, dict):
                    continue
                media_schema = media_object.get("schema")
                if isinstance(media_schema, dict):
                    yield from iter_schema_fields(
                        media_schema,
                        f"{location_prefix} ({media_type})",
                    )


def iter_endpoint_request_fields(endpoint: Endpoint) -> Iterator[tuple[str, str, str]]:
    request_body = endpoint.request_body
    if not isinstance(request_body, dict):
        return

    schema = request_body.get("schema")
    if isinstance(schema, dict):
        yield from iter_schema_fields(schema, "request body")

    content = request_body.get("content")
    if isinstance(content, dict):
        for media_type, media_object in content.items():
            if not isinstance(media_object, dict):
                continue
            media_schema = media_object.get("schema")
            if isinstance(media_schema, dict):
                yield from iter_schema_fields(
                    media_schema,
                    f"request body ({media_type})",
                )


def iter_endpoint_parameters(endpoint: Endpoint) -> Iterator[tuple[str, str, str]]:
    for parameter in endpoint.parameters or []:
        if not isinstance(parameter, dict):
            continue
        name = str(parameter.get("name", ""))
        location = str(parameter.get("in", "parameter"))
        param_type = str((parameter.get("schema") or {}).get("type", "string"))
        yield location, name, param_type


def is_sensitive_field_name(field_name: str) -> bool:
    normalized = field_name.lower().replace("-", "_")
    return normalized in SENSITIVE_FIELD_NAMES


def is_rate_limit_sensitive_endpoint(endpoint: Endpoint) -> bool:
    path = endpoint.path.lower()
    operation_id = (endpoint.operation_id or "").lower()
    if endpoint.method != "POST":
        return False
    if any(term in path for term in RATE_LIMIT_PATH_TERMS):
        return True
    return any(term.strip("/") in operation_id for term in RATE_LIMIT_PATH_TERMS)


def has_documented_rate_limiting(endpoint: Endpoint) -> bool:
    serialized = " ".join(
        [
            str(endpoint.summary or ""),
            str(endpoint.description or ""),
            str(endpoint.responses or {}),
        ]
    ).lower()
    if any(indicator in serialized for indicator in RATE_LIMIT_INDICATORS):
        return True

    for key in (endpoint.responses or {}).keys():
        if isinstance(key, str) and "429" in key:
            return True

    return False


def bola_severity_for_method(method: str) -> str:
    if method in {"DELETE", "PUT", "PATCH"}:
        return "HIGH"
    if method in {"POST"}:
        return "MEDIUM"
    return "MEDIUM"
