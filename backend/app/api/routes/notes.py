"""Kişisel notlar — PostgreSQL-backed storage."""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.database import get_db
from app.models.note import Note
from app.models.user import User

router = APIRouter(prefix="/api/notes", tags=["Notes"])


class NoteCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    body: str = ""
    crew_member_id: int | None = None
    priority: str = "normal"  # low, normal, high, urgent


class NoteUpdate(BaseModel):
    title: str | None = None
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
        "user_email": note.user_email or "",
    }


@router.get("/", response_model=list[dict])
def list_notes(
    crew_member_id: int | None = None,
    done: bool | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = db.query(Note)
    if crew_member_id is not None:
        q = q.filter(Note.crew_member_id == crew_member_id)
    if done is not None:
        q = q.filter(Note.done == done)
    notes = q.order_by(Note.id.desc()).all()
    return [_serialize(n) for n in notes]


@router.post("/", response_model=dict, status_code=status.HTTP_201_CREATED)
def create_note(
    body: NoteCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    note = Note(
        title=body.title,
        body=body.body,
        priority=body.priority,
        crew_member_id=body.crew_member_id,
        user_email=current_user.email,
    )
    db.add(note)
    db.commit()
    db.refresh(note)
    return _serialize(note)


@router.put("/{note_id}", response_model=dict)
def update_note(
    note_id: int,
    body: NoteUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    note = db.query(Note).filter(Note.id == note_id).first()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    if body.title is not None:
        note.title = body.title
    if body.body is not None:
        note.body = body.body
    if body.priority is not None:
        note.priority = body.priority
    if body.done is not None:
        note.done = body.done
    db.commit()
    db.refresh(note)
    return _serialize(note)


@router.delete("/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_note(
    note_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    note = db.query(Note).filter(Note.id == note_id).first()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    db.delete(note)
    db.commit()
