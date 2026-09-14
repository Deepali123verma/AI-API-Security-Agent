from app.scanner.base import BaseScanner
from app.scanner.helpers import (
    endpoint_label,
    has_documented_rate_limiting,
    is_rate_limit_sensitive_endpoint,
)
from app.scanner.models import ScanContext, ScannerFinding


class RateLimitScanner(BaseScanner):
    name = "rate_limit"

    def scan(self, context: ScanContext) -> list[ScannerFinding]:
        findings: list[ScannerFinding] = []

        for endpoint in context.endpoints:
            if not is_rate_limit_sensitive_endpoint(endpoint):
                continue
            if has_documented_rate_limiting(endpoint):
                continue

            label = endpoint_label(endpoint)
            findings.append(
                ScannerFinding(
                    title="Potential Missing Rate Limiting",
                    description=(
                        "This sensitive operation commonly requires rate limiting, but no "
                        "rate limiting is documented in the OpenAPI specification."
                    ),
                    severity="MEDIUM",
                    category="Rate Limiting",
                    owasp_category="API4:2023 Unrestricted Resource Consumption",
                    evidence=(
                        f"Rate limiting is not documented or cannot be verified from the "
                        f"OpenAPI specification for {label}."
                    ),
                    remediation=(
                        "Document and implement rate limiting for authentication and account "
                        "abuse-sensitive operations such as login and registration."
                    ),
                    confidence="LOW",
                    endpoint_id=endpoint.id,
                    endpoint_label=label,
                )
            )

        return findings
