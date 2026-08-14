"""0007 — app_settings tablosu (UI'dan düzenlenebilir SMTP / WhatsApp hedef ayarları)."""

import sqlalchemy as sa
from alembic import op

revision = "20260818_0007"
down_revision = "20260818_0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "app_settings",
        sa.Column("key", sa.String(length=100), primary_key=True),
        sa.Column("value", sa.String(length=500), nullable=False, server_default=""),
    )


def downgrade() -> None:
    op.drop_table("app_settings")
