"""Add users, ships, assignments, contracts, and crew profile fields."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision = "20260809_0002"
down_revision = "20260809_0001"
branch_labels = None
depends_on = None


def _column_names(table_name: str) -> set[str]:
    return {column["name"] for column in inspect(op.get_bind()).get_columns(table_name)}


def upgrade() -> None:
    bind = op.get_bind()
    existing_crew_columns = _column_names("crew_members")
    crew_columns = [
        ("date_of_birth", sa.Date()),
        ("passport_number", sa.String(length=100)),
        ("seaman_book_number", sa.String(length=100)),
        ("rank", sa.String(length=100)),
        ("phone", sa.String(length=50)),
        ("email", sa.String(length=255)),
        ("address", sa.Text()),
        ("emergency_contact_name", sa.String(length=200)),
        ("emergency_contact_phone", sa.String(length=50)),
    ]
    with op.batch_alter_table("crew_members") as batch_op:
        for column_name, column_type in crew_columns:
            if column_name not in existing_crew_columns:
                batch_op.add_column(sa.Column(column_name, column_type, nullable=True))
        if "status" not in existing_crew_columns:
            batch_op.add_column(sa.Column("status", sa.String(length=50), nullable=False, server_default="active"))
        if "updated_at" not in existing_crew_columns:
            batch_op.add_column(sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()))

    existing_crew_indexes = {index["name"] for index in inspect(bind).get_indexes("crew_members")}
    for index_name, column_name in [
        ("ix_crew_members_first_name", "first_name"),
        ("ix_crew_members_last_name", "last_name"),
        ("ix_crew_members_position", "position"),
        ("ix_crew_members_status", "status"),
    ]:
        if index_name not in existing_crew_indexes:
            op.create_index(index_name, "crew_members", [column_name])

    if not inspect(bind).has_table("users"):
        op.create_table(
            "users",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("email", sa.String(length=255), nullable=False),
            sa.Column("full_name", sa.String(length=200), nullable=False),
            sa.Column("role", sa.String(length=50), nullable=False, server_default="viewer"),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("email"),
        )
        op.create_index("ix_users_email", "users", ["email"], unique=True)

    if not inspect(bind).has_table("ships"):
        op.create_table(
            "ships",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("name", sa.String(length=200), nullable=False),
            sa.Column("imo_number", sa.String(length=7), nullable=True),
            sa.Column("flag", sa.String(length=100), nullable=True),
            sa.Column("ship_type", sa.String(length=100), nullable=True),
            sa.Column("company", sa.String(length=200), nullable=True),
            sa.Column("status", sa.String(length=50), nullable=False, server_default="active"),
            sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("imo_number"),
        )
        op.create_index("ix_ships_name", "ships", ["name"])
        op.create_index("ix_ships_status", "ships", ["status"])

    if not inspect(bind).has_table("ship_crew_assignments"):
        op.create_table(
            "ship_crew_assignments",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("ship_id", sa.Integer(), nullable=False),
            sa.Column("crew_member_id", sa.Integer(), nullable=False),
            sa.Column("position", sa.String(length=100), nullable=False),
            sa.Column("start_date", sa.Date(), nullable=False),
            sa.Column("end_date", sa.Date(), nullable=True),
            sa.Column("status", sa.String(length=50), nullable=False, server_default="active"),
            sa.Column("notes", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.ForeignKeyConstraint(["crew_member_id"], ["crew_members.id"]),
            sa.ForeignKeyConstraint(["ship_id"], ["ships.id"]),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_ship_crew_assignments_ship_id", "ship_crew_assignments", ["ship_id"])
        op.create_index("ix_ship_crew_assignments_crew_member_id", "ship_crew_assignments", ["crew_member_id"])
        op.create_index("ix_ship_crew_assignments_status", "ship_crew_assignments", ["status"])

    if not inspect(bind).has_table("contracts"):
        op.create_table(
            "contracts",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("crew_member_id", sa.Integer(), nullable=False),
            sa.Column("ship_id", sa.Integer(), nullable=False),
            sa.Column("contract_number", sa.String(length=100), nullable=False),
            sa.Column("contract_type", sa.String(length=100), nullable=False),
            sa.Column("start_date", sa.Date(), nullable=False),
            sa.Column("end_date", sa.Date(), nullable=True),
            sa.Column("status", sa.String(length=50), nullable=False, server_default="active"),
            sa.Column("notes", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.ForeignKeyConstraint(["crew_member_id"], ["crew_members.id"]),
            sa.ForeignKeyConstraint(["ship_id"], ["ships.id"]),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("contract_number"),
        )
        op.create_index("ix_contracts_crew_member_id", "contracts", ["crew_member_id"])
        op.create_index("ix_contracts_ship_id", "contracts", ["ship_id"])
        op.create_index("ix_contracts_contract_number", "contracts", ["contract_number"], unique=True)
        op.create_index("ix_contracts_status", "contracts", ["status"])


def downgrade() -> None:
    # Intentionally non-destructive: core operational records are never dropped automatically.
    pass
