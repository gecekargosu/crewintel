"""Add document_matches table for persistent match decision audit."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision = "20260817_0005"
down_revision = "20260817_0004"
branch_labels = None
depends_on = None


def _table_exists(table_name: str) -> bool:
    return table_name in inspect(op.get_bind()).get_table_names()


def upgrade() -> None:
    if _table_exists("document_matches"):
        return
    op.create_table(
        "document_matches",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("document_id", sa.Integer(), nullable=False),
        sa.Column("candidate_crew_id", sa.Integer(), nullable=True),
        sa.Column("final_crew_id", sa.Integer(), nullable=True),
        sa.Column("score", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("decision", sa.String(length=30), nullable=False),
        sa.Column("signals", sa.JSON(), nullable=True),
        sa.Column("candidates", sa.JSON(), nullable=True),
        sa.Column("actor_email", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["candidate_crew_id"], ["crew_members.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["final_crew_id"], ["crew_members.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_document_matches_document_id", "document_matches", ["document_id"])
    op.create_index("ix_document_matches_candidate_crew_id", "document_matches", ["candidate_crew_id"])
    op.create_index("ix_document_matches_final_crew_id", "document_matches", ["final_crew_id"])
    op.create_index("ix_document_matches_decision", "document_matches", ["decision"])
    op.create_index("ix_document_matches_created_at", "document_matches", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_document_matches_created_at", table_name="document_matches")
    op.drop_index("ix_document_matches_decision", table_name="document_matches")
    op.drop_index("ix_document_matches_final_crew_id", table_name="document_matches")
    op.drop_index("ix_document_matches_candidate_crew_id", table_name="document_matches")
    op.drop_index("ix_document_matches_document_id", table_name="document_matches")
    op.drop_table("document_matches")
