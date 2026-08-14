from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class DocumentMatch(Base):
    """Kalıcı match kararı kaydı.

    Her otomatik/manuel eşleştirme kararı burada saklanır: hangi adaylara hangi
    sinyallerle kaç puan verildiği ve hangi kararın alındığı. Manual override'lar
    MATCH_OVERRIDE decision'ı ile loglanır.
    """

    __tablename__ = "document_matches"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    document_id: Mapped[int] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"),
        index=True,
    )
    candidate_crew_id: Mapped[int | None] = mapped_column(
        ForeignKey("crew_members.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    final_crew_id: Mapped[int | None] = mapped_column(
        ForeignKey("crew_members.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    score: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    decision: Mapped[str] = mapped_column(String(30), index=True)
    signals: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    candidates: Mapped[list | None] = mapped_column(JSON, nullable=True)
    actor_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(UTC).replace(tzinfo=None),
        server_default=func.now(),
        index=True,
    )
