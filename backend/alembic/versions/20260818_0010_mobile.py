"""0010 — M1 Mobile: crew_members iş tercihleri, user_devices, conversations,
messages, job_applications.match_score / applied_from.

Tüm eklemeler nullable/default'ludur — mevcut üretim verisi etkilenmez.
"""

import sqlalchemy as sa
from alembic import op

revision = "20260818_0010"
down_revision = "20260818_0009"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── crew_members: iş tercihleri / müsaitlik (M1 Mobile) ─────────────────
    op.add_column("crew_members", sa.Column("available_from", sa.Date(), nullable=True))
    op.add_column("crew_members", sa.Column("job_preferences", sa.JSON(), nullable=True))
    op.add_column("crew_members", sa.Column("vessel_types_experience", sa.String(length=200), nullable=True))
    op.add_column("crew_members", sa.Column("expected_salary_min", sa.Integer(), nullable=True))
    op.add_column("crew_members", sa.Column("expected_salary_max", sa.Integer(), nullable=True))
    op.add_column("crew_members", sa.Column("expected_salary_currency", sa.String(length=10), nullable=True))
    op.add_column("crew_members", sa.Column("expected_salary_period", sa.String(length=30), nullable=True))

    # ── job_applications: skor + kaynak ─────────────────────────────────────
    op.add_column("job_applications", sa.Column("match_score", sa.Integer(), nullable=True))
    op.add_column(
        "job_applications",
        sa.Column("applied_from", sa.String(length=20), nullable=False, server_default="portal"),
    )

    # ── user_devices (push token) ───────────────────────────────────────────
    op.create_table(
        "user_devices",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("platform", sa.String(length=20), nullable=False, server_default="android"),
        sa.Column("push_token", sa.String(length=255), nullable=False),
        sa.Column("device_name", sa.String(length=100), nullable=True),
        sa.Column("last_seen", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("user_id", "push_token", name="uq_user_device_token"),
    )
    op.create_index("ix_user_devices_id", "user_devices", ["id"])
    op.create_index("ix_user_devices_user_id", "user_devices", ["user_id"])
    op.create_index("ix_user_devices_push_token", "user_devices", ["push_token"])

    # ── conversations + messages ────────────────────────────────────────────
    op.create_table(
        "conversations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "participant_a",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "participant_b",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("subject", sa.String(length=200), nullable=True),
        sa.Column("last_message_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_conversations_id", "conversations", ["id"])
    op.create_index("ix_conversations_participant_a", "conversations", ["participant_a"])
    op.create_index("ix_conversations_participant_b", "conversations", ["participant_b"])
    op.create_index("ix_conversations_last_message_at", "conversations", ["last_message_at"])

    op.create_table(
        "messages",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "conversation_id",
            sa.Integer(),
            sa.ForeignKey("conversations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("sender_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("kind", sa.String(length=30), nullable=False, server_default="chat"),
        sa.Column("body", sa.Text(), nullable=True),
        sa.Column("attachment_path", sa.String(length=300), nullable=True),
        sa.Column("read_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_messages_id", "messages", ["id"])
    op.create_index("ix_messages_conversation_id", "messages", ["conversation_id"])
    op.create_index("ix_messages_sender_user_id", "messages", ["sender_user_id"])
    op.create_index("ix_messages_created_at", "messages", ["created_at"])


def downgrade() -> None:
    op.drop_table("messages")
    op.drop_table("conversations")
    op.drop_table("user_devices")
    op.drop_column("job_applications", "applied_from")
    op.drop_column("job_applications", "match_score")
    for col in [
        "expected_salary_period", "expected_salary_currency", "expected_salary_max",
        "expected_salary_min", "vessel_types_experience", "job_preferences",
        "available_from",
    ]:
        op.drop_column("crew_members", col)
