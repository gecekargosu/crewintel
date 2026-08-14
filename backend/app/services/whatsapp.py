"""WhatsApp Business API entegrasyonu (Phase 8).

Tasarım:
- WhatsAppMessage tablosu bir kuyruktur: publish sırasında her alıcı için bir satır
  oluşturulur (status=pending). Gerçek gönderim Meta Graph API'ye çağrı yapılarak
  yapılır; token / phone_id yoksa mesajlar kuyrukta kalır ve sahte başarı ÜRETİLMEZ
  (publication.status="queued", error="WhatsApp bağlantısı yapılandırılmadı").

- Meta politikaları: toplu gönderim template mesajı gerektirir. Bu fazda kuyruk +
  provider katmanı hazırlanır; template id'leri ileride ilan tipine göre eşlenir.

Token'lar DB'de (app_settings) saklanır, asla frontend'e / loglara yazılmaz.
"""

from __future__ import annotations

import logging
import re
from datetime import UTC, datetime

import httpx
from sqlalchemy.orm import Session

from app.models.job import JobPosting, JobPublication, WhatsAppMessage
from app.services.notifications import load_db_settings

logger = logging.getLogger(__name__)

GRAPH_API_BASE = "https://graph.facebook.com"
GRAPH_API_VERSION = "v21.0"


class WhatsAppNotConfigured(Exception):
    """Token / phone ID eksik — gerçek gönderim yapılamaz."""


def normalize_phone(phone: str | None) -> str:
    """+90 532 327 61 21 → 905323276121 (sadece rakamlar, başta 00 varsa kaldır)."""
    if not phone:
        return ""
    digits = re.sub(r"[^0-9]", "", phone or "")
    if digits.startswith("00"):
        digits = digits[2:]
    return digits


def _now() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


class WhatsAppProvider:
    def __init__(self, db: Session):
        self.db = db
        self._settings = load_db_settings(db) if db is not None else {}

    def _cfg(self, key: str) -> str:
        return (self._settings.get(key) or "").strip()

    def is_configured(self) -> bool:
        return bool(self._cfg("whatsapp_api_token") and self._cfg("whatsapp_phone_id"))

    # ── gerçek Graph API gönderimi ──────────────────────────────────────────
    def send_text(self, to_phone: str, text: str) -> dict:
        """Meta WhatsApp Business API üzerinden text mesajı gönderir."""
        if not self.is_configured():
            raise WhatsAppNotConfigured(
                "whatsapp_api_token / whatsapp_phone_id ayarları tanımlı değil."
            )
        token = self._cfg("whatsapp_api_token")
        phone_id = self._cfg("whatsapp_phone_id")
        url = f"{GRAPH_API_BASE}/{GRAPH_API_VERSION}/{phone_id}/messages"
        payload = {
            "messaging_product": "whatsapp",
            "to": normalize_phone(to_phone),
            "type": "text",
            "text": {"body": text},
        }
        headers = {"Authorization": f"Bearer {token}"}
        try:
            with httpx.Client(timeout=30) as client:
                response = client.post(url, json=payload, headers=headers)
        except httpx.HTTPError as error:
            logger.warning("WhatsApp HTTP hatası: %s", error)
            return {"ok": False, "error": f"HTTP: {error}"}
        if response.status_code >= 400:
            logger.warning("WhatsApp API hatası %s: %s", response.status_code, response.text[:300])
            return {"ok": False, "error": f"API {response.status_code}: {response.text[:200]}"}
        data = response.json()
        return {"ok": True, "message_id": (data.get("messages") or [{}])[0].get("id")}

    # ── kuyruk işleme ───────────────────────────────────────────────────────
    def process_queue(self, limit: int = 50, posting_id: int | None = None) -> dict:
        """pending mesajları göndermeyi dener. Sonuç: {sent, failed, skipped, remaining}."""
        query = self.db.query(WhatsAppMessage).filter(WhatsAppMessage.status == "pending")
        if posting_id is not None:
            query = query.filter(WhatsAppMessage.job_posting_id == posting_id)
        messages = query.order_by(WhatsAppMessage.id).limit(limit).all()

        sent = failed = skipped = 0
        for message in messages:
            message.attempts = (message.attempts or 0) + 1
            if not self.is_configured():
                message.last_error = "WhatsApp bağlantısı yapılandırılmadı (Ayarlar → Bildirim)."
                skipped += 1
                continue
            try:
                result = self.send_text(message.phone, message.text)
            except WhatsAppNotConfigured as error:
                message.last_error = str(error)
                skipped += 1
                continue
            if result.get("ok"):
                message.status = "sent"
                message.provider_message_id = result.get("message_id")
                message.sent_at = _now()
                message.last_error = None
                sent += 1
            else:
                message.status = "failed"
                message.last_error = result.get("error", "Bilinmeyen hata")
                failed += 1
        self.db.commit()

        remaining = (
            self.db.query(WhatsAppMessage)
            .filter(WhatsAppMessage.status == "pending")
            .count()
        )
        return {"sent": sent, "failed": failed, "skipped": skipped, "remaining": remaining}

    def queue_job_broadcast(
        self, posting: JobPosting, crew_ids: list[int], text: str
    ) -> tuple[int, int]:
        """Seçili personellere ilan kuyruğu oluşturur (duplicate korumalı).

        Dönüş: (oluşturulan, zaten kuyrukta olan)
        """
        from app.models.crew_member import CrewMember

        created = skipped = 0
        if crew_ids:
            crews = (
                self.db.query(CrewMember)
                .filter(CrewMember.id.in_(crew_ids), CrewMember.phone.isnot(None))
                .all()
            )
            for crew in crews:
                phone = normalize_phone(crew.phone)
                if not phone:
                    skipped += 1
                    continue
                existing = (
                    self.db.query(WhatsAppMessage)
                    .filter(
                        WhatsAppMessage.job_posting_id == posting.id,
                        WhatsAppMessage.crew_member_id == crew.id,
                    )
                    .first()
                )
                if existing:
                    skipped += 1
                    continue
                self.db.add(
                    WhatsAppMessage(
                        job_posting_id=posting.id,
                        crew_member_id=crew.id,
                        phone=phone,
                        text=text,
                        status="pending",
                    )
                )
                created += 1
        self.db.commit()
        return created, skipped
