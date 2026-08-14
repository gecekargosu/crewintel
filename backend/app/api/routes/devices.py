"""Mobil cihaz kayıtları — push token yönetimi (M1).

- POST /api/devices: token kaydet (UNIQUE(user_id, push_token) → upsert).
- DELETE /api/devices/{token}: çıkışta token sil.
"""

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.database import get_db
from app.models.user import User
from app.models.user_device import UserDevice

router = APIRouter(prefix="/api/devices", tags=["Devices"])


@router.post("", status_code=status.HTTP_201_CREATED)
def register_device(
    payload: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    push_token = (payload.get("push_token") or "").strip()
    if not push_token or len(push_token) > 255:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                            detail="Geçerli bir push_token gereklidir.")
    platform = (payload.get("platform") or "android").strip().lower()
    if platform not in ("android", "ios", "web"):
        platform = "android"

    device = (
        db.query(UserDevice)
        .filter(
            UserDevice.user_id == current_user.id,
            UserDevice.push_token == push_token,
        )
        .first()
    )
    now = datetime.now(UTC).replace(tzinfo=None)
    if device:
        device.platform = platform
        device.last_seen = now
        if payload.get("device_name"):
            device.device_name = (payload["device_name"] or "")[:100]
        db.commit()
        return {"id": device.id, "registered": True, "updated": True}

    device = UserDevice(
        user_id=current_user.id,
        platform=platform,
        push_token=push_token,
        device_name=(payload.get("device_name") or "")[:100] or None,
        last_seen=now,
    )
    db.add(device)
    db.commit()
    db.refresh(device)
    return {"id": device.id, "registered": True, "updated": False}


@router.delete("/{push_token}", status_code=status.HTTP_204_NO_CONTENT)
def unregister_device(
    push_token: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    device = (
        db.query(UserDevice)
        .filter(
            UserDevice.user_id == current_user.id,
            UserDevice.push_token == push_token,
        )
        .first()
    )
    if device:
        db.delete(device)
        db.commit()
