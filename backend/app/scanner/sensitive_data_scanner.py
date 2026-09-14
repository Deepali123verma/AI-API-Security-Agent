from app.models.endpoint import Endpoint
from app.scanner.base import BaseScanner
from app.scanner.helpers import (
    endpoint_label,
    is_sensitive_field_name,
    iter_endpoint_parameters,
    iter_endpoint_request_fields,
    iter_endpoint_response_fields,
)
from app.scanner.models import ScanContext, ScannerFinding


class SensitiveDataScanner(BaseScanner):
    name = "sensitive_data"

    def scan(self, context: ScanContext) -> list[ScannerFinding]:
        findings: list[ScannerFinding] = []

        for endpoint in context.endpoints:
            findings.extend(self._scan_endpoint(endpoint))

        return findings

    def _scan_endpoint(self, endpoint: Endpoint) -> list[ScannerFinding]:
        findings: list[ScannerFinding] = []
        label = endpoint_label(endpoint)
        seen: set[tuple[str, str, str]] = set()

        for location, field_name, _field_type in iter_endpoint_response_fields(endpoint):
            key = ("response", location, field_name.lower())
            if key in seen or not is_sensitive_field_name(field_name):
                continue
            seen.add(key)
            findings.append(
                self._build_finding(
                    endpoint=endpoint,
                    label=label,
                    field_name=field_name,
                    location=location,
                    in_response=True,
                )
            )

        for location, field_name, _field_type in iter_endpoint_request_fields(endpoint):
            key = ("request", location, field_name.lower())
            if key in seen or not is_sensitive_field_name(field_name):
                continue
            seen.add(key)
            findings.append(
                self._build_finding(
                    endpoint=endpoint,
                    label=label,
                    field_name=field_name,
                    location=location,
                    in_response=False,
                )
            )

        for location, field_name, _field_type in iter_endpoint_parameters(endpoint):
            key = ("parameter", location, field_name.lower())
            if key in seen or not is_sensitive_field_name(field_name):
                continue
            seen.add(key)
            findings.append(
                self._build_finding(
                    endpoint=endpoint,
                    label=label,
                    field_name=field_name,
                    location=f"{location} parameter",
                    in_response=False,
                )
            )

        return findings

    def _build_finding(
        self,
        endpoint: Endpoint,
        label: str,
        field_name: str,
        location: str,
        in_response: bool,
    ) -> ScannerFinding:
        if in_response:
            severity = "HIGH"
            confidence = "HIGH"
            description = (
                "A potentially sensitive field appears in a documented API response schema. "
                "This may indicate possible sensitive data exposure and requires verification."
            )
            evidence = (
                f"Suspicious field '{field_name}' found in {location} for {label}."
            )
            remediation = (
                "Avoid returning sensitive fields in API responses. Mask, omit, or protect "
                "sensitive data and document safe response schemas."
            )
        else:
            severity = "LOW"
            confidence = "MEDIUM"
            description = (
                "A potentially sensitive field appears in a request schema or parameter. "
                "This is not necessarily a vulnerability but should be reviewed."
            )
            evidence = (
                f"Suspicious field '{field_name}' found in {location} for {label}."
            )
            remediation = (
                "Ensure sensitive request fields are handled securely and never echoed "
                "back in responses."
            )

        return ScannerFinding(
            title="Potential Sensitive Data Exposure",
            description=description,
            severity=severity,
            category="Sensitive Data",
            owasp_category="API3:2023 Broken Object Property Level Authorization",
            evidence=evidence,
            remediation=remediation,
            confidence=confidence,
            endpoint_id=endpoint.id,
            endpoint_label=label,
        )
