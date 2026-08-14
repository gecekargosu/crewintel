"""Add document archive, audit trail, and CV profile fields."""

from alembic import op
import sqlalchemy as sa


revision = "20260809_0003"
down_revision = "20260809_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("crew_members") as batch_op:
        batch_op.add_column(sa.Column("birth_place", sa.String(length=150), nullable=True))
        batch_op.add_column(sa.Column("hometown", sa.String(length=150), nullable=True))
        batch_op.add_column(sa.Column("marital_status", sa.String(length=50), nullable=True))
        batch_op.add_column(sa.Column("experience_years", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("sea_service_months", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("languages", sa.Text(), nullable=True))
        batch_op.add_column(sa.Column("education_summary", sa.Text(), nullable=True))
        batch_op.add_column(sa.Column("notes", sa.Text(), nullable=True))
        batch_op.add_column(sa.Column("profile_data", sa.JSON(), nullable=True))

    op.create_table(
        "documents",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("crew_member_id", sa.Integer(), nullable=True),
        sa.Column("original_filename", sa.String(length=500), nullable=False),
        sa.Column("stored_filename", sa.String(length=500), nullable=False),
        sa.Column("storage_path", sa.String(length=1000), nullable=False),
        sa.Column("mime_type", sa.String(length=150), nullable=True),
        sa.Column("file_size", sa.Integer(), nullable=False),
        sa.Column("checksum", sa.String(length=64), nullable=False),
        sa.Column("document_type", sa.String(length=100), nullable=False, server_default="other"),
        sa.Column("document_number", sa.String(length=150), nullable=True),
        sa.Column("issue_date", sa.Date(), nullable=True),
        sa.Column("expiry_date", sa.Date(), nullable=True),
        sa.Column("match_status", sa.String(length=30), nullable=False, server_default="pending"),
        sa.Column("match_confidence", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("extracted_text", sa.Text(), nullable=True),
        sa.Column("extracted_metadata", sa.JSON(), nullable=True),
        sa.Column("source", sa.String(length=50), nullable=False, server_default="upload"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["crew_member_id"], ["crew_members.id"]),
        sa.PrimaryKeyConstraint("id"), sa.UniqueConstraint("stored_filename"), sa.UniqueConstraint("checksum"),
    )
    for name, column in [("ix_documents_crew_member_id", "crew_member_id"), ("ix_documents_checksum", "checksum"), ("ix_documents_document_type", "document_type"), ("ix_documents_document_number", "document_number"), ("ix_documents_expiry_date", "expiry_date"), ("ix_documents_match_status", "match_status")]:
        op.create_index(name, "documents", [column])

    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Integer(), nullable=False), sa.Column("action", sa.String(length=100), nullable=False),
        sa.Column("entity", sa.String(length=100), nullable=False), sa.Column("entity_id", sa.Integer(), nullable=True),
        sa.Column("message", sa.Text(), nullable=False), sa.Column("status", sa.String(length=30), nullable=False, server_default="success"),
        sa.Column("metadata_json", sa.JSON(), nullable=True), sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()), sa.PrimaryKeyConstraint("id"),
    )
    for name, column in [("ix_audit_logs_action", "action"), ("ix_audit_logs_entity", "entity"), ("ix_audit_logs_entity_id", "entity_id"), ("ix_audit_logs_status", "status"), ("ix_audit_logs_created_at", "created_at")]:
        op.create_index(name, "audit_logs", [column])


def downgrade() -> None:
    pass
