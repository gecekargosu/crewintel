from fastapi import APIRouter, Depends, File, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.document import DocumentMatchUpdate, DocumentResponse
from app.services.document_service import DocumentService


router = APIRouter(prefix="/api/documents", tags=["Documents"])


@router.post(
    "/upload",
    response_model=list[DocumentResponse],
    status_code=status.HTTP_201_CREATED,
)
async def upload_documents(
    files: list[UploadFile] = File(...),
    db: Session = Depends(get_db),
):
    service = DocumentService(db)
    documents = await service.upload_documents(files)

    return [
        service.serialize(document)
        for document in documents
    ]


@router.get(
    "/",
    response_model=list[DocumentResponse],
)
def list_documents(
    crew_member_id: int | None = None,
    document_type: str | None = None,
    match_status: str | None = None,
    expiry_status: str | None = None,
    db: Session = Depends(get_db),
):
    service = DocumentService(db)

    documents = service.list_documents(
        crew_member_id=crew_member_id,
        document_type=document_type,
        match_status=match_status,
        expiry_status=expiry_status,
    )

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
):
    service = DocumentService(db)
    document = service.get_document(document_id)

    return service.serialize(document)


@router.get("/{document_id}/file")
def download_document(
    document_id: int,
    db: Session = Depends(get_db),
):
    service = DocumentService(db)
    document = service.get_document_file(document_id)

    return FileResponse(
        document.storage_path,
        media_type=document.mime_type,
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
):
    service = DocumentService(db)

    document = service.match_document(
        document_id=document_id,
        crew_member_id=payload.crew_member_id,
    )

    return service.serialize(document)


@router.delete(
    "/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_document(
    document_id: int,
    db: Session = Depends(get_db),
):
    service = DocumentService(db)
    service.delete_document(document_id)

