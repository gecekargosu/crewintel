"""Push bildirim servisi — Expo Push API (M1 Mobile).

- Kullanıcının `user_devices` tablosundaki token'larına gönderir.
- Expo yanıtında `DeviceNotRegistered` dönen token'lar silinir (duplicate/ölü token temizliği).
- Hata asla yukarı fırlatmaz: bildirim gönderilememesi ana iş akışını bozmaz.
"""

from __future__ import annotations

from datetime import UTC, datetime

import httpx
from sqlalchemy.orm import Session

from app.models.user_device import UserDevice

EXPO_PUSH_URL = "https://exp.host/--/api/v2/push/send"


def send_push(
    db: Session,
    user_id: int,
    title: str,
    body: str,
    data: dict | None = None,
    platform_hint: str | None = None,
) -> dict:
    """Kullanıcının tüm cihazlarına push gönderir.

    Returns:
        {"ok": bool, "sent": int, "skipped": int, "removed": [tokens], "errors": [...]}
    """
    query = db.query(UserDevice).filter(UserDevice.user_id == user_id)
    if platform_hint:
        query = query.filter(UserDevice.platform == platform_hint)
    devices = query.all()
    if not devices:
        return {"ok": True, "sent": 0, "skipped": 0, "removed": [], "errors": []}

    messages = [
        {
            "to": device.push_token,
            "title": title,
            "body": body,
            "data": data or {},
            "sound": "default",
        }
        for device in devices
    ]

    removed: list[str] = []
    errors: list[dict] = []
    try:
        response = httpx.post(EXPO_PUSH_URL, json=messages, timeout=15)
        response.raise_for_status()
        results = response.json().get("data", [])
    except Exception as error:  # noqa: BLE001 — push hatası akışı durdurmamalı
        return {
            "ok": False,
            "sent": 0,
            "skipped": len(messages),
            "removed": [],
            "errors": [{"token": device.push_token, "error": str(error)} for device in devices],
        }

    now = datetime.now(UTC).replace(tzinfo=None)
    sent = 0
    for device, result in zip(devices, results, strict=False):
        status = result.get("status")
        if status == "ok":
            sent += 1
            device.last_seen = now
        elif status == "error":
            details = result.get("details", {})
            if details.get("error") in ("DeviceNotRegistered", "MessageTooBig"):
                removed.append(device.push_token)
                db.delete(device)
            else:
                errors.append({"token": device.push_token, "error": details.get("error")})
    db.commit()
    return {"ok": len(errors) == 0, "sent": sent, "skipped": len(messages) - sent,
            "removed": removed, "errors": errors}
