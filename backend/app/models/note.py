"""Kişisel notlar (personele veya genel operasyona bağlanabilir)."""

from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


def _utcnow_naive() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


class Note(Base):
    """Kullanıcıya ait not.

    `user_id` sahiplik alanıdır: bir kullanıcı başkasının notunu listeleyemez
    veya değiştiremez.
    """

    __tablename__ = "notes"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(200))
    body: Mapped[str] = mapped_column(Text, default="")
    priority: Mapped[str] = mapped_column(String(20), default="normal")
    done: Mapped[bool] = mapped_column(Boolean, default=False)
    crew_member_id: Mapped[int | None] = mapped_column(
        ForeignKey("crew_members.id", ondelete="SET NULL"), nullable=True, index=True
    )
    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True
    )
    user_email: Mapped[str] = mapped_column(String(255), default="")
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=_utcnow_naive, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=_utcnow_naive, server_default=func.now(), onupdate=_utcnow_naive
    )
