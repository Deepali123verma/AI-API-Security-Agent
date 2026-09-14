import re
from typing import Any

from app.models.endpoint import Endpoint
from app.scanner.helpers import (
    OBJECT_ID_PATH_PATTERN,
    has_object_identifier,
    is_sensitive_field_name,
    iter_endpoint_parameters,
    iter_endpoint_request_fields,
    iter_endpoint_response_fields,
)
from app.scanner.models import ScannerFinding
from app.scoring.rules import (
    AUTHENTICATION_CATEGORIES,
    AUTHORIZATION_CATEGORIES,
    ENDPOINT_SENSITIVITY_HIGH_TERMS,
    ENDPOINT_SENSITIVITY_MEDIUM_TERMS,
    SENSITIVE_DATA_CATEGORIES,
    STATE_CHANGING_METHODS,
)

SENSITIVE_FIELD_PATTERN = re.compile(r"Suspicious field '([^']+)' found in ([^ ]+(?: [^ ]+)*) for")


def endpoint_sensitivity(path: str) -> str:
    lowered = path.lower()
    if any(term in lowered for term in ENDPOINT_SENSITIVITY_HIGH_TERMS):
        return "HIGH"
    if any(term in lowered for term in ENDPOINT_SENSITIVITY_MEDIUM_TERMS):
        return "MEDIUM"
    return "NORMAL"


def extract_object_identifier(path: str) -> str | None:
    match = OBJECT_ID_PATH_PATTERN.search(path)
    if match:
        return match.group(1)
    return None


def detect_sensitive_data_context(
    finding: ScannerFinding,
    endpoint: Endpoint | None,
) -> tuple[bool, bool]:
    """Return (response_exposure, request_exposure)."""
    if endpoint is None:
        return _sensitive_from_evidence(finding.evidence)

    response_exposure = False
    request_exposure = False

    for _location, field_name, _field_type in iter_endpoint_response_fields(endpoint):
        if is_sensitive_field_name(field_name):
            response_exposure = True

    for _location, field_name, _field_type in iter_endpoint_request_fields(endpoint):
        if is_sensitive_field_name(field_name):
            request_exposure = True

    for _location, field_name, _field_type in iter_endpoint_parameters(endpoint):
        if is_sensitive_field_name(field_name):
            request_exposure = True

    if not response_exposure and not request_exposure:
        return _sensitive_from_evidence(finding.evidence)

    return response_exposure, request_exposure


def _sensitive_from_evidence(evidence: str) -> tuple[bool, bool]:
    match = SENSITIVE_FIELD_PATTERN.search(evidence)
    if not match:
        return False, False

    location = match.group(2).lower()
    if location.startswith("response"):
        return True, False
    return False, True


def category_to_finding_type(category: str) -> str:
    mapping = {
        "Authentication": "authentication",
        "Authorization": "authorization",
        "Sensitive Data": "sensitive_data",
        "Rate Limiting": "rate_limiting",
        "Configuration": "configuration",
        "Injection": "injection",
    }
    return mapping.get(category, category.lower().replace(" ", "_"))


def build_structured_evidence(
    finding: ScannerFinding,
    endpoint: Endpoint | None,
) -> dict[str, Any]:
    finding_type = category_to_finding_type(finding.category)
    evidence: dict[str, Any] = {
        "finding_type": finding_type,
        "text_evidence": finding.evidence,
    }

    if endpoint is not None:
        evidence.update(
            {
                "endpoint": f"{endpoint.method} {endpoint.path}",
                "method": endpoint.method,
                "path": endpoint.path,
                "security_declared": endpoint.security_defined,
            }
        )

    if finding.category in AUTHORIZATION_CATEGORIES and endpoint is not None:
        object_identifier = extract_object_identifier(endpoint.path)
        if object_identifier:
            evidence["object_identifier"] = object_identifier

    if finding.category in AUTHENTICATION_CATEGORIES and endpoint is not None:
        evidence["authentication_context"] = (
            "DOCUMENTED" if endpoint.security_defined else "MISSING"
        )

    if finding.category in SENSITIVE_DATA_CATEGORIES:
        match = SENSITIVE_FIELD_PATTERN.search(finding.evidence)
        if match:
            evidence["field"] = match.group(1)
            location = match.group(2)
            evidence["location"] = "response" if location.lower().startswith("response") else "request"
            evidence["schema_location"] = location

    if finding.category == "Rate Limiting" and endpoint is not None:
        evidence["rate_limit_documented"] = False

    if finding.category == "Injection":
        match = re.search(r"input '([^']+)'", finding.evidence)
        if match:
            evidence["input_field"] = match.group(1)

    if finding.category == "Configuration":
        evidence["configuration_issue"] = finding.title

    return evidence
