"""add notes table

Revision ID: 3b90f6112c93
Revises: 20260818_0010
Create Date: 2026-08-30
"""
from alembic import op
import sqlalchemy as sa

revision = "3b90f6112c93"
down_revision = "20260818_0010"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "notes",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("body", sa.Text(), server_default=""),
        sa.Column("priority", sa.String(20), server_default="normal"),
        sa.Column("done", sa.Boolean(), server_default="false"),
        sa.Column("crew_member_id", sa.Integer(), sa.ForeignKey("crew_members.id"), nullable=True),
        sa.Column("user_email", sa.String(255), server_default=""),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index("ix_notes_id", "notes", ["id"])


def downgrade() -> None:
    op.drop_index("ix_notes_id", table_name="notes")
    op.drop_table("notes")
