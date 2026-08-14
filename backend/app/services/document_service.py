from datetime import date
from pathlib import Path

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.crew_member import CrewMember
from app.models.document import Document
from app.services.audit import log_event
from app.services.document_processing import (
    document_expiry_status,
    extract_metadata,
    extract_name,
    extract_text,
    match_crew,
    serialize_metadata_for_json,
    store_file,
)


class DocumentService:
    def __init__(self, db: Session):
        self.db = db
        self.settings = get_settings()

    def serialize(self, document: Document) -> dict:
        from app.schemas.document import DocumentResponse

        data = DocumentResponse.model_validate(document).model_dump()
        data["expiry_status"] = document_expiry_status(
            document.expiry_date,
            date.today(),
            self.settings.expiry_urgent_days,
            self.settings.expiry_approaching_days,
        )
        return data

    async def upload_documents(self, files):
        saved = []

        for upload in files:
            content = await upload.read()

            if not content:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"{upload.filename}: empty file.",
                )

            if len(content) > self.settings.max_upload_size_mb * 1024 * 1024:
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail=f"{upload.filename}: file is too large.",
                )

            original_filename = upload.filename or "document"

            path, stored_name, checksum = store_file(
                self.settings.storage_path,
                original_filename,
                content,
            )

            existing = (
                self.db.query(Document)
                .filter(Document.checksum == checksum)
                .first()
            )

            if existing:
                Path(path).unlink(missing_ok=True)
                saved.append(existing)
                continue

            text = extract_text(original_filename, content)
            metadata = extract_metadata(original_filename, text)

            crew, match_status, confidence = match_crew(
                self.db,
                original_filename,
                text,
                metadata,
            )

            if (
                crew is None
                and match_status == "unmatched"
                and metadata["document_type"] == "cv"
            ):
                first_name, last_name = extract_name(
                    original_filename,
                    text,
                )

                if first_name and last_name:
                    crew = CrewMember(
                        first_name=first_name,
                        last_name=last_name,
                        position="Unspecified",
                        nationality=None,
                        email=metadata.get("email"),
                        passport_number=metadata.get("passport_number"),
                        seaman_book_number=metadata.get("seaman_book_number"),
                        profile_data={
                            "source": "cv_upload",
                            "extracted": serialize_metadata_for_json(metadata),
                        },
                    )

                    self.db.add(crew)
                    self.db.flush()

                    match_status = "matched"
                    confidence = 90

                    log_event(
                        self.db,
                        "crew_created_from_cv",
                        "crew_member",
                        crew.id,
                        "Crew member created from CV",
                        metadata={"document": original_filename},
                    )

            document = Document(
                crew_member_id=crew.id if crew else None,
                original_filename=original_filename,
                stored_filename=stored_name,
                storage_path=path,
                mime_type=upload.content_type,
                file_size=len(content),
                checksum=checksum,
                document_type=metadata["document_type"],
                issue_date=metadata["issue_date"],
                expiry_date=metadata["expiry_date"],
                match_status=match_status,
                match_confidence=confidence,
                extracted_text=text or None,
                extracted_metadata=serialize_metadata_for_json(metadata),
            )

            self.db.add(document)
            self.db.flush()

            log_event(
                self.db,
                "document_uploaded",
                "document",
                document.id,
                f"Uploaded {document.original_filename}",
                metadata={
                    "match_status": match_status,
                    "confidence": confidence,
                },
            )

            saved.append(document)

        self.db.commit()

        for document in saved:
            self.db.refresh(document)

        return saved

    def list_documents(
        self,
        crew_member_id: int | None = None,
        document_type: str | None = None,
        match_status: str | None = None,
        expiry_status: str | None = None,
    ):
        query = self.db.query(Document)

        if crew_member_id:
            query = query.filter(
                Document.crew_member_id == crew_member_id
            )

        if document_type:
            query = query.filter(
                Document.document_type == document_type
            )

        if match_status:
            query = query.filter(
                Document.match_status == match_status.strip()
            )

        documents = (
            query
            .order_by(Document.created_at.desc())
            .all()
        )

        if expiry_status:
            return [
                document
                for document in documents
                if self.serialize(document)["expiry_status"] == expiry_status
            ]

        return documents

    def get_document(self, document_id: int) -> Document:
        document = self.db.get(Document, document_id)

        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found.",
            )

        return document

    def get_document_file(self, document_id: int) -> Document:
        document = self.get_document(document_id)

        if not Path(document.storage_path).is_file():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document file not found.",
            )

        return document

    def match_document(
        self,
        document_id: int,
        crew_member_id: int,
    ) -> Document:
        document = self.get_document(document_id)

        crew_member = self.db.get(CrewMember, crew_member_id)

        if crew_member is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Crew member not found.",
            )

        document.crew_member_id = crew_member_id
        document.match_status = "matched"
        document.match_confidence = 100

        log_event(
            self.db,
            "document_manually_matched",
            "document",
            document.id,
            "Document manually linked to crew member",
            metadata={"crew_member_id": crew_member_id},
        )

        self.db.commit()
        self.db.refresh(document)

        return document

    def delete_document(self, document_id: int) -> None:
        document = self.get_document(document_id)

        Path(document.storage_path).unlink(missing_ok=True)

        log_event(
            self.db,
            "document_deleted",
            "document",
            document.id,
            "Document deleted",
        )

        self.db.delete(document)
        self.db.commit()

