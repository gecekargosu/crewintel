from datetime import UTC, datetime

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class Ship(Base):
    __tablename__ = "ships"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(200), index=True)
    imo_number: Mapped[str | None] = mapped_column(String(7), unique=True, nullable=True)
    flag: Mapped[str | None] = mapped_column(String(100), nullable=True)
    ship_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    company: Mapped[str | None] = mapped_column(String(200), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="active", server_default="active", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC).replace(tzinfo=None), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC).replace(tzinfo=None), server_default=func.now(), onupdate=lambda: datetime.now(UTC).replace(tzinfo=None))

    assignments: Mapped[list["ShipCrewAssignment"]] = relationship(back_populates="ship")
    contracts: Mapped[list["Contract"]] = relationship(back_populates="ship")
