from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class AppSetting(Base):
    """UI'dan düzenlenebilen key-value ayarlar (SMTP, WhatsApp hedef, vb.)."""

    __tablename__ = "app_settings"

    key: Mapped[str] = mapped_column(String(100), primary_key=True)
    value: Mapped[str] = mapped_column(String(500), default="")
