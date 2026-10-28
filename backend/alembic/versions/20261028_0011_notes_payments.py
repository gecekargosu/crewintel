"""0011 — Notlar ve maaş/ödeme kayıtları.

Notlar: kullanıcıya özel (user_id), personele bağlanabilir.
Ödemeler: personel başına tutar/tarih/tip kaydı; muhasebe için Numeric(12,2).

Not: Daha eski bir sürümde (GitHub master) `notes` tablosu migration dışında
oluşturulmuş olabilir. Bu yüzden geçiş idempotenttir: tablo varsa yeniden
yaratılmaz, yalnızca eksik `user_id` kolonu eklenir.
"""

import sqlalchemy as sa
from alembic import op

revision = "20261028_0011"
down_revision = "20260818_0010"
branch_labels = None
depends_on = None


def _has_column(inspector, table: str, column: str) -> bool:
    return column in {item["name"] for item in inspector.get_columns(table)}


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())

    # ── notes ────────────────────────────────────────────────────────────────
    if not inspector.has_table("notes"):
        op.create_table(
            "notes",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("title", sa.String(length=200), nullable=False),
            sa.Column("body", sa.Text(), nullable=False, server_default=""),
            sa.Column("priority", sa.String(length=20), nullable=False, server_default="normal"),
            sa.Column("done", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column(
                "crew_member_id",
                sa.Integer(),
                sa.ForeignKey("crew_members.id", ondelete="SET NULL"),
                nullable=True,
            ),
            sa.Column(
                "user_id",
                sa.Integer(),
                sa.ForeignKey("users.id", ondelete="CASCADE"),
                nullable=True,
            ),
            sa.Column("user_email", sa.String(length=255), nullable=False, server_default=""),
            sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
            sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        )
    elif not _has_column(inspector, "notes", "user_id"):
        op.add_column("notes", sa.Column("user_id", sa.Integer(), nullable=True))
        op.create_foreign_key(
            "fk_notes_user_id", "notes", "users", ["user_id"], ["id"], ondelete="CASCADE"
        )

    op.execute("CREATE INDEX IF NOT EXISTS ix_notes_id ON notes (id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_notes_user_id ON notes (user_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_notes_crew_member_id ON notes (crew_member_id)")

    # ── payments ─────────────────────────────────────────────────────────────
    if not inspector.has_table("payments"):
        op.create_table(
            "payments",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column(
                "crew_member_id",
                sa.Integer(),
                sa.ForeignKey("crew_members.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column("amount", sa.Numeric(12, 2), nullable=False),
            sa.Column("currency", sa.String(length=10), nullable=False, server_default="USD"),
            sa.Column("payment_type", sa.String(length=30), nullable=False, server_default="salary"),
            sa.Column("description", sa.Text(), nullable=False, server_default=""),
            sa.Column("payment_date", sa.Date(), nullable=False),
            sa.Column(
                "created_by_user_id",
                sa.Integer(),
                sa.ForeignKey("users.id", ondelete="SET NULL"),
                nullable=True,
            ),
            sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
            sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        )

    op.execute("CREATE INDEX IF NOT EXISTS ix_payments_id ON payments (id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_payments_crew_member_id ON payments (crew_member_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_payments_payment_date ON payments (payment_date)")

    # Eski kayıtlarda güven skoru 100'ü aşabiliyordu ("%215" gösterimi);
    # yüzde alanı 0-100 aralığına çekilir. Ham skor DocumentMatch/audit
    # kayıtlarında duruyor, burada yalnızca gösterim alanı düzeltiliyor.
    op.execute("UPDATE documents SET match_confidence = 100 WHERE match_confidence > 100")


def downgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    if inspector.has_table("payments"):
        op.drop_table("payments")
    # `notes` bu sürümden önce de var olabildiği için yalnızca eklenen kolon
    # kaldırılır; tablo silinmez (veri kaybı olmasın).
    if inspector.has_table("notes") and _has_column(inspector, "notes", "user_id"):
        op.drop_constraint("fk_notes_user_id", "notes", type_="foreignkey")
        op.drop_column("notes", "user_id")
