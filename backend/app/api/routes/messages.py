"""Mesajlaşma (M1 Mobile) — admin/hr ↔ crew.

- Konuşma başlatma: yalnızca admin/hr (personel kendi tarafına mesaj yazar).
- Katılımcı dışı erişim 403 (IDOR korumalı).
- REST tabanlı; WebSocket M2+ (karar #10).
"""

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_roles
from app.db.database import get_db
from app.models.message import Conversation, Message
from app.models.user import User
from app.services.audit import log_event
from app.services.push import send_push

router = APIRouter(prefix="/api/messages", tags=["Messages"])

VALID_KINDS = {"chat", "system", "job_alert", "document_alert", "contract_alert"}


def _get_conversation_or_403(conversation_id: int, user: User, db: Session) -> Conversation:
    conversation = db.get(Conversation, conversation_id)
    if conversation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Konuşma bulunamadı.")
    if user.id not in (conversation.participant_a, conversation.participant_b):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Bu konuşmaya erişim yetkiniz yok.")
    return conversation


def _conversation_dict(conversation: Conversation, current_user: User, db: Session) -> dict:
    other_id = (
        conversation.participant_b
        if conversation.participant_a == current_user.id
        else conversation.participant_a
    )
    other = db.get(User, other_id)
    unread = (
        db.query(Message)
        .filter(
            Message.conversation_id == conversation.id,
            Message.sender_user_id != current_user.id,
            Message.read_at.is_(None),
        )
        .count()
    )
    last = (
        db.query(Message)
        .filter(Message.conversation_id == conversation.id)
        .order_by(Message.id.desc())
        .first()
    )
    return {
        "id": conversation.id,
        "other_user": {
            "id": other.id if other else None,
            "full_name": other.full_name if other else "—",
            "role": other.role if other else None,
        },
        "subject": conversation.subject,
        "unread_count": unread,
        "last_message": last.body if last else None,
        "last_message_at": (
            last.created_at.isoformat() if last and last.created_at else None
        ),
        "created_at": conversation.created_at.isoformat() if conversation.created_at else None,
    }


def _message_dict(message: Message) -> dict:
    return {
        "id": message.id,
        "conversation_id": message.conversation_id,
        "sender_user_id": message.sender_user_id,
        "kind": message.kind,
        "body": message.body,
        "attachment_path": message.attachment_path,
        "read": message.read_at is not None,
        "created_at": message.created_at.isoformat() if message.created_at else None,
    }


@router.get("/conversations")
def list_conversations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    conversations = (
        db.query(Conversation)
        .filter(or_(
            Conversation.participant_a == current_user.id,
            Conversation.participant_b == current_user.id,
        ))
        .order_by(Conversation.last_message_at.desc().nullslast(), Conversation.id.desc())
        .all()
    )
    return [_conversation_dict(c, current_user, db) for c in conversations]


@router.post("/conversations", status_code=status.HTTP_201_CREATED)
def create_conversation(
    payload: dict,
    db: Session = Depends(get_db),
    actor: User = Depends(require_roles("admin", "hr")),
):
    """Personel (crew) kullanıcısıyla konuşma başlat."""
    crew_user_id = payload.get("crew_user_id")
    if not crew_user_id:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                            detail="crew_user_id gereklidir.")
    crew_user = db.get(User, crew_user_id)
    if crew_user is None or crew_user.role != "crew":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Geçerli bir personel hesabı seçin.")
    if crew_user.id == actor.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Kendinizle konuşma başlatamazsınız.")

    existing = (
        db.query(Conversation)
        .filter(or_(
            (Conversation.participant_a == actor.id) & (Conversation.participant_b == crew_user.id),
            (Conversation.participant_a == crew_user.id) & (Conversation.participant_b == actor.id),
        ))
        .first()
    )
    if existing:
        return _conversation_dict(existing, actor, db)

    conversation = Conversation(
        participant_a=actor.id,
        participant_b=crew_user.id,
        subject=(payload.get("subject") or "").strip()[:200] or None,
        last_message_at=datetime.now(UTC).replace(tzinfo=None),
    )
    db.add(conversation)
    db.flush()
    log_event(db, "conversation_created", "conversation", conversation.id,
              f"Konuşma başlatıldı: {actor.email} ↔ {crew_user.email}",
              user_email=actor.email)
    db.commit()
    db.refresh(conversation)
    return _conversation_dict(conversation, actor, db)


@router.get("/conversations/{conversation_id}")
def get_conversation(
    conversation_id: int,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    conversation = _get_conversation_or_403(conversation_id, current_user, db)
    messages = (
        db.query(Message)
        .filter(Message.conversation_id == conversation_id)
        .order_by(Message.id.desc())
        .limit(min(limit, 200))
        .all()
    )
    messages = list(reversed(messages))

    # Gelen mesajları okundu işaretle
    now = datetime.now(UTC).replace(tzinfo=None)
    for message in messages:
        if message.sender_user_id != current_user.id and message.read_at is None:
            message.read_at = now
    db.commit()

    return {
        "conversation": _conversation_dict(conversation, current_user, db),
        "messages": [_message_dict(m) for m in messages],
    }


@router.post("/conversations/{conversation_id}", status_code=status.HTTP_201_CREATED)
def send_message(
    conversation_id: int,
    payload: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    conversation = _get_conversation_or_403(conversation_id, current_user, db)
    body = (payload.get("body") or "").strip()
    kind = (payload.get("kind") or "chat").strip().lower()
    if kind not in VALID_KINDS:
        kind = "chat"
    if not body and not payload.get("attachment_path"):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                            detail="Mesaj boş olamaz.")

    now = datetime.now(UTC).replace(tzinfo=None)
    message = Message(
        conversation_id=conversation_id,
        sender_user_id=current_user.id,
        kind=kind,
        body=body or None,
        attachment_path=(payload.get("attachment_path") or "").strip() or None,
    )
    db.add(message)
    conversation.last_message_at = now
    log_event(db, "message_sent", "message", message.id,
              f"Mesaj: {current_user.email} → konuşma #{conversation_id}",
              user_email=current_user.email)
    db.commit()
    db.refresh(message)

    # Alıcıya push bildirimi (hata olursa mesaj akışını bozma)
    recipient_id = (
        conversation.participant_b
        if conversation.participant_a == current_user.id
        else conversation.participant_a
    )
    send_push(
        db,
        recipient_id,
        "Yeni mesaj",
        f"{current_user.full_name}: {body[:120] or 'Dosya gönderildi'}",
        data={"type": "message", "conversation_id": conversation_id},
    )
    return _message_dict(message)


@router.patch("/{message_id}/read")
def mark_read(
    message_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    message = db.get(Message, message_id)
    if message is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mesaj bulunamadı.")
    conversation = _get_conversation_or_403(message.conversation_id, current_user, db)
    if message.sender_user_id == current_user.id:
        return {"id": message.id, "read": True}
    message.read_at = datetime.now(UTC).replace(tzinfo=None)
    db.commit()
    return {"id": message.id, "read": True}
