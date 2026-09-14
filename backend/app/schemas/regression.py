from pydantic import BaseModel, Field


class RegressionFindingItem(BaseModel):
    id: int
    title: str
    category: str
    severity: str
    risk_score: int
    risk_level: str
    endpoint: str | None = None
    method: str | None = None
    path: str | None = None
    fingerprint: str


class RegressionScanInfo(BaseModel):
    id: int
    name: str
    status: str
    overall_risk_score: int
    overall_risk_level: str
    finding_count: int


class RegressionResponse(BaseModel):
    baseline_scan: RegressionScanInfo
    current_scan: RegressionScanInfo
    baseline_risk_score: int
    current_risk_score: int
    risk_score_change: int = Field(
        description="current_score - baseline_score; negative means improved"
    )
    baseline_risk_level: str
    current_risk_level: str
    new_findings: list[RegressionFindingItem]
    resolved_findings: list[RegressionFindingItem]
    persistent_findings: list[RegressionFindingItem]
    new_critical_count: int
    resolved_critical_count: int
    posture: str
    summary: str
