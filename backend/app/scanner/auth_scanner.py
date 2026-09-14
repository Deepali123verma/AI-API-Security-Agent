from app.models.endpoint import Endpoint
from app.scanner.base import BaseScanner
from app.scanner.helpers import (
    endpoint_label,
    is_public_endpoint,
    is_sensitive_endpoint,
)
from app.scanner.models import ScanContext, ScannerFinding


class AuthenticationScanner(BaseScanner):
    name = "authentication"

    def scan(self, context: ScanContext) -> list[ScannerFinding]:
        findings: list[ScannerFinding] = []

        for endpoint in context.endpoints:
            finding = self._analyze_endpoint(endpoint)
            if finding is not None:
                findings.append(finding)

        return findings

    def _analyze_endpoint(self, endpoint: Endpoint) -> ScannerFinding | None:
        label = endpoint_label(endpoint)

        if endpoint.security_defined:
            return None

        if is_public_endpoint(endpoint):
            return None

        if not is_sensitive_endpoint(endpoint):
            return None

        return ScannerFinding(
            title="Potential Missing Authentication",
            description=(
                "This potentially sensitive endpoint does not declare an authentication "
                "requirement in the OpenAPI specification."
            ),
            severity="HIGH",
            category="Authentication",
            owasp_category="API2:2023 Broken Authentication",
            evidence=(
                f"No security requirement is defined for this operation: {label}. "
                "The path appears sensitive based on static path analysis."
            ),
            remediation=(
                "Require authentication for this endpoint and document the security "
                "requirement in the OpenAPI specification."
            ),
            confidence="HIGH",
            endpoint_id=endpoint.id,
            endpoint_label=label,
        )
