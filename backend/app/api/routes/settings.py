"""Ayarlar — UI'dan düzenlenebilen bildirim / iletişim ayarları (admin)."""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_roles
from app.db.database import get_db
from app.models.setting import AppSetting
from app.models.user import User

router = APIRouter(prefix="/api/settings", tags=["Settings"])

# UI'dan yönetilebilir anahtarlar (gizli olanlar okurken maskelenir)
EDITABLE_KEYS = {
    "smtp_host",
    "smtp_port",
    "smtp_user",
    "smtp_password",
    "smtp_from",
    "whatsapp_admin_number",
    "whatsapp_api_token",
    "whatsapp_phone_id",
    "whatsapp_business_account_id",
    "whatsapp_api_base_url",
    "whatsapp_webhook_verify_token",
    "whatsapp_sender_number",
    "instagram_access_token",
    "instagram_page_id",
    "facebook_access_token",
    "facebook_page_id",
}
_SECRET_KEYS = {
    "smtp_password",
    "whatsapp_api_token",
    "whatsapp_business_account_id",
    "whatsapp_webhook_verify_token",
    "instagram_access_token",
    "facebook_access_token",
}


def _mask(value: str) -> str:
    if not value:
        return ""
    if len(value) <= 4:
        return "****"
    return value[:2] + "****" + value[-2:]


class SettingsUpdateRequest(BaseModel):
    values: dict[str, str]


def _load_all(db: Session) -> dict[str, str]:
    return {row.key: row.value for row in db.query(AppSetting).all()}


def get_setting(db: Session, key: str, default: str | None = None) -> str | None:
    row = db.get(AppSetting, key)
    return row.value if row is not None else default


@router.get("", response_model=dict)
def get_settings(
    _admin: User = Depends(require_roles("admin")),
    db: Session = Depends(get_db),
):
    stored = _load_all(db)
    result: dict[str, str] = {}
    for key in EDITABLE_KEYS:
        value = stored.get(key, "")
        if key in _SECRET_KEYS and value:
            value = _mask(value)
        result[key] = value
    return {"values": result}


@router.get("/contact")
def get_contact_info(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """İletişim sayfası için yönetici WhatsApp numarası (hassas değil)."""
    return {"whatsapp_admin_number": get_setting(db, "whatsapp_admin_number") or ""}


@router.put("", response_model=dict)
def update_settings(
    payload: SettingsUpdateRequest,
    admin: User = Depends(require_roles("admin")),
    db: Session = Depends(get_db),
):
    import re

    for key, value in payload.values.items():
        if key not in EDITABLE_KEYS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Bilinmeyen ayar anahtarı: {key}",
            )
        value = (value or "").strip()
        if key == "whatsapp_admin_number" and value:
            digits = re.sub(r"[^0-9]", "", value)
            if len(digits) < 10:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="WhatsApp numarası geçerli değil (en az 10 hane).",
                )
        if key == "smtp_port" and value:
            try:
                int(value)
            except ValueError as exc:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="SMTP portu sayı olmalı.",
                ) from exc
        row = db.get(AppSetting, key)
        if row is None:
            db.add(AppSetting(key=key, value=value))
        else:
            row.value = value
    from app.services.audit import log_event

    log_event(db, "settings_updated", "settings", None,
              f"Settings updated by {admin.email}",
              user_email=admin.email)
    db.commit()
    return {"status": "ok"}
