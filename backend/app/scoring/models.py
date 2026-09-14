from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ScoreResult:
    risk_score: int
    risk_level: str
    risk_factors: dict[str, Any]


@dataclass(frozen=True)
class ScanRiskSummary:
    total_findings: int
    critical: int
    high: int
    medium: int
    low: int
    info: int
    overall_risk_score: int
    risk_level: str
