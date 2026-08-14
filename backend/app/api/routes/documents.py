from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, Query, Response, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_staff_read, require_roles
from app.db.database import get_db
from app.models.document import Document
from app.models.document_match import DocumentMatch
from app.services.audit import log_event
from app.schemas.document import DocumentMatchUpdate, DocumentResponse
from app.services.document_service import (
    BATCH_REGISTRY,
    DocumentService,
    process_batch_document,
)
from app.services.match_engine import MatchEngine


router = APIRouter(prefix="/api/documents", tags=["Documents"])


SAFE_MEDIA_TYPES = {
    ".pdf": "application/pdf",
    ".txt": "text/plain; charset=utf-8",
}


@router.post(
    "/batch",
    status_code=status.HTTP_202_ACCEPTED,
)
async def upload_batch(
    background_tasks: BackgroundTasks,
    files: list[UploadFile] = File(...),
    db: Session = Depends(get_db),
    actor: Session = Depends(require_roles("admin", "hr")),
):
    """Bulk upload: dosyaları kabul eder, `processing` durumunda kaydeder ve
    arka planda match engine çalıştırır. Anında batch_id + özet döner.
    """
    service = DocumentService(db, actor_email=actor.email)
    batch, documents = await service.stage_batch_upload(files)

    for document in documents:
        background_tasks.add_task(
            process_batch_document,
            document.id,
            batch["batch_id"],
        )

    resp = {
        "batch_id": batch["batch_id"],
        "status": batch["status"],
        "total": batch["total"],
        "duplicate": batch["duplicate"],
        "failed": batch.get("failed", 0),
        "message": f"{batch['total']} belge kuyruğa alındı.",
    }
    if batch.get("failed_details"):
        resp["failed_details"] = batch["failed_details"]
    return resp


@router.get(
    "/batch/{batch_id}",
)
def get_batch_status(
    batch_id: str,
    db: Session = Depends(get_db),
    current_user: Session = Depends(require_staff_read),
):
    """Batch işleme ilerlemesi + sonuç özeti."""
    batch = BATCH_REGISTRY.get(batch_id)
    if batch is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Batch not found.",
        )
    return batch


@router.get(
    "/review",
    response_model=list[DocumentResponse],
)
def list_review_queue(
    response: Response,
    limit: int = Query(default=100, ge=1, le=5000),
    db: Session = Depends(get_db),
    current_user: Session = Depends(require_staff_read),
):
    """İnceleme kuyruğu: review_required + conflict + pending_approval."""
    service = DocumentService(db)
    total, documents = service.list_documents(
        offset=0,
        limit=limit,
    )
    queue = [
        doc
        for doc in documents
        if doc.match_status in ("review_required", "conflict", "pending_approval")
    ]
    response.headers["X-Total-Count"] = str(len(queue))
    return [service.serialize(doc) for doc in queue]


@router.get(
    "/{document_id}/candidates",
)
def get_match_candidates(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: Session = Depends(require_staff_read),
):
    """Bir belge için aday personel listesi + skorlar (DB'ye yazmaz)."""
    service = DocumentService(db)
    document = service.get_document(document_id)

    engine = MatchEngine(db, actor_email=current_user.email)
    result = engine.process(
        document,
        text=document.extracted_text or "",
        dry_run=True,
    )

    return {
        "document_id": document.id,
        "filename": document.original_filename,
        "document_type": document.document_type,
        "decision": result.decision,
        "reason": result.reason,
        "candidates": [
            {
                "crew_id": candidate.crew_id,
                "first_name": candidate.first_name,
                "last_name": candidate.last_name,
                "score": candidate.score,
                "signals": candidate.signals,
            }
            for candidate in result.candidates
        ],
        "extracted_metadata": document.extracted_metadata,
    }


@router.get(
    "/{document_id}/matches",
)
def get_match_history(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: Session = Depends(require_staff_read),
):
    """Belge için tüm match kararı geçmişi."""
    rows = (
        db.query(DocumentMatch)
        .filter(DocumentMatch.document_id == document_id)
        .order_by(DocumentMatch.created_at.desc())
        .limit(20)
        .all()
    )
    return [
        {
            "id": row.id,
            "candidate_crew_id": row.candidate_crew_id,
            "final_crew_id": row.final_crew_id,
            "score": row.score,
            "decision": row.decision,
            "signals": row.signals,
            "candidates": row.candidates,
            "actor_email": row.actor_email,
            "created_at": row.created_at.isoformat() if row.created_at else None,
        }
        for row in rows
    ]


