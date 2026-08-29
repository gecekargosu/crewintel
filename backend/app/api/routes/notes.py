"""Kişisel notlar — admin/hr crew notları."""


from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_roles
from app.db.database import get_db
from app.models.user import User


router = APIRouter(prefix="/api/notes", tags=["Notes"])

# In-memory store (persistent in production — DB table needed)
_notes: list[dict] = []
_note_id_counter = 0


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


def _serialize(note: dict) -> dict:
    return {
        "id": note["id"],
        "title": note["title"],
        "body": note.get("body", ""),
        "crew_member_id": note.get("crew_member_id"),
        "priority": note.get("priority", "normal"),
        "done": note.get("done", False),
        "created_at": note.get("created_at", ""),
        "user_email": note.get("user_email", ""),
    }


@router.get("/", response_model=list[dict])
def list_notes(
    crew_member_id: int | None = None,
    done: bool | None = None,
    current_user: User = Depends(get_current_user),
):
    results = _notes
    if crew_member_id is not None:
        results = [n for n in results if n.get("crew_member_id") == crew_member_id]
    if done is not None:
        results = [n for n in results if n.get("done", False) == done]
    return [_serialize(n) for n in sorted(results, key=lambda x: x["id"], reverse=True)]


@router.post("/", status_code=status.HTTP_201_CREATED)
def create_note(
    payload: NoteCreate,
    current_user: User = Depends(get_current_user),
):
    global _note_id_counter
    _note_id_counter += 1
    from datetime import datetime
    note = {
        "id": _note_id_counter,
        "title": payload.title,
        "body": payload.body,
        "crew_member_id": payload.crew_member_id,
        "priority": payload.priority,
        "done": False,
        "created_at": datetime.now().isoformat(),
        "user_email": current_user.email,
    }
    _notes.append(note)
    return _serialize(note)


@router.put("/{note_id}")
def update_note(
    note_id: int,
    payload: NoteUpdate,
    current_user: User = Depends(get_current_user),
):
    for note in _notes:
        if note["id"] == note_id:
            if payload.title is not None:
                note["title"] = payload.title
            if payload.body is not None:
                note["body"] = payload.body
            if payload.priority is not None:
                note["priority"] = payload.priority
            if payload.done is not None:
                note["done"] = payload.done
            return _serialize(note)
    raise HTTPException(status_code=404, detail="Not bulunamadı.")


@router.delete("/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_note(
    note_id: int,
    current_user: User = Depends(get_current_user),
):
    global _notes
    _notes = [n for n in _notes if n["id"] != note_id]
