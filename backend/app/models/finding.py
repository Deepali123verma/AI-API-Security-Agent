from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Finding(Base):
    __tablename__ = "findings"

    id: Mapped[int] = mapped_column(primary_key=True)
    scan_id: Mapped[int] = mapped_column(ForeignKey("scans.id", ondelete="CASCADE"), index=True)
    endpoint_id: Mapped[int | None] = mapped_column(
        ForeignKey("endpoints.id", ondelete="SET NULL"),
        index=True,
    )
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text)
    severity: Mapped[str] = mapped_column(String(20), index=True)
    category: Mapped[str] = mapped_column(String(50), index=True)
    owasp_category: Mapped[str | None] = mapped_column(String(100))
    evidence: Mapped[str] = mapped_column(Text)
    remediation: Mapped[str] = mapped_column(Text)
    confidence: Mapped[str] = mapped_column(String(20))
    structured_evidence: Mapped[dict | None] = mapped_column(JSON)
    risk_score: Mapped[int] = mapped_column(Integer, default=0)
    risk_level: Mapped[str] = mapped_column(String(20), default="INFO", index=True)
    risk_factors: Mapped[dict | None] = mapped_column(JSON)
    ai_summary: Mapped[str | None] = mapped_column(Text)
    ai_why_it_matters: Mapped[str | None] = mapped_column(Text)
    ai_technical_reasoning: Mapped[str | None] = mapped_column(Text)
    ai_validation_guidance: Mapped[str | None] = mapped_column(Text)
    ai_remediation: Mapped[str | None] = mapped_column(Text)
    ai_priority: Mapped[str | None] = mapped_column(String(20))
    ai_limitations: Mapped[str | None] = mapped_column(Text)
    ai_model: Mapped[str | None] = mapped_column(String(100))
    ai_analyzed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    scan = relationship("Scan", back_populates="findings")
    endpoint = relationship("Endpoint", back_populates="findings")
