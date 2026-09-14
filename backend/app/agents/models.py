from typing import Any, Literal

from pydantic import BaseModel, Field


class AIAnalysisResult(BaseModel):
    summary: str = Field(description="Plain-language summary of the deterministic finding")
    why_it_matters: str = Field(description="Security impact explanation")
    technical_reasoning: str = Field(description="Evidence-based technical reasoning")
    validation_guidance: str = Field(
        description="What a security engineer should verify in the real API"
    )
    remediation: str = Field(description="Practical remediation guidance")
    priority: Literal["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"] = Field(
        description="Explanatory priority; does not override deterministic risk_score"
    )
    limitations: str = Field(
        description="Limitations of static/OpenAPI analysis for this finding"
    )


class FindingAIContext(BaseModel):
    finding: dict[str, Any]
    endpoint: dict[str, Any] | None = None
    scan_metadata: dict[str, Any] | None = None
