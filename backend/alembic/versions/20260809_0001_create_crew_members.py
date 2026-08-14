"""Create the initial crew members table without replacing an existing table."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision = "20260809_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    if inspect(bind).has_table("crew_members"):
        return

    op.create_table(
        "crew_members",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("first_name", sa.String(length=100), nullable=False),
        sa.Column("last_name", sa.String(length=100), nullable=False),
        sa.Column("position", sa.String(length=100), nullable=False),
        sa.Column("nationality", sa.String(length=100), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_crew_members_id", "crew_members", ["id"])


def downgrade() -> None:
    # Intentionally non-destructive: this initial migration must not delete crew data.
    pass
