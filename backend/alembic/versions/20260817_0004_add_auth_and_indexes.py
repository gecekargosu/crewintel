"""Add auth fields (password_hash, audit user identity) and crew identifier indexes."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision = "20260817_0004"
down_revision = "20260809_0003"
branch_labels = None
depends_on = None


def _column_names(table_name: str) -> set[str]:
    return {column["name"] for column in inspect(op.get_bind()).get_columns(table_name)}


def upgrade() -> None:
    bind = op.get_bind()

    # users.password_hash — nullable so existing rows (without passwords) migrate cleanly.
    if "password_hash" not in _column_names("users"):
        op.add_column("users", sa.Column("password_hash", sa.String(length=255), nullable=True))

    # audit_logs.user_email — identity of the actor for audit trails.
    if "user_email" not in _column_names("audit_logs"):
        op.add_column("audit_logs", sa.Column("user_email", sa.String(length=255), nullable=True))
    existing_audit_indexes = {index["name"] for index in inspect(bind).get_indexes("audit_logs")}
    if "ix_audit_logs_user_email" not in existing_audit_indexes:
        op.create_index("ix_audit_logs_user_email", "audit_logs", ["user_email"])

    # Crew identifier indexes: speed up document matching and crew filtering.
    existing_crew_indexes = {index["name"] for index in inspect(bind).get_indexes("crew_members")}
    crew_indexes = [
        ("ix_crew_members_passport_number", "passport_number"),
        ("ix_crew_members_seaman_book_number", "seaman_book_number"),
        ("ix_crew_members_email", "email"),
    ]
    for index_name, column_name in crew_indexes:
        if index_name not in existing_crew_indexes and column_name in _column_names("crew_members"):
            op.create_index(index_name, "crew_members", [column_name])


def downgrade() -> None:
    pass
