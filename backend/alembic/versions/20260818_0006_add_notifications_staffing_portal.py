"""Phase 4B: notifications, user<->crew link, availability, document archive, ship positions."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision = "20260818_0006"
down_revision = "20260817_0005"
branch_labels = None
depends_on = None


def _table_exists(table_name: str) -> bool:
    return table_name in inspect(op.get_bind()).get_table_names()


def _column_exists(table_name: str, column_name: str) -> bool:
    inspector = inspect(op.get_bind())
    return column_name in [c["name"] for c in inspector.get_columns(table_name)]


def upgrade() -> None:
    # 1) notifications
    if not _table_exists("notifications"):
        op.create_table(
            "notifications",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("user_id", sa.Integer(), nullable=True, index=True),
            sa.Column("title", sa.String(length=200), nullable=False),
            sa.Column("message", sa.Text(), nullable=True),
            sa.Column("channel", sa.String(length=20), nullable=False, server_default="system"),
            sa.Column("status", sa.String(length=20), nullable=False, server_default="pending"),
            sa.Column("entity_type", sa.String(length=50), nullable=True),
            sa.Column("entity_id", sa.Integer(), nullable=True),
            sa.Column("link", sa.String(255), nullable=True),
            sa.Column("read_at", sa.DateTime(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        )
        op.create_index("ix_notifications_user_status", "notifications", ["user_id", "status"])

    # 2) users.crew_member_id (personel portalı bağlantısı)
    if not _column_exists("users", "crew_member_id"):
        op.add_column("users", sa.Column("crew_member_id", sa.Integer(), nullable=True))
        op.create_foreign_key("fk_users_crew_member_id", "users", "crew_members", ["crew_member_id"], ["id"])

    # 3) crew_members.availability (müsaitlik durumu)
    if not _column_exists("crew_members", "availability"):
        op.add_column("crew_members", sa.Column("availability", sa.String(length=30), nullable=True, server_default="available"))

    # 4) documents.archived_at (belge versiyon/arşiv işareti)
    if not _column_exists("documents", "archived_at"):
        op.add_column("documents", sa.Column("archived_at", sa.DateTime(), nullable=True))

    # 5) ship_positions (gemi kadro planı)
    if not _table_exists("ship_positions"):
        op.create_table(
            "ship_positions",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("ship_id", sa.Integer(), nullable=False, index=True),
            sa.Column("position", sa.String(length=100), nullable=False),
            sa.Column("required_count", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        )
        op.create_unique_constraint("uq_ship_positions_ship_position", "ship_positions", ["ship_id", "position"])


def downgrade() -> None:
    if _table_exists("ship_positions"):
        op.drop_table("ship_positions")
    if _column_exists("documents", "archived_at"):
        op.drop_column("documents", "archived_at")
    if _column_exists("crew_members", "availability"):
        op.drop_column("crew_members", "availability")
    if _column_exists("users", "crew_member_id"):
        op.drop_constraint("fk_users_crew_member_id", "users", type_="foreignkey")
        op.drop_column("users", "crew_member_id")
    if _table_exists("notifications"):
        op.drop_table("notifications")
