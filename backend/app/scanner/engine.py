from app.scanner.auth_scanner import AuthenticationScanner
from app.scanner.authorization_scanner import AuthorizationScanner
from app.scanner.base import BaseScanner
from app.scanner.configuration_scanner import ConfigurationScanner
from app.scanner.injection_scanner import InjectionScanner
from app.scanner.models import ScanContext, ScannerFinding
from app.scanner.rate_limit_scanner import RateLimitScanner
from app.scanner.sensitive_data_scanner import SensitiveDataScanner

DEFAULT_SCANNERS: list[BaseScanner] = [
    AuthenticationScanner(),
    AuthorizationScanner(),
    SensitiveDataScanner(),
    RateLimitScanner(),
    ConfigurationScanner(),
    InjectionScanner(),
]


class ScannerEngine:
    def __init__(self, scanners: list[BaseScanner] | None = None) -> None:
        self.scanners = scanners or DEFAULT_SCANNERS

    def run(self, context: ScanContext) -> list[ScannerFinding]:
        findings: list[ScannerFinding] = []
        for scanner in self.scanners:
            findings.extend(scanner.scan(context))
        return findings
