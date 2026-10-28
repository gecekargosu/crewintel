"""0008 — job_postings + job_applications (iş ilanı / başvuru havuzu)."""

import sqlalchemy as sa
from alembic import op

revision = "20260818_0008"
down_revision = "20260818_0007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "job_postings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("title", sa.String(length=150), nullable=False),
        sa.Column("position", sa.String(length=150), nullable=False),
        sa.Column("ship_id", sa.Integer(), sa.ForeignKey("ships.id"), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("requirements", sa.Text(), nullable=True),
        sa.Column("salary", sa.String(length=100), nullable=True),
        sa.Column("start_date", sa.Date(), nullable=True),
        sa.Column(
            "status", sa.String(length=20), nullable=False, server_default="open"
        ),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index("ix_job_postings_id", "job_postings", ["id"])
    op.create_index("ix_job_postings_position", "job_postings", ["position"])
    op.create_index("ix_job_postings_ship_id", "job_postings", ["ship_id"])
    op.create_index("ix_job_postings_status", "job_postings", ["status"])

    op.create_table(
        "job_applications",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "job_posting_id",
            sa.Integer(),
            sa.ForeignKey("job_postings.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "crew_member_id",
            sa.Integer(),
            sa.ForeignKey("crew_members.id"),
            nullable=False,
        ),
        sa.Column(
            "status", sa.String(length=20), nullable=False, server_default="applied"
        ),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.UniqueConstraint(
            "job_posting_id", "crew_member_id", name="uq_job_posting_crew"
        ),
    )
    op.create_index("ix_job_applications_id", "job_applications", ["id"])
    op.create_index(
        "ix_job_applications_job_posting_id", "job_applications", ["job_posting_id"]
    )
    op.create_index(
        "ix_job_applications_crew_member_id", "job_applications", ["crew_member_id"]
    )
    op.create_index("ix_job_applications_status", "job_applications", ["status"])


def downgrade() -> None:
    op.drop_table("job_applications")
    op.drop_table("job_postings")
