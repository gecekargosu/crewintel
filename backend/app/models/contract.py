from datetime import UTC, date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class Contract(Base):
    __tablename__ = "contracts"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    crew_member_id: Mapped[int] = mapped_column(ForeignKey("crew_members.id"), index=True)
    ship_id: Mapped[int] = mapped_column(ForeignKey("ships.id"), index=True)
    contract_number: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    contract_type: Mapped[str] = mapped_column(String(100))
    start_date: Mapped[date] = mapped_column(Date)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="active", server_default="active", index=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC).replace(tzinfo=None), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC).replace(tzinfo=None), server_default=func.now(), onupdate=lambda: datetime.now(UTC).replace(tzinfo=None))

    ship: Mapped["Ship"] = relationship(back_populates="contracts")
    crew_member: Mapped["CrewMember"] = relationship(back_populates="contracts")
