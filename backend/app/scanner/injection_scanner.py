from app.models.endpoint import Endpoint
from app.scanner.base import BaseScanner
from app.scanner.helpers import (
    INJECTION_PARAM_NAMES,
    endpoint_label,
    iter_endpoint_parameters,
    iter_endpoint_request_fields,
)
from app.scanner.models import ScanContext, ScannerFinding


class InjectionScanner(BaseScanner):
    name = "injection"

    def scan(self, context: ScanContext) -> list[ScannerFinding]:
        findings: list[ScannerFinding] = []

        for endpoint in context.endpoints:
            findings.extend(self._scan_endpoint(endpoint))

        return findings

    def _scan_endpoint(self, endpoint: Endpoint) -> list[ScannerFinding]:
        findings: list[ScannerFinding] = []
        label = endpoint_label(endpoint)
        seen: set[str] = set()

        for location, name, _param_type in iter_endpoint_parameters(endpoint):
            if location != "query":
                continue
            normalized = name.lower()
            if normalized not in INJECTION_PARAM_NAMES or normalized in seen:
                continue
            seen.add(normalized)
            findings.append(self._build_finding(endpoint, label, name, f"query parameter '{name}'"))

        for location, field_name, _field_type in iter_endpoint_request_fields(endpoint):
            normalized = field_name.lower()
            if normalized not in INJECTION_PARAM_NAMES or normalized in seen:
                continue
            seen.add(normalized)
            findings.append(
                self._build_finding(endpoint, label, field_name, f"request field '{field_name}' in {location}")
            )

        return findings

    def _build_finding(
        self,
        endpoint: Endpoint,
        label: str,
        field_name: str,
        location_description: str,
    ) -> ScannerFinding:
        return ScannerFinding(
            title="Potential Injection Risk",
            description=(
                "This endpoint accepts input that may require strict validation and safe "
                "parameterized handling. Injection cannot be confirmed from the OpenAPI "
                "document alone."
            ),
            severity="MEDIUM",
            category="Injection",
            owasp_category="API10:2023 Unsafe Consumption of APIs",
            evidence=(
                f"Potentially dangerous input '{field_name}' is accepted via "
                f"{location_description} on {label}."
            ),
            remediation=(
                "Validate and sanitize user input, use parameterized queries, and verify "
                "safe handling through code review and runtime testing."
            ),
            confidence="LOW",
            endpoint_id=endpoint.id,
            endpoint_label=label,
        )