@router.post(
    "/upload",
    response_model=list[DocumentResponse],
    status_code=status.HTTP_201_CREATED,
)
async def upload_documents(
    files: list[UploadFile] = File(...),
    db: Session = Depends(get_db),
    actor: Session = Depends(require_roles("admin", "hr")),
):
    service = DocumentService(db, actor_email=actor.email)
    documents = await service.upload_documents(files)

    return [
        service.serialize(document, duplicate=duplicate)
        for document, duplicate in documents
    ]


@router.get(
    "/",
    response_model=list[DocumentResponse],
)
def list_documents(
    response: Response,
    crew_member_id: int | None = None,
    document_type: str | None = None,
    match_status: str | None = None,
    expiry_status: str | None = None,
    offset: int = Query(default=0, ge=0),
    limit: int | None = Query(default=None, ge=1, le=5000),
    db: Session = Depends(get_db),
    current_user: Session = Depends(require_staff_read),
):
    service = DocumentService(db)

    total, documents = service.list_documents(
        crew_member_id=crew_member_id,
        document_type=document_type,
        match_status=match_status,
        expiry_status=expiry_status,
        offset=offset,
        limit=limit,
    )
    response.headers["X-Total-Count"] = str(total)

    return [
        service.serialize(document)
        for document in documents
    ]


@router.get(
    "/{document_id}",
    response_model=DocumentResponse,
)
def get_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: Session = Depends(require_staff_read),
):
    service = DocumentService(db)
    document = service.get_document(document_id)

    return service.serialize(document)


@router.get("/{document_id}/file")
def download_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: Session = Depends(require_staff_read),
):
    service = DocumentService(db)
    document = service.get_document_file(document_id)

    # Derive the media type from the stored file extension instead of trusting
    # the client-supplied mime_type: prevents stored content-type confusion
    # (e.g. a malicious upload being served as text/html).
    suffix = Path(document.storage_path).suffix.lower()
    media_type = SAFE_MEDIA_TYPES.get(suffix, "application/octet-stream")

    return FileResponse(
        document.storage_path,
        media_type=media_type,
        filename=document.original_filename,
    )


@router.put(
    "/{document_id}/match",
    response_model=DocumentResponse,
)
def match_document(
    document_id: int,
    payload: DocumentMatchUpdate,
    db: Session = Depends(get_db),
    actor: Session = Depends(require_roles("admin", "hr")),
):
    service = DocumentService(db, actor_email=actor.email)

    document = service.match_document(
        document_id=document_id,
        crew_member_id=payload.crew_member_id,
    )

    return service.serialize(document)


@router.post(
    "/{document_id}/approve",
    response_model=DocumentResponse,
)
def approve_document(
    document_id: int,
    db: Session = Depends(get_db),
    actor: Session = Depends(require_roles("admin", "hr")),
):
    """Personel tarafından yüklenen / inceleme bekleyen belgeyi onaylar.
    Aynı tipteki eski (geçersiz) belgeyi arşive alır — versiyonlama."""
    from datetime import UTC, datetime

    service = DocumentService(db, actor_email=actor.email)
    document = service.get_document(document_id)
    if document.crew_member_id is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Belge önce bir personele bağlanmalı.")

    # Aynı tipteki eski belgeleri arşivle (sadece farklı dosya ise)
    old_docs = (
        db.query(Document)
        .filter(
            Document.crew_member_id == document.crew_member_id,
            Document.document_type == document.document_type,
            Document.id != document.id,
            Document.archived_at.is_(None),
        )
        .all()
    )
    for old in old_docs:
        old.archived_at = datetime.now(UTC).replace(tzinfo=None)

    document.match_status = "matched"
    document.match_confidence = 100
    document.archived_at = None
    log_event(db, "document_approved", "document", document.id,
              f"Document approved: {document.original_filename} → crew {document.crew_member_id} (eski {len(old_docs)} arşivlendi)",
              user_email=actor.email)
    db.commit()
    db.refresh(document)
    return service.serialize(document)


@router.post(
    "/{document_id}/reject",
    response_model=DocumentResponse,
)
def reject_document(
    document_id: int,
    db: Session = Depends(get_db),
    actor: Session = Depends(require_roles("admin", "hr")),
):
    """İnceleme bekleyen belgeyi reddeder — unmatched durumuna düşürür."""
    service = DocumentService(db, actor_email=actor.email)
    document = service.get_document(document_id)
    document.match_status = "unmatched"
    document.match_confidence = 0
    document.crew_member_id = None
    log_event(db, "document_rejected", "document", document.id,
              f"Document rejected: {document.original_filename}",
              user_email=actor.email)
    db.commit()
    db.refresh(document)
    return service.serialize(document)


@router.delete(
    "/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_document(
    document_id: int,
    db: Session = Depends(get_db),
    actor: Session = Depends(require_roles("admin", "hr")),
):
    service = DocumentService(db, actor_email=actor.email)
    service.delete_document(document_id)

