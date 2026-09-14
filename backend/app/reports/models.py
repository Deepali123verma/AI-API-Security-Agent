from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class ReportFindingAI:
    summary: str | None = None
    why_it_matters: str | None = None
    technical_reasoning: str | None = None
    validation_guidance: str | None = None
    remediation: str | None = None
    priority: str | None = None
    limitations: str | None = None
    model: str | None = None
    analyzed_at: datetime | None = None


@dataclass
class ReportFinding:
    id: int
    title: str
    category: str
    severity: str
    risk_score: int
    risk_level: str
    confidence: str
    evidence: str
    remediation: str
    risk_factors: dict[str, Any] | None
    endpoint_label: str | None
    method: str | None
    path: str | None
    owasp_category: str | None = None
    ai: ReportFindingAI | None = None


@dataclass
class ScanReportData:
    scan_id: int
    scan_name: str
    status: str
    generated_at: datetime
    created_at: datetime | None
    completed_at: datetime | None
    source_filename: str
    overall_risk_score: int
    overall_risk_level: str
    endpoint_count: int
    finding_count: int
    critical: int
    high: int
    medium: int
    low: int
    info: int
    ai_analysis_count: int
    findings: list[ReportFinding] = field(default_factory=list)


@dataclass
class ComparisonReportData:
    baseline_scan_id: int
    baseline_scan_name: str
    baseline_risk_score: int
    baseline_risk_level: str
    current_scan_id: int
    current_scan_name: str
    current_risk_score: int
    current_risk_level: str
    risk_score_change: int
    posture: str
    new_count: int
    resolved_count: int
    persistent_count: int
    new_critical_count: int
    resolved_critical_count: int
    new_titles: list[str] = field(default_factory=list)
    resolved_titles: list[str] = field(default_factory=list)
    persistent_titles: list[str] = field(default_factory=list)
    generated_at: datetime | None = None
