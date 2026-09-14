from sqlalchemy import Boolean, ForeignKey, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Endpoint(Base):
    __tablename__ = "endpoints"

    id: Mapped[int] = mapped_column(primary_key=True)
    scan_id: Mapped[int] = mapped_column(ForeignKey("scans.id", ondelete="CASCADE"), index=True)
    path: Mapped[str] = mapped_column(String(512))
    method: Mapped[str] = mapped_column(String(10))
    summary: Mapped[str | None] = mapped_column(String(512))
    description: Mapped[str | None] = mapped_column(Text)
    operation_id: Mapped[str | None] = mapped_column(String(255))
    tags: Mapped[list | None] = mapped_column(JSON)
    parameters: Mapped[list | None] = mapped_column(JSON)
    request_body: Mapped[dict | None] = mapped_column(JSON)
    responses: Mapped[dict | None] = mapped_column(JSON)
    security_defined: Mapped[bool] = mapped_column(Boolean, default=False)
    security_requirements: Mapped[list | None] = mapped_column(JSON)

    scan = relationship("Scan", back_populates="endpoints")
    findings = relationship("Finding", back_populates="endpoint")
