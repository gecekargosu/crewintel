from datetime import UTC, date, datetime

from sqlalchemy import Boolean, Date, DateTime, Integer, JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class CrewMember(Base):
    __tablename__ = "crew_members"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    first_name: Mapped[str] = mapped_column(String(100), index=True)
    last_name: Mapped[str] = mapped_column(String(100), index=True)
    date_of_birth: Mapped[date | None] = mapped_column(Date, nullable=True)
    nationality: Mapped[str | None] = mapped_column(String(100), nullable=True)
    passport_number: Mapped[str | None] = mapped_column(String(100), nullable=True)
    seaman_book_number: Mapped[str | None] = mapped_column(String(100), nullable=True)
    position: Mapped[str] = mapped_column(String(100), index=True)
    rank: Mapped[str | None] = mapped_column(String(100), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    emergency_contact_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    emergency_contact_phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    birth_place: Mapped[str | None] = mapped_column(String(150), nullable=True)
    hometown: Mapped[str | None] = mapped_column(String(150), nullable=True)
    marital_status: Mapped[str | None] = mapped_column(String(50), nullable=True)
    experience_years: Mapped[int | None] = mapped_column(Integer, nullable=True)
    sea_service_months: Mapped[int | None] = mapped_column(Integer, nullable=True)
    languages: Mapped[str | None] = mapped_column(Text, nullable=True)
    education_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    profile_data: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="active", server_default="active", index=True)
    job_seeking: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    availability: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
        server_default="available",
        comment="available | on_board | on_leave | not_available",
    )
    # ── M1 Mobile: iş tercihleri / müsaitlik (migration 0010) ──────────────
    available_from: Mapped[date | None] = mapped_column(Date, nullable=True)
    job_preferences: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    vessel_types_experience: Mapped[str | None] = mapped_column(String(200), nullable=True)
    expected_salary_min: Mapped[int | None] = mapped_column(Integer, nullable=True)
    expected_salary_max: Mapped[int | None] = mapped_column(Integer, nullable=True)
    expected_salary_currency: Mapped[str | None] = mapped_column(String(10), nullable=True)
    expected_salary_period: Mapped[str | None] = mapped_column(String(30), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(UTC).replace(tzinfo=None),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(UTC).replace(tzinfo=None),
        server_default=func.now(),
        onupdate=lambda: datetime.now(UTC).replace(tzinfo=None),
    )

    assignments: Mapped[list["ShipCrewAssignment"]] = relationship(
        back_populates="crew_member",
    )
    contracts: Mapped[list["Contract"]] = relationship(back_populates="crew_member")
    documents: Mapped[list["Document"]] = relationship(back_populates="crew_member")
