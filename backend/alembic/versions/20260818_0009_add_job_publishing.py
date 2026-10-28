"""0009 — İş İlanları & Yayın: job_templates, job_publications, whatsapp_messages,
job_images; job_postings detay alanları; crew_members.job_seeking."""

import sqlalchemy as sa
from alembic import op

revision = "20260818_0009"
down_revision = "20260818_0008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── job_postings yeni yayın alanları ─────────────────────────────────────
    op.add_column("job_postings", sa.Column("vessel_type", sa.String(length=100), nullable=True))
    op.add_column("job_postings", sa.Column("flag", sa.String(length=100), nullable=True))
    op.add_column("job_postings", sa.Column("location", sa.String(length=150), nullable=True))
    op.add_column("job_postings", sa.Column("currency", sa.String(length=10), nullable=True, server_default="USD"))
    op.add_column("job_postings", sa.Column("salary_period", sa.String(length=30), nullable=True, server_default="monthly"))
    op.add_column("job_postings", sa.Column("contract_duration", sa.String(length=50), nullable=True))
    op.add_column("job_postings", sa.Column("join_date", sa.Date(), nullable=True))
    op.add_column("job_postings", sa.Column("application_deadline", sa.Date(), nullable=True))
    op.add_column("job_postings", sa.Column("duties", sa.Text(), nullable=True))
    op.add_column("job_postings", sa.Column("certificates_required", sa.Text(), nullable=True))
    op.add_column("job_postings", sa.Column("experience_required", sa.String(length=100), nullable=True))
    op.add_column("job_postings", sa.Column("languages_required", sa.String(length=150), nullable=True))
    op.add_column("job_postings", sa.Column("age_min", sa.Integer(), nullable=True))
    op.add_column("job_postings", sa.Column("age_max", sa.Integer(), nullable=True))
    op.add_column("job_postings", sa.Column("notes", sa.Text(), nullable=True))
    op.add_column("job_postings", sa.Column("contact_info", sa.String(length=200), nullable=True))

    # ── crew_members.job_seeking (portal 'İş Arıyorum' anahtarı) ─────────────
    op.add_column(
        "crew_members",
        sa.Column("job_seeking", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )

    # ── job_templates ────────────────────────────────────────────────────────
    op.create_table(
        "job_templates",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("is_default", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_job_templates_id", "job_templates", ["id"])

    # ── job_publications ─────────────────────────────────────────────────────
    op.create_table(
        "job_publications",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "job_posting_id",
            sa.Integer(),
            sa.ForeignKey("job_postings.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("channel", sa.String(length=30), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="queued"),
        sa.Column("recipient_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("message_id", sa.String(length=200), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("sent_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("job_posting_id", "channel", name="uq_job_posting_channel"),
    )
    op.create_index("ix_job_publications_id", "job_publications", ["id"])
    op.create_index("ix_job_publications_job_posting_id", "job_publications", ["job_posting_id"])
    op.create_index("ix_job_publications_channel", "job_publications", ["channel"])
    op.create_index("ix_job_publications_status", "job_publications", ["status"])

    # ── whatsapp_messages (kuyruk) ───────────────────────────────────────────
    op.create_table(
        "whatsapp_messages",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "job_posting_id",
            sa.Integer(),
            sa.ForeignKey("job_postings.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "crew_member_id",
            sa.Integer(),
            sa.ForeignKey("crew_members.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("phone", sa.String(length=30), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="pending"),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("provider_message_id", sa.String(length=200), nullable=True),
        sa.Column("sent_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_whatsapp_messages_id", "whatsapp_messages", ["id"])
    op.create_index("ix_whatsapp_messages_job_posting_id", "whatsapp_messages", ["job_posting_id"])
    op.create_index("ix_whatsapp_messages_crew_member_id", "whatsapp_messages", ["crew_member_id"])
    op.create_index("ix_whatsapp_messages_phone", "whatsapp_messages", ["phone"])
    op.create_index("ix_whatsapp_messages_status", "whatsapp_messages", ["status"])

    # ── job_images ───────────────────────────────────────────────────────────
    op.create_table(
        "job_images",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "job_posting_id",
            sa.Integer(),
            sa.ForeignKey("job_postings.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("storage_path", sa.String(length=300), nullable=False),
        sa.Column("original_filename", sa.String(length=200), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_job_images_id", "job_images", ["id"])
    op.create_index("ix_job_images_job_posting_id", "job_images", ["job_posting_id"])


def downgrade() -> None:
    op.drop_table("job_images")
    op.drop_table("whatsapp_messages")
    op.drop_table("job_publications")
    op.drop_table("job_templates")
    op.drop_column("crew_members", "job_seeking")
    for col in [
        "vessel_type", "flag", "location", "currency", "salary_period",
        "contract_duration", "join_date", "application_deadline", "duties",
        "certificates_required", "experience_required", "languages_required",
        "age_min", "age_max", "notes", "contact_info",
    ]:
        op.drop_column("job_postings", col)
