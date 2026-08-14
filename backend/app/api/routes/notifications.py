from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_staff_read, require_roles
from app.core.config import get_settings
from app.db.database import get_db
from app.models.notification import Notification
from app.models.user import User
from app.services.notifications import NotificationService


router = APIRouter(prefix="/api/notifications", tags=["Notifications"])


def _serialize(n: Notification) -> dict:
    return {
        "id": n.id,
        "title": n.title,
        "message": n.message,
        "channel": n.channel,
        "status": n.status,
        "entity_type": n.entity_type,
        "entity_id": n.entity_id,
        "link": n.link,
        "read": n.read_at is not None,
        "created_at": n.created_at.isoformat() if n.created_at else None,
    }


@router.get("/", response_model=list[dict])
def list_my_notifications(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_staff_read),
    unread_only: bool = False,
):
    query = db.query(Notification).filter(
        (Notification.user_id == current_user.id) | (Notification.user_id.is_(None))
    )
    if unread_only:
        query = query.filter(Notification.read_at.is_(None))
    notifications = query.order_by(Notification.created_at.desc()).limit(100).all()
    return [_serialize(n) for n in notifications]


@router.post("/{notification_id}/read", status_code=status.HTTP_204_NO_CONTENT)
def mark_read(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_staff_read),
):
    from datetime import UTC, datetime

    notification = db.get(Notification, notification_id)
    if notification is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found.")
    if notification.user_id is not None and notification.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your notification.")
    notification.read_at = datetime.now(UTC).replace(tzinfo=None)
    db.commit()


@router.post("/generate", response_model=dict)
def generate_alerts(
    db: Session = Depends(get_db),
    actor: User = Depends(require_roles("admin")),
):
    service = NotificationService(db, get_settings())
    created = service.generate_due_alerts()
    return {"created": created}


class SingleEmailRequest(BaseModel):
    crew_member_id: int
    subject: str = Field(min_length=1, max_length=200)
    body: str = ""


class BulkEmailRequest(BaseModel):
    crew_ids: list[int] = Field(min_length=1)
    subject: str = Field(min_length=1, max_length=200)
    body: str = ""


@router.post("/send-email", response_model=dict)
def send_single_email(
    payload: SingleEmailRequest,
    db: Session = Depends(get_db),
    actor: User = Depends(require_roles("admin", "hr")),
):
    """Tek personele e-posta — personel detayındaki 'E-posta Gönder' butonu."""
    from app.models.crew_member import CrewMember
    from app.services.audit import log_event

    crew = db.get(CrewMember, payload.crew_member_id)
    if crew is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Personel bulunamadı.")
    if not crew.email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Bu personelin e-posta adresi kayıtlı değil.")
    service = NotificationService(db, get_settings())
    notification = service.notify_email_to(
        title=payload.subject, message=payload.body,
        to_email=crew.email, entity_type="crew_member", entity_id=crew.id,
    )
    log_event(db, "email_sent", "crew_member", crew.id,
              f"Email sent to {crew.email} ({payload.subject})",
              user_email=actor.email)
    db.commit()
    cfg = service._email_config()
    return {
        "status": notification.status,
        "recipient": crew.email,
        "smtp_configured": bool(cfg["host"] and cfg["from"]),
        "message": "SMTP yapılandırılmamış — bildirim kuyrukta bekliyor." if notification.status == "pending" else "E-posta gönderildi.",
    }


@router.post("/send-bulk", response_model=dict)
def send_bulk_email(
    payload: BulkEmailRequest,
    db: Session = Depends(get_db),
    actor: User = Depends(require_roles("admin", "hr")),
):
    """Seçilen personellere toplu e-posta — önizleme öncesi 'N kişiye gidecek'."""
    from app.models.crew_member import CrewMember
    from app.services.audit import log_event

    crews = db.query(CrewMember).filter(CrewMember.id.in_(payload.crew_ids)).all()
    with_email = [c for c in crews if c.email]
    service = NotificationService(db, get_settings())
    sent = 0
    pending = 0
    for crew in with_email:
        notification = service.notify_email_to(
            title=payload.subject, message=payload.body,
            to_email=crew.email, entity_type="crew_member", entity_id=crew.id,
        )
        if notification.status == "sent":
            sent += 1
        else:
            pending += 1
    log_event(db, "bulk_email_sent", "crew_member", None,
              f"Bulk email to {len(with_email)} crew ({payload.subject})",
              user_email=actor.email)
    db.commit()
    cfg = service._email_config()
    return {
        "recipients": len(with_email),
        "skipped_no_email": len(crews) - len(with_email),
        "sent": sent,
        "pending": pending,
        "smtp_configured": bool(cfg["host"] and cfg["from"]),
    }


@router.post("/test-email", response_model=dict)
def send_test_email(
    db: Session = Depends(get_db),
    actor: User = Depends(require_roles("admin")),
):
    """SMTP yapılandırmasını dener — Ayarlar'daki 'Test E-postası Gönder' butonu."""
    service = NotificationService(db, get_settings())
    notification = service.notify(
        title="CREWINTEL Test E-postası",
        message="SMTP ayarları doğru yapılandırılmış. Bu bir test mesajıdır.",
        user_id=actor.id,
        channel="email",
    )
    db.commit()
    if notification.status == "failed":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="E-posta gönderilemedi. SMTP ayarlarını kontrol edin.")
    if notification.status == "pending":
        return {"status": "pending", "message": "SMTP yapılandırılmamış — bildirim kuyrukta bekliyor."}
    return {"status": "sent", "message": "Test e-postası gönderildi."}
