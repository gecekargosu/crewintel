"""Kişisel notlar — kullanıcıya özel, veritabanı destekli.

Notlar önceki sürümde yalnızca mobil uygulamanın belleğinde tutuluyordu.
Bu sürümde PostgreSQL'de saklanır ve her kullanıcı yalnızca kendi notlarını
görür/değiştirir.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.deps import require_staff_read
from app.db.database import get_db
from app.models.note import Note
from app.models.user import User
from app.services.audit import log_event

router = APIRouter(prefix="/api/notes", tags=["Notes"])

PRIORITIES = ("low", "normal", "high", "urgent")


class NoteCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    body: str = ""
    crew_member_id: int | None = None
    priority: str = "normal"


class NoteUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    body: str | None = None
    priority: str | None = None
    done: bool | None = None


def _serialize(note: Note) -> dict:
    return {
        "id": note.id,
        "title": note.title,
        "body": note.body or "",
        "crew_member_id": note.crew_member_id,
        "priority": note.priority or "normal",
        "done": note.done,
        "created_at": note.created_at.isoformat() if note.created_at else "",
        "updated_at": note.updated_at.isoformat() if note.updated_at else "",
        "user_email": note.user_email or "",
    }


def _validate_priority(priority: str) -> str:
    value = (priority or "normal").strip().lower()
    if value not in PRIORITIES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Geçersiz öncelik: {priority}. Seçenekler: {', '.join(PRIORITIES)}.",
        )
    return value


def _get_own_note(note_id: int, db: Session, current_user: User) -> Note:
    note = db.get(Note, note_id)
    if note is None or (note.user_id is not None and note.user_id != current_user.id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not bulunamadı.")
    return note


@router.get("/")
def list_notes(
    crew_member_id: int | None = Query(default=None),
    done: bool | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_staff_read),
):
    query = db.query(Note).filter(Note.user_id == current_user.id)
    if crew_member_id is not None:
        query = query.filter(Note.crew_member_id == crew_member_id)
    if done is not None:
        query = query.filter(Note.done == done)

    notes = query.order_by(Note.done.asc(), Note.id.desc()).all()
    return [_serialize(note) for note in notes]


@router.post("/", status_code=status.HTTP_201_CREATED)
def create_note(
    payload: NoteCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_staff_read),
):
    note = Note(
        title=payload.title.strip(),
        body=payload.body,
        priority=_validate_priority(payload.priority),
        crew_member_id=payload.crew_member_id,
        user_id=current_user.id,
        user_email=current_user.email,
    )
    db.add(note)
    db.flush()

    log_event(
        db,
        "note_created",
        "note",
        note.id,
        f"Note created: {note.title}",
        metadata={"crew_member_id": note.crew_member_id},
        user_email=current_user.email,
    )

    db.commit()
    db.refresh(note)
    return _serialize(note)


@router.put("/{note_id}")
def update_note(
    note_id: int,
    payload: NoteUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_staff_read),
):
    note = _get_own_note(note_id, db, current_user)

    if payload.title is not None:
        note.title = payload.title.strip()
    if payload.body is not None:
        note.body = payload.body
    if payload.priority is not None:
        note.priority = _validate_priority(payload.priority)
    if payload.done is not None:
        note.done = payload.done

    log_event(
        db,
        "note_updated",
        "note",
        note.id,
        f"Note updated: {note.title}",
        user_email=current_user.email,
    )

    db.commit()
    db.refresh(note)
    return _serialize(note)


@router.delete("/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_note(
    note_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_staff_read),
):
    note = _get_own_note(note_id, db, current_user)

    log_event(
        db,
        "note_deleted",
        "note",
        note.id,
        f"Note deleted: {note.title}",
        user_email=current_user.email,
    )

    db.delete(note)
    db.commit()
