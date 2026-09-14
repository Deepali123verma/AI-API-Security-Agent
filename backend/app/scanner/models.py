from dataclasses import dataclass, field
from typing import Any

from app.models.endpoint import Endpoint
from app.models.scan import Scan


@dataclass
class ScanContext:
    scan: Scan
    endpoints: list[Endpoint]
    spec_metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ScannerFinding:
    title: str
    description: str
    severity: str
    category: str
    evidence: str
    remediation: str
    confidence: str
    owasp_category: str | None = None
    endpoint_id: int | None = None
    endpoint_label: str | None = None
