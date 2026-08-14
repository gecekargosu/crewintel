"""NotificationService — tek kanal soyutlaması.

Kanallar:
  system   → notifications tablosuna kayıt (uygulama içi zil)
  email    → notifications kaydı + SMTP ile gönderim (smtplib, config)
  whatsapp → notifications kaydı + stub (Meta Business API bilgileri
             girilene kadar "pending" bırakılır, aktivasyon sonra)

WhatsApp kanalı dışarıya çağrı yapmaz; WHATSAPP_API_TOKEN / WHATSAPP_PHONE_ID
ayarları boşken güvenli şekilde pending olarak bekler.
"""

from __future__ import annotations

import logging
import smtplib
from email.message import EmailMessage
from datetime import date, datetime, timedelta

from sqlalchemy.orm import Session

from app.core.config import Settings
from app.models.notification import Notification

logger = logging.getLogger(__name__)


def load_db_settings(db: Session) -> dict[str, str]:
    """UI'dan (Ayarlar → Bildirim) girilen SMTP / WhatsApp değerlerini okur.

    Öncelik: DB'de değer varsa DB, yoksa .env (config) kullanılır.
    """
    from app.models.setting import AppSetting

    return {row.key: row.value for row in db.query(AppSetting).all()}


class NotificationService:
    def __init__(self, db: Session, settings: Settings):
        self.db = db
        self.settings = settings
        self._db = load_db_settings(db) if db is not None else {}

    # ── DB'den gelen ayarlarla config birleştirme ────────────────────────────
    def _cfg(self, key: str):
        db_value = self._db.get(key)
        if db_value:
            return db_value
        return getattr(self.settings, key, None)

    # ── kayıt ────────────────────────────────────────────────────────────────
    def create(
        self,
        title: str,
        message: str | None = None,
        user_id: int | None = None,
        channel: str = "system",
        entity_type: str | None = None,
        entity_id: int | None = None,
        link: str | None = None,
    ) -> Notification:
        notification = Notification(
            user_id=user_id,
            title=title,
            message=message,
            channel=channel,
            status="pending",
            entity_type=entity_type,
            entity_id=entity_id,
            link=link,
        )
        self.db.add(notification)
        self.db.flush()
        return notification

    def notify(
        self,
        title: str,
        message: str | None = None,
        user_id: int | None = None,
        channel: str = "system",
        entity_type: str | None = None,
        entity_id: int | None = None,
        link: str | None = None,
    ) -> Notification:
        """Kanal bazında gönderim: system → kayıt; email → kayıt + SMTP;
        whatsapp → kayıt (pending, stub)."""
        notification = self.create(
            title=title, message=message, user_id=user_id, channel=channel,
            entity_type=entity_type, entity_id=entity_id, link=link,
        )
        if channel == "email":
            self._send_email(to_user_id=user_id, notification=notification)
        elif channel == "whatsapp":
            self._send_whatsapp(notification)
        else:
            notification.status = "sent"
        return notification

    # ── email kanalı ─────────────────────────────────────────────────────────
    def _email_config(self):
        return {
            "host": self._cfg("smtp_host"),
            "port": int(self._cfg("smtp_port") or self.settings.smtp_port or 587),
            "user": self._cfg("smtp_user"),
            "password": self._cfg("smtp_password"),
            "from": self._cfg("smtp_from"),
            "tls": self.settings.smtp_tls,
        }

    def _send_email(self, to_user_id: int | None, notification: Notification) -> None:
        cfg = self._email_config()
        if not (cfg["host"] and cfg["from"]):
            logger.warning("SMTP yapılandırılmamış — email bildirimi pending bırakıldı (id=%s)", notification.id)
            notification.status = "pending"
            return
        if to_user_id is None:
            notification.status = "pending"
            return
        from app.models.user import User

        user = self.db.get(User, to_user_id)
        if user is None or not user.email:
            notification.status = "pending"
            return
        try:
            message = EmailMessage()
            message["Subject"] = notification.title
            message["From"] = cfg["from"]
            message["To"] = user.email
            message.set_content(notification.message or notification.title)
            with smtplib.SMTP(cfg["host"], cfg["port"], timeout=15) as server:
                if cfg["tls"]:
                    server.starttls()
                if cfg["user"]:
                    server.login(cfg["user"], cfg["password"] or "")
                server.send_message(message)
            notification.status = "sent"
        except Exception as exc:  # noqa: BLE001 — ağ hatası tek bildirimi düşürmesin
            logger.error("Email gönderilemedi (notif %s): %s", notification.id, exc)
            notification.status = "failed"

    def notify_email_to(
        self,
        title: str,
        message: str | None,
        to_email: str,
        entity_type: str | None = None,
        entity_id: int | None = None,
    ) -> Notification:
        """Doğrudan bir e-posta adresine gönderim (personelin kendi maili).

        SMTP yapılandırılmamışsa kayıt 'pending' olarak kalır ve Ayarlar'dan
        SMTP girildiğinde yeniden denenebilir.
        """
        notification = self.create(
            title=title, message=message, channel="email",
            entity_type=entity_type, entity_id=entity_id,
        )
        self._send_email_to_address(to_email, notification)
        return notification

    def _send_email_to_address(self, to_email: str, notification: Notification) -> None:
        cfg = self._email_config()
        if not (cfg["host"] and cfg["from"]):
            logger.warning("SMTP yapılandırılmamış — email pending bırakıldı (id=%s)", notification.id)
            notification.status = "pending"
            return
        try:
            message = EmailMessage()
            message["Subject"] = notification.title
            message["From"] = cfg["from"]
            message["To"] = to_email
            message.set_content(notification.message or notification.title)
            with smtplib.SMTP(cfg["host"], cfg["port"], timeout=15) as server:
                if cfg["tls"]:
                    server.starttls()
                if cfg["user"]:
                    server.login(cfg["user"], cfg["password"] or "")
                server.send_message(message)
            notification.status = "sent"
        except Exception as exc:  # noqa: BLE001 — ağ hatası tek bildirimi düşürmesin
            logger.error("Email gönderilemedi (notif %s): %s", notification.id, exc)
            notification.status = "failed"

    # ── whatsapp kanalı (stub — Meta bilgileri girilince aktifleşir) ─────────
    def _send_whatsapp(self, notification: Notification) -> None:
        api_token = self._cfg("whatsapp_api_token")
        phone_id = self._cfg("whatsapp_phone_id")
        if not (api_token and phone_id):
            logger.info("WhatsApp yapılandırılmamış — bildirim pending bırakıldı (id=%s)", notification.id)
            notification.status = "pending"
            return
        # Hedef: Ayarlar'dan girilen admin/personel WhatsApp numarası
        target = self._cfg("whatsapp_admin_number")
        if target:
            notification.message = (notification.message or "") + f"\n(Hedef: {target})"
        # Aktivasyon sonrası: Meta Cloud API POST /messages çağrısı buraya.
        # Template onayı gerektiği için şimdilik gerçek çağrı yapılmıyor.
        logger.info("WHATSAPP STUB: %s → %s", notification.title, target or "(hedef yok)")
        notification.status = "pending"

    # ── uyarı üretimi ────────────────────────────────────────────────────────
    def generate_due_alerts(self, days_urgent: int = 30, days_approaching: int = 90) -> int:
        """Süresi geçen/yaklaşan belgeler, biten kontratlar ve onay bekleyen
        belgeler için bildirim üretir. Tekrar üretimde aynı kayıtı çoğaltmaz."""
        from app.models.crew_member import CrewMember
        from app.models.document import Document
        from app.models.contract import Contract
        from app.models.user import User

        today = date.today()
        created = 0

        def _exists(title: str, entity_type: str, entity_id: int | None) -> bool:
            return (
                self.db.query(Notification)
                .filter(
                    Notification.title == title,
                    Notification.entity_type == entity_type,
                    Notification.entity_id == entity_id,
                    Notification.created_at >= datetime.now().replace(hour=0, minute=0, second=0, microsecond=0),
                )
                .first()
                is not None
            )

        # Süresi geçen / yaklaşan belgeler
        expiry_docs = (
            self.db.query(Document, CrewMember)
            .join(CrewMember, Document.crew_member_id == CrewMember.id)
            .filter(Document.expiry_date.isnot(None), Document.archived_at.is_(None))
            .all()
        )
        for doc, crew in expiry_docs:
            days = (doc.expiry_date - today).days
            if days < 0:
                title = f"{crew.first_name} {crew.last_name} — {doc.document_type} süresi DOLDU"
                message = f"{doc.original_filename} belgesi {doc.expiry_date} tarihinde geçerliliğini yitirdi."
            elif days <= days_urgent:
                title = f"{crew.first_name} {crew.last_name} — {doc.document_type} {days} gün içinde bitiyor"
                message = f"{doc.original_filename} belgesi {doc.expiry_date} tarihinde sona eriyor."
            else:
                continue
            if not _exists(title, "document", doc.id):
                self.create(title=title, message=message, channel="system",
                            entity_type="document", entity_id=doc.id, link=f"/documents?doc={doc.id}")
                created += 1

        # Biten kontratlar (7 gün)
        soon = today + timedelta(days=7)
        contracts = (
            self.db.query(Contract, CrewMember)
            .join(CrewMember, Contract.crew_member_id == CrewMember.id)
            .filter(Contract.end_date.isnot(None), Contract.end_date <= soon, Contract.status == "active")
            .all()
        )
        for contract, crew in contracts:
            title = f"{crew.first_name} {crew.last_name} — kontrat {contract.end_date} bitiyor"
            if not _exists(title, "contract", contract.id):
                self.create(title=title, message=contract.contract_number, channel="system",
                            entity_type="contract", entity_id=contract.id)
                created += 1

        # Onay bekleyen belgeler (admin'e)
        pending = self.db.query(Document).filter(Document.match_status.in_(["review_required", "pending_approval"])).count()
        if pending > 0:
            title = f"{pending} belge onay/inceleme bekliyor"
            if not _exists(title, "document", None):
                admin_users = self.db.query(User).filter(User.role == "admin", User.is_active.is_(True)).all()
                for admin in admin_users:
                    self.create(title=title, message="Belge kuyruğunu kontrol edin.", channel="system",
                                user_id=admin.id, entity_type="document", link="/documents")
                    created += 1

        self.db.commit()
        return created
