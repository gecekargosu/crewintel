from datetime import UTC, date, datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class JobPosting(Base):
    """Manning yöneticisinin açtığı iş ilanı (örn. 'MV Kılıç 3 — Elektrikçi').

    Durumlar: draft (taslak), open (yayında), closed (kapalı/arşiv), expired (süresi doldu).
    """

    __tablename__ = "job_postings"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(150))
    position: Mapped[str] = mapped_column(String(150), index=True)
    ship_id: Mapped[int | None] = mapped_column(ForeignKey("ships.id"), nullable=True, index=True)
    # ── Yayın için detay alanları (Phase 8) ─────────────────────────────────
    vessel_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    flag: Mapped[str | None] = mapped_column(String(100), nullable=True)
    location: Mapped[str | None] = mapped_column(String(150), nullable=True)
    currency: Mapped[str | None] = mapped_column(String(10), default="USD", server_default="USD")
    salary: Mapped[str | None] = mapped_column(String(100), nullable=True)
    salary_period: Mapped[str | None] = mapped_column(String(30), default="monthly", server_default="monthly")
    contract_duration: Mapped[str | None] = mapped_column(String(50), nullable=True)
    join_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    application_deadline: Mapped[date | None] = mapped_column(Date, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    duties: Mapped[str | None] = mapped_column(Text, nullable=True)
    requirements: Mapped[str | None] = mapped_column(Text, nullable=True)
    certificates_required: Mapped[str | None] = mapped_column(Text, nullable=True)
    experience_required: Mapped[str | None] = mapped_column(String(100), nullable=True)
    languages_required: Mapped[str | None] = mapped_column(String(150), nullable=True)
    age_min: Mapped[int | None] = mapped_column(Integer, nullable=True)
    age_max: Mapped[int | None] = mapped_column(Integer, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    contact_info: Mapped[str | None] = mapped_column(String(200), nullable=True)
    # ────────────────────────────────────────────────────────────────────────
    status: Mapped[str] = mapped_column(String(20), default="open", server_default="open", index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(UTC).replace(tzinfo=None), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(UTC).replace(tzinfo=None),
        server_default=func.now(),
        onupdate=lambda: datetime.now(UTC).replace(tzinfo=None),
    )

    ship: Mapped["Ship"] = relationship()  # noqa: F821
    applications: Mapped[list["JobApplication"]] = relationship(
        back_populates="posting", cascade="all, delete-orphan"
    )
    publications: Mapped[list["JobPublication"]] = relationship(
        back_populates="posting", cascade="all, delete-orphan"
    )


class JobApplication(Base):
    """Bir personele ait iş ilanı başvurusu (başvuru havuzu)."""

    __tablename__ = "job_applications"
    __table_args__ = (
        UniqueConstraint("job_posting_id", "crew_member_id", name="uq_job_posting_crew"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    job_posting_id: Mapped[int] = mapped_column(
        ForeignKey("job_postings.id", ondelete="CASCADE"), index=True
    )
    crew_member_id: Mapped[int] = mapped_column(ForeignKey("crew_members.id"), index=True)
    status: Mapped[str] = mapped_column(
        String(20), default="applied", server_default="applied", index=True
    )
    # ── M1 Mobile: başvuru skoru + kaynak ──────────────────────────────────
    match_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    applied_from: Mapped[str] = mapped_column(
        String(20), default="portal", server_default="portal"
    )  # portal | mobile | admin
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(UTC).replace(tzinfo=None), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(UTC).replace(tzinfo=None),
        server_default=func.now(),
        onupdate=lambda: datetime.now(UTC).replace(tzinfo=None),
    )

    posting: Mapped["JobPosting"] = relationship(back_populates="applications")  # noqa: F821
    crew_member: Mapped["CrewMember"] = relationship()  # noqa: F821


class JobTemplate(Base):
    """İlan görseli/metni için şablon. {{position}}, {{vessel}} gibi değişkenler içerir."""

    __tablename__ = "job_templates"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(150))
    body: Mapped[str] = mapped_column(Text)  # {{...}} değişkenleriyle
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(UTC).replace(tzinfo=None), server_default=func.now()
    )


class JobPublication(Base):
    """Bir ilanın kanal bazlı yayın geçmişi (crew_portal / whatsapp / instagram / facebook)."""

    __tablename__ = "job_publications"
    __table_args__ = (
        UniqueConstraint("job_posting_id", "channel", name="uq_job_posting_channel"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    job_posting_id: Mapped[int] = mapped_column(
        ForeignKey("job_postings.id", ondelete="CASCADE"), index=True
    )
    channel: Mapped[str] = mapped_column(String(30), index=True)  # crew_portal/whatsapp/instagram/facebook
    status: Mapped[str] = mapped_column(
        String(20), default="queued", server_default="queued", index=True
    )  # queued/sent/failed/skipped
    recipient_count: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    message_id: Mapped[str | None] = mapped_column(String(200), nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(UTC).replace(tzinfo=None), server_default=func.now()
    )

    posting: Mapped["JobPosting"] = relationship(back_populates="publications")  # noqa: F821


class WhatsAppMessage(Base):
    """WhatsApp gönderim kuyruğu — her alıcı için bir satır.

    status: pending (sırada) / sent (gönderildi) / failed (hata, tekrar denenebilir)
    """

    __tablename__ = "whatsapp_messages"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    job_posting_id: Mapped[int | None] = mapped_column(
        ForeignKey("job_postings.id", ondelete="SET NULL"), nullable=True, index=True
    )
    crew_member_id: Mapped[int | None] = mapped_column(
        ForeignKey("crew_members.id", ondelete="SET NULL"), nullable=True, index=True
    )
    phone: Mapped[str] = mapped_column(String(30), index=True)
    text: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), default="pending", server_default="pending", index=True)
    attempts: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    provider_message_id: Mapped[str | None] = mapped_column(String(200), nullable=True)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(UTC).replace(tzinfo=None), server_default=func.now()
    )

    posting: Mapped["JobPosting"] = relationship()  # noqa: F821
    crew_member: Mapped["CrewMember"] = relationship()  # noqa: F821


class JobImage(Base):
    """Üretilen ilan görseli (şablon + ilan bilgisiyle oluşturulur, ayrı dosya)."""

    __tablename__ = "job_images"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    job_posting_id: Mapped[int] = mapped_column(
        ForeignKey("job_postings.id", ondelete="CASCADE"), index=True
    )
    storage_path: Mapped[str] = mapped_column(String(300))
    original_filename: Mapped[str | None] = mapped_column(String(200), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(UTC).replace(tzinfo=None), server_default=func.now()
    )
