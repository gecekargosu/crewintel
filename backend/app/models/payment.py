"""Maaş / ödeme kayıtları (personel başına bütçe takibi)."""

from datetime import UTC, date, datetime
from decimal import Decimal

from sqlalchemy import Date, DateTime, ForeignKey, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


def _utcnow_naive() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


class Payment(Base):
    """Personele yapılan/yapılacak ödeme.

    Tutar `Numeric(12, 2)` olarak tutulur — float yuvarlama hataları
    muhasebe kaydında kabul edilemez.
    """

    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    crew_member_id: Mapped[int] = mapped_column(
        ForeignKey("crew_members.id", ondelete="CASCADE"), index=True
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    currency: Mapped[str] = mapped_column(String(10), default="USD")
    payment_type: Mapped[str] = mapped_column(String(30), default="salary")
    description: Mapped[str] = mapped_column(Text, default="")
    payment_date: Mapped[date] = mapped_column(Date, index=True)
    created_by_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=_utcnow_naive, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=_utcnow_naive, server_default=func.now(), onupdate=_utcnow_naive
    )
