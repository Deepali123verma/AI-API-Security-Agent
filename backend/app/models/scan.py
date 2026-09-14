from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.core.scan_status import PENDING


class Scan(Base):
    __tablename__ = "scans"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(255))
    source_filename: Mapped[str] = mapped_column(String(255))
    specification_version: Mapped[str | None] = mapped_column(String(20))
    title: Mapped[str | None] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text)
    version: Mapped[str | None] = mapped_column(String(50))
    status: Mapped[str] = mapped_column(String(20), default=PENDING, index=True)
    spec_metadata: Mapped[dict | None] = mapped_column(JSON)
    overall_risk_score: Mapped[int | None] = mapped_column(Integer)
    overall_risk_level: Mapped[str | None] = mapped_column(String(20), index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    user = relationship("User", back_populates="scans")
    endpoints = relationship(
        "Endpoint",
        back_populates="scan",
        cascade="all, delete-orphan",
    )
    findings = relationship(
        "Finding",
        back_populates="scan",
        cascade="all, delete-orphan",
    )
