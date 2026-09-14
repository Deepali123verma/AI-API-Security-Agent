from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class AIAnalysis(BaseModel):
    summary: str
    why_it_matters: str
    technical_reasoning: str
    validation_guidance: str
    remediation: str
    priority: Literal["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"]
    limitations: str


class AIAnalysisResponse(BaseModel):
    finding_id: int
    ai_analysis: AIAnalysis
    model: str
    cached: bool = False
    analyzed_at: datetime | None = None


class BulkAIAnalysisResponse(BaseModel):
    scan_id: int
    analyzed_count: int
    skipped_existing_count: int
    failed_count: int
    results: list[AIAnalysisResponse]
    errors: list[str] = Field(default_factory=list)
