from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


RiskLevel = Literal["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"]
ConfidenceLevel = Literal["HIGH", "MEDIUM", "LOW"]


class FindingAIAnalysisSummary(BaseModel):
    summary: str | None = None
    why_it_matters: str | None = None
    technical_reasoning: str | None = None
    validation_guidance: str | None = None
    remediation: str | None = None
    priority: str | None = None
    limitations: str | None = None
    model: str | None = None
    analyzed_at: datetime | None = None


class FindingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    severity: str
    category: str
    owasp_category: str | None
    endpoint: str | None = None
    evidence: str
    structured_evidence: dict[str, Any] | None = None
    confidence: str
    remediation: str
    risk_score: int
    risk_level: RiskLevel
    risk_factors: dict[str, Any] | None = None
    ai_analysis: FindingAIAnalysisSummary | None = None


class FindingDetailResponse(FindingResponse):
    description: str
    created_at: datetime


class SecurityScanResponse(BaseModel):
    scan_id: int
    total_findings: int
    findings_count: int = Field(description="Backward-compatible alias for total_findings")
    critical: int
    high: int
    medium: int
    low: int
    info: int
    overall_risk_score: int
    risk_level: RiskLevel
    findings: list[FindingResponse]


class FindingSummary(BaseModel):
    title: str
    severity: str
    category: str
    risk_score: int
    risk_level: RiskLevel


class FindingHistoryResponse(BaseModel):
    items: list[FindingResponse]
    page: int
    page_size: int
    total: int
    total_pages: int
