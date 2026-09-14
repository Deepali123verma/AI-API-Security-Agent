import json
from dataclasses import dataclass
from typing import Any

import yaml
from openapi_spec_validator import validate
from openapi_spec_validator.validation.exceptions import OpenAPIValidationError

HTTP_METHODS = frozenset({"get", "post", "put", "patch", "delete", "head", "options"})
OPENAPI_VERSION_KEYS = ("openapi", "swagger")


class OpenAPIParserError(Exception):
    """Raised when uploaded content is not a valid OpenAPI specification."""


@dataclass
class ParsedEndpoint:
    path: str
    method: str
    summary: str | None
    description: str | None
    operation_id: str | None
    tags: list[str]
    parameters: list[dict[str, Any]] | None
    request_body: dict[str, Any] | None
    responses: dict[str, Any] | None
    security_defined: bool
    security_requirements: list[dict[str, Any]] | None


@dataclass
class ParsedOpenAPI:
    specification_version: str
    title: str | None
    description: str | None
    version: str | None
    endpoints: list[ParsedEndpoint]
    spec_metadata: dict[str, Any]


def parse_spec_content(content: bytes) -> ParsedOpenAPI:
    text = decode_content(content)
    spec = load_json_or_yaml(text)
    validate_openapi_spec(spec)
    metadata = extract_metadata(spec)
    endpoints = discover_endpoints(spec)
    spec_metadata = extract_spec_metadata(spec)
    return ParsedOpenAPI(endpoints=endpoints, spec_metadata=spec_metadata, **metadata)


def decode_content(content: bytes) -> str:
    if not content:
        raise OpenAPIParserError("Empty file")

    for encoding in ("utf-8", "utf-8-sig", "latin-1"):
        try:
            return content.decode(encoding)
        except UnicodeDecodeError:
            continue

    raise OpenAPIParserError("Invalid file encoding")


def load_json_or_yaml(text: str) -> dict[str, Any]:
    stripped = text.strip()
    if not stripped:
        raise OpenAPIParserError("Empty file")

    data: Any
    if stripped.startswith("{") or stripped.startswith("["):
        try:
            data = json.loads(stripped)
        except json.JSONDecodeError:
            try:
                data = yaml.safe_load(stripped)
            except yaml.YAMLError as exc:
                raise OpenAPIParserError("Invalid JSON or YAML") from exc
    else:
        try:
            data = yaml.safe_load(stripped)
        except yaml.YAMLError as exc:
            raise OpenAPIParserError("Invalid YAML") from exc

    if not isinstance(data, dict):
        raise OpenAPIParserError("Specification must be a JSON or YAML object")

    return data


def validate_openapi_spec(spec: dict[str, Any]) -> None:
    if not any(key in spec for key in OPENAPI_VERSION_KEYS):
        raise OpenAPIParserError("Not a valid OpenAPI or Swagger specification")

    version = str(spec.get("openapi") or spec.get("swagger", ""))
    major_version = version.split(".", maxsplit=1)[0]
    if major_version not in {"2", "3"}:
        raise OpenAPIParserError(f"Unsupported specification version: {version}")

    try:
        validate(spec)
    except OpenAPIValidationError as exc:
        raise OpenAPIParserError("Invalid OpenAPI specification") from exc


def extract_metadata(spec: dict[str, Any]) -> dict[str, str | None]:
    info = spec.get("info", {})
    if not isinstance(info, dict):
        info = {}

    return {
        "specification_version": str(spec.get("openapi") or spec.get("swagger") or ""),
        "title": info.get("title"),
        "description": info.get("description"),
        "version": info.get("version"),
    }


def discover_endpoints(spec: dict[str, Any]) -> list[ParsedEndpoint]:
    paths = spec.get("paths", {})
    if not isinstance(paths, dict):
        return []

    endpoints: list[ParsedEndpoint] = []
    for path, path_item in paths.items():
        if not isinstance(path_item, dict):
            continue

        for key, operation in path_item.items():
            if key.lower() not in HTTP_METHODS:
                continue
            if not isinstance(operation, dict):
                continue

            security_defined, security_requirements = resolve_security(spec, operation)
            endpoints.append(
                ParsedEndpoint(
                    path=path,
                    method=key.upper(),
                    summary=operation.get("summary"),
                    description=operation.get("description"),
                    operation_id=operation.get("operationId"),
                    tags=operation.get("tags") or [],
                    parameters=collect_parameters(path_item, operation),
                    request_body=collect_request_body(operation),
                    responses=collect_responses(operation),
                    security_defined=security_defined,
                    security_requirements=security_requirements,
                )
            )

    return endpoints


def resolve_security(
    spec: dict[str, Any],
    operation: dict[str, Any],
) -> tuple[bool, list[dict[str, Any]] | None]:
    if "security" in operation:
        requirements = operation["security"]
        if not isinstance(requirements, list):
            return False, None
        return len(requirements) > 0, requirements or None

    global_security = spec.get("security")
    if global_security is not None:
        if not isinstance(global_security, list):
            return False, None
        return len(global_security) > 0, global_security or None

    return False, None


def collect_parameters(
    path_item: dict[str, Any],
    operation: dict[str, Any],
) -> list[dict[str, Any]] | None:
    parameters: list[dict[str, Any]] = []
    for source in (path_item.get("parameters"), operation.get("parameters")):
        if isinstance(source, list):
            parameters.extend(item for item in source if isinstance(item, dict))
    return parameters or None


def collect_request_body(operation: dict[str, Any]) -> dict[str, Any] | None:
    request_body = operation.get("requestBody")
    if isinstance(request_body, dict):
        return request_body

    for parameter in operation.get("parameters") or []:
        if isinstance(parameter, dict) and parameter.get("in") == "body":
            return parameter

    return None


def collect_responses(operation: dict[str, Any]) -> dict[str, Any] | None:
    responses = operation.get("responses")
    if isinstance(responses, dict) and responses:
        return responses
    return None


def extract_spec_metadata(spec: dict[str, Any]) -> dict[str, Any]:
    security_schemes: dict[str, Any] = {}
    components = spec.get("components")
    if isinstance(components, dict):
        schemes = components.get("securitySchemes")
        if isinstance(schemes, dict):
            security_schemes = schemes

    legacy_schemes = spec.get("securityDefinitions")
    if isinstance(legacy_schemes, dict):
        security_schemes = {**security_schemes, **legacy_schemes}

    return {
        "global_security": spec.get("security"),
        "security_schemes": security_schemes,
        "servers": spec.get("servers"),
        "schemes": spec.get("schemes"),
        "host": spec.get("host"),
        "base_path": spec.get("basePath"),
    }
