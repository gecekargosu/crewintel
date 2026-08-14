from datetime import UTC, date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Integer, JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    crew_member_id: Mapped[int | None] = mapped_column(ForeignKey("crew_members.id"), nullable=True, index=True)
    original_filename: Mapped[str] = mapped_column(String(500))
    stored_filename: Mapped[str] = mapped_column(String(500), unique=True)
    storage_path: Mapped[str] = mapped_column(String(1000))
    mime_type: Mapped[str | None] = mapped_column(String(150), nullable=True)
    file_size: Mapped[int] = mapped_column(Integer)
    checksum: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    document_type: Mapped[str] = mapped_column(String(100), default="other", server_default="other", index=True)
    document_number: Mapped[str | None] = mapped_column(String(150), nullable=True, index=True)
    issue_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    expiry_date: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)
    match_status: Mapped[str] = mapped_column(String(30), default="pending", server_default="pending", index=True)
    match_confidence: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    extracted_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    extracted_metadata: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    source: Mapped[str] = mapped_column(String(50), default="upload", server_default="upload")
    archived_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC).replace(tzinfo=None), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC).replace(tzinfo=None), server_default=func.now(), onupdate=lambda: datetime.now(UTC).replace(tzinfo=None))

    crew_member: Mapped["CrewMember | None"] = relationship(back_populates="documents")
