from typing import Any

from app.scanner.base import BaseScanner
from app.scanner.models import ScanContext, ScannerFinding


class ConfigurationScanner(BaseScanner):
    name = "configuration"

    def scan(self, context: ScanContext) -> list[ScannerFinding]:
        findings: list[ScannerFinding] = []
        metadata = context.spec_metadata or {}
        security_schemes: dict[str, Any] = metadata.get("security_schemes") or {}

        findings.extend(self._check_insecure_server_urls(metadata))
        findings.extend(self._check_security_schemes(security_schemes))
        findings.extend(self._check_missing_global_security(context, metadata))

        return findings

    def _check_insecure_server_urls(self, metadata: dict[str, Any]) -> list[ScannerFinding]:
        findings: list[ScannerFinding] = []
        servers = metadata.get("servers") or []

        for server in servers:
            if not isinstance(server, dict):
                continue
            url = str(server.get("url", ""))
            if url.startswith("http://"):
                findings.append(
                    ScannerFinding(
                        title="Potential Insecure Server Configuration",
                        description=(
                            "The OpenAPI specification documents a non-TLS server URL."
                        ),
                        severity="MEDIUM",
                        category="Configuration",
                        owasp_category="API8:2023 Security Misconfiguration",
                        evidence=f"Server URL uses HTTP instead of HTTPS: {url}",
                        remediation=(
                            "Use HTTPS for production API server URLs documented in the "
                            "OpenAPI specification."
                        ),
                        confidence="HIGH",
                    )
                )

        schemes = metadata.get("schemes") or []
        if isinstance(schemes, list) and "http" in schemes and "https" not in schemes:
            findings.append(
                ScannerFinding(
                    title="Potential Insecure Server Configuration",
                    description=(
                        "The OpenAPI specification documents HTTP without HTTPS support."
                    ),
                    severity="MEDIUM",
                    category="Configuration",
                    owasp_category="API8:2023 Security Misconfiguration",
                    evidence="Swagger schemes include 'http' but not 'https'.",
                    remediation=(
                        "Prefer HTTPS and document secure transport in the OpenAPI specification."
                    ),
                    confidence="HIGH",
                )
            )

        return findings

    def _check_security_schemes(
        self,
        security_schemes: dict[str, Any],
    ) -> list[ScannerFinding]:
        findings: list[ScannerFinding] = []

        for scheme_name, scheme in security_schemes.items():
            if not isinstance(scheme, dict):
                continue

            scheme_type = scheme.get("type")
            scheme_in = scheme.get("in")

            if scheme_type == "apiKey" and scheme_in == "query":
                findings.append(
                    ScannerFinding(
                        title="Potential Security Misconfiguration",
                        description=(
                            "An API key security scheme is configured to be sent in the query "
                            "string, which may expose credentials in logs and URLs."
                        ),
                        severity="MEDIUM",
                        category="Configuration",
                        owasp_category="API8:2023 Security Misconfiguration",
                        evidence=(
                            f"Security scheme '{scheme_name}' uses apiKey in query parameters."
                        ),
                        remediation=(
                            "Prefer Authorization headers or secure cookies instead of query "
                            "string API keys."
                        ),
                        confidence="HIGH",
                    )
                )

            if scheme_type == "http" and scheme.get("scheme") == "basic":
                findings.append(
                    ScannerFinding(
                        title="Potential Security Misconfiguration",
                        description=(
                            "HTTP Basic authentication is documented. Basic credentials require "
                            "careful transport and storage protections."
                        ),
                        severity="LOW",
                        category="Configuration",
                        owasp_category="API8:2023 Security Misconfiguration",
                        evidence=f"Security scheme '{scheme_name}' uses HTTP Basic authentication.",
                        remediation=(
                            "Ensure Basic authentication is only used over HTTPS and consider "
                            "stronger authentication mechanisms."
                        ),
                        confidence="MEDIUM",
                    )
                )

        return findings

    def _check_missing_global_security(
        self,
        context: ScanContext,
        metadata: dict[str, Any],
    ) -> list[ScannerFinding]:
        if not context.endpoints:
            return []

        security_schemes = metadata.get("security_schemes") or {}
        global_security = metadata.get("global_security")
        secured_endpoints = sum(1 for endpoint in context.endpoints if endpoint.security_defined)

        if security_schemes and global_security is None and secured_endpoints == 0:
            return [
                ScannerFinding(
                    title="Potential Security Misconfiguration",
                    description=(
                        "Security schemes are defined but no global or operation-level security "
                        "requirements are documented for discovered endpoints."
                    ),
                    severity="MEDIUM",
                    category="Configuration",
                    owasp_category="API8:2023 Security Misconfiguration",
                    evidence=(
                        "Security schemes exist in the specification, but no endpoint declares "
                        "a security requirement."
                    ),
                    remediation=(
                        "Apply appropriate global or operation-level security requirements "
                        "in the OpenAPI specification."
                    ),
                    confidence="MEDIUM",
                )
            ]

        return []
