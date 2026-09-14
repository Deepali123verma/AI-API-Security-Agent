from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class SpecMetadataSummary(BaseModel):
    title: str | None = None
    version: str | None = None
    openapi_version: str | None = None
    description: str | None = None


class ScanSummary(BaseModel):
    endpoint_count: int
    finding_count: int
    critical: int = 0
    high: int = 0
    medium: int = 0
    low: int = 0
    info: int = 0
    overall_risk_score: int = 0
    risk_level: str = "INFO"
    ai_analysis_count: int = 0


class ScanHistoryItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    status: str
    created_at: datetime
    updated_at: datetime | None = None
    completed_at: datetime | None = None
    spec_metadata: SpecMetadataSummary
    endpoint_count: int = 0
    finding_count: int = 0
    risk_level: str | None = None
    overall_risk_score: int | None = None


class ScanHistoryResponse(BaseModel):
    items: list[ScanHistoryItem]
    page: int
    page_size: int
    total: int
    total_pages: int


class ScanCreateResponse(BaseModel):
    scan_id: int
    name: str
    status: str


class ScanDetailResponse(BaseModel):
    id: int
    scan_id: int | None = None
    name: str
    source_filename: str
    status: str
    created_at: datetime
    updated_at: datetime | None = None
    completed_at: datetime | None = None
    specification_version: str | None = None
    title: str | None = None
    description: str | None = None
    version: str | None = None
    endpoint_count: int = 0
    spec_metadata: SpecMetadataSummary | dict[str, Any] | None = None
    summary: ScanSummary


# Backward-compatible aliases used by older imports/tests.
class ScanListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    scan_id: int = Field(validation_alias="id")
    name: str
    status: str
    title: str | None
    endpoint_count: int = 0
    created_at: datetime


class ScanDetail(ScanDetailResponse):
    pass
