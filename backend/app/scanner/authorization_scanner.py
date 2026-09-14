from app.models.endpoint import Endpoint
from app.scanner.base import BaseScanner
from app.scanner.helpers import bola_severity_for_method, endpoint_label, has_object_identifier
from app.scanner.models import ScanContext, ScannerFinding


class AuthorizationScanner(BaseScanner):
    name = "authorization"

    def scan(self, context: ScanContext) -> list[ScannerFinding]:
        findings: list[ScannerFinding] = []

        for endpoint in context.endpoints:
            if not has_object_identifier(endpoint):
                continue

            label = endpoint_label(endpoint)
            findings.append(
                ScannerFinding(
                    title="Potential BOLA / IDOR Risk",
                    description=(
                        "This endpoint accepts a client-controlled object identifier. "
                        "This is a potential authorization risk requiring authorization "
                        "testing and cannot be confirmed from the OpenAPI document alone."
                    ),
                    severity=bola_severity_for_method(endpoint.method),
                    category="Authorization",
                    owasp_category="API1:2023 Broken Object Level Authorization",
                    evidence=(
                        f"The endpoint accepts a client-controlled object identifier: {label}"
                    ),
                    remediation=(
                        "Ensure object-level authorization verifies that the authenticated "
                        "user can only access resources they are authorized to access."
                    ),
                    confidence="MEDIUM",
                    endpoint_id=endpoint.id,
                    endpoint_label=label,
                )
            )

        return findings
