import hashlib
import threading
import uuid
from datetime import date
from pathlib import Path

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.database import SessionLocal
from app.models.crew_member import CrewMember
from app.models.document import Document
from app.services.audit import log_event
from app.services.document_processing import (
    PDF_CONVERTIBLE_EXTENSIONS,
    convert_to_pdf,
    document_expiry_status,
    extract_metadata,
    extract_name,
    extract_text,
    serialize_metadata_for_json,
    store_file,
)
from app.services.match_engine import (
    AUTO_MATCH,
    DECISION_TO_STATUS,
    MatchEngine,
)


ALLOWED_UPLOAD_EXTENSIONS = set(PDF_CONVERTIBLE_EXTENSIONS)
MAX_UPLOAD_SIZE = 20 * 1024 * 1024  # 20 MB

# Uzantı bazlı zorunlu dosya imzaları (magic bytes)
_MAGIC_BY_SUFFIX: dict[str, tuple[bytes, ...]] = {
    ".pdf": (b"%PDF",),
    ".jpg": (b"\xff\xd8\xff",),
    ".jpeg": (b"\xff\xd8\xff",),
    ".jfif": (b"\xff\xd8\xff",),
    ".png": (b"\x89PNG\r\n\x1a\n",),
    ".bmp": (b"BM",),
    ".tif": (b"II*\x00", b"MM\x00*"),
    ".tiff": (b"II*\x00", b"MM\x00*"),
    ".docx": (b"PK\x03\x04",),
    ".xlsx": (b"PK\x03\x04",),
    ".xlsm": (b"PK\x03\x04",),
    ".odt": (b"PK\x03\x04",),
    ".ods": (b"PK\x03\x04",),
    ".doc": (b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1",),
    ".xls": (b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1",),
}


def validate_upload(filename: str, content: bytes) -> None:
    """Backend-side upload validation: extension allowlist + content sniffing.

    PDF, TXT, DOC/DOCX, XLSX, resim (JPEG/PNG/WebP/TIFF/BMP) ve OpenOffice
    formatları kabul edilir. API client'a güvenmez: uzantı ile içerik
    uyuşmuyorsa (ör. HTML'in .pdf'e çevrilmesi) reddeder.
    """
    suffix = Path(filename).suffix.lower()

    # 1) Dosya boyutu limiti (20MB)
    if len(content) > MAX_UPLOAD_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"{filename}: dosya çok büyük ({len(content) // 1024 // 1024}MB). Maksimum 20MB.",
        )

    # 2) Uzantı kontrolü
    if suffix not in ALLOWED_UPLOAD_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=(
                f"{filename}: desteklenmeyen dosya tipi. "
                "PDF, TXT, DOC/DOCX, XLS/XLSX, JPEG, PNG, WebP, TIFF, BMP kabul edilir."
            ),
        )

    # 3) Magic byte doğrulaması (uzantı ile içerik uyuşmalı)
    expected_signatures = _MAGIC_BY_SUFFIX.get(suffix)
    if expected_signatures and not any(content.startswith(sig) for sig in expected_signatures):
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"{filename}: dosya içeriği {suffix} formatıyla uyuşmuyor.",
        )

    # 4) TXT/CSV binary kontrolü
    if suffix in (".txt", ".csv") and b"\x00" in content:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"{filename}: dosya içeriği geçerli metin değil.",
        )

    # 5) WEBP ek kontrolü: RIFF....WEBP
    if suffix == ".webp" and not (content.startswith(b"RIFF") and content[8:12] == b"WEBP"):
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"{filename}: dosya içeriği WebP formatıyla uyuşmuyor.",
        )


def store_document_file(storage_path: str, original_filename: str, content: bytes) -> tuple[str, str, str]:
    """Belgeyi arşive kaydeder.

    PDF olmayan her dosya (doc/docx/xlsx/resim/txt) PDF'e çevrilip
    **PDF olarak saklanır**; kayıtlar arşiv tek format olur (madde:
    "pdf converter"). Checksum her zaman ORİJİNAL içerikten üretilir
    ki duplicate tespiti dosyanın kendisini yapsın.

    Returns:
        (storage_path, stored_filename, original_checksum)
    """
    original_checksum = hashlib.sha256(content).hexdigest()
    suffix = Path(original_filename).suffix.lower()

    stored_content = content
    store_name = original_filename

    if suffix != ".pdf":
        pdf_bytes, _error = convert_to_pdf(original_filename, content)
        if pdf_bytes:
            stored_content = pdf_bytes
            store_name = str(Path(original_filename).with_suffix(".pdf").name)

    path, stored_name, _stored_checksum = store_file(
        storage_path,
        store_name,
        stored_content,
    )
    return path, stored_name, original_checksum


# -- Asenkron batch isleme kayit defteri ------------------------------------
BATCH_LOCK = threading.Lock()
BATCH_REGISTRY: dict[str, dict] = {}


def _new_batch() -> dict:
    return {
        "batch_id": uuid.uuid4().hex[:12],
        "status": "queued",
        "total": 0,
        "processed": 0,
        "matched": 0,
        "review": 0,
        "conflict": 0,
        "unmatched": 0,
        "failed": 0,
        "duplicate": 0,
        "duplicate_files": [],
        "failed_details": [],
        "documents": [],
    }


def process_batch_document(document_id: int, batch_id: str) -> None:
    """Tek belgeyi ayri session'da isler ve batch registry'yi gunceller."""
    db = SessionLocal()
    try:
        document = db.get(Document, document_id)
        if document is None:
            with BATCH_LOCK:
                if batch_id in BATCH_REGISTRY:
                    BATCH_REGISTRY[batch_id]["failed"] += 1
            return

        try:
            path = Path(document.storage_path)
            content = path.read_bytes() if path.is_file() else b""
            text = extract_text(document.original_filename, content) or document.extracted_text or ""

            engine = MatchEngine(db, actor_email="system-batch")
            result = engine.process(document, text=text, dry_run=False)

            decision_status = DECISION_TO_STATUS.get(result.decision, "pending")
            outcome = {
                AUTO_MATCH: "matched",
                "REVIEW_REQUIRED": "review",
                "MATCH_CONFLICT": "conflict",
                "UNMATCHED": "unmatched",
            }.get(result.decision, "unmatched")

            log_event(
                db,
                "document_batch_processed",
                "document",
                document.id,
                f"Batch processed {document.original_filename} -> {result.decision}",
                metadata={
                    "batch_id": batch_id,
                    "decision": result.decision,
                    "score": result.best_candidate.score if result.best_candidate else 0,
                },
                user_email="system-batch",
            )

            db.commit()

            with BATCH_LOCK:
                if batch_id in BATCH_REGISTRY:
                    registry = BATCH_REGISTRY[batch_id]
                    registry["processed"] += 1
                    registry[outcome] += 1
                    registry["documents"].append({
                        "document_id": document.id,
                        "filename": document.original_filename,
                        "decision": result.decision,
                        "score": result.best_candidate.score if result.best_candidate else 0,
                        "crew_member_id": document.crew_member_id,
                        "match_status": decision_status,
                    })
        except Exception as error:
            db.rollback()
            with BATCH_LOCK:
                if batch_id in BATCH_REGISTRY:
                    BATCH_REGISTRY[batch_id]["processed"] += 1
                    BATCH_REGISTRY[batch_id]["failed"] += 1
                    BATCH_REGISTRY[batch_id]["documents"].append({
                        "document_id": document.id,
                        "filename": document.original_filename or "",
                        "decision": "FAILED",
                        "error": str(error)[:200],
                    })
    finally:
        db.close()
        with BATCH_LOCK:
            if batch_id in BATCH_REGISTRY:
                registry = BATCH_REGISTRY[batch_id]
                if registry["processed"] >= registry["total"]:
                    registry["status"] = "done"


class DocumentService:
    def __init__(self, db: Session, actor_email: str | None = None):
        self.db = db
        self.settings = get_settings()
        self.actor_email = actor_email

    def serialize(self, document: Document, duplicate: bool = False) -> dict:
        from app.schemas.document import DocumentResponse

        data = DocumentResponse.model_validate(document).model_dump()
        data["expiry_status"] = document_expiry_status(
            document.expiry_date,
            date.today(),
            self.settings.expiry_urgent_days,
            self.settings.expiry_approaching_days,
        )
        data["archived"] = document.archived_at is not None
        data["duplicate"] = duplicate
        return data

    async def upload_documents(self, files):
        saved = []
        stored_files: list[Path] = []

        try:
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

                validate_upload(original_filename, content)

                path, stored_name, checksum = store_document_file(
                    self.settings.storage_path,
                    original_filename,
                    content,
                )
                stored_files.append(Path(path))

                existing = (
                    self.db.query(Document)
                    .filter(Document.checksum == checksum)
                    .first()
                )

                if existing:
                    Path(path).unlink(missing_ok=True)

                    log_event(
                        self.db,
                        "document_duplicate_upload",
                        "document",
                        existing.id,
                        f"Duplicate upload detected for {existing.original_filename}",
                        metadata={
                            "original_filename": original_filename,
                            "checksum": checksum,
                        },
                        user_email=self.actor_email,
                    )

                    saved.append((existing, True))
                    continue

                text = extract_text(original_filename, content)
                metadata = extract_metadata(original_filename, text)

                # Metin çıkarılamadıysa metadata'ya not ekle
                if text.startswith("[") and text.endswith("]"):
                    metadata["extraction_error"] = text

                document = Document(
                    crew_member_id=None,
                    original_filename=original_filename,
                    stored_filename=stored_name,
                    storage_path=path,
                    mime_type="application/pdf" if stored_name.lower().endswith(".pdf") else upload.content_type,
                    file_size=len(content),
                    checksum=checksum,
                    document_type=metadata["document_type"],
                    issue_date=metadata["issue_date"],
                    expiry_date=metadata["expiry_date"],
                    match_status="processing",
                    match_confidence=0,
                    extracted_text=text or None,
                    extracted_metadata=serialize_metadata_for_json(metadata),
                )

                self.db.add(document)
                self.db.flush()

                engine = MatchEngine(self.db, actor_email=self.actor_email)
                result = engine.process(document, text=text, dry_run=False)
                match_status = document.match_status
                confidence = document.match_confidence

                if (
                    document.crew_member_id is None
                    and result.decision == "UNMATCHED"
                ):
                    first_name, last_name = extract_name(
                        original_filename,
                        text,
                    )

                    if first_name and last_name and document.document_type == "cv":
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

                        document.crew_member_id = crew.id
                        document.match_status = "matched"
                        document.match_confidence = 90
                        match_status = "matched"
                        confidence = 90

                        log_event(
                            self.db,
                            "crew_created_from_cv",
                            "crew_member",
                            crew.id,
                            "Crew member created from CV",
                            metadata={"document": original_filename},
                            user_email=self.actor_email,
                        )

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
                    user_email=self.actor_email,
                )

                saved.append((document, False))

            self.db.commit()

            for document, _duplicate in saved:
                self.db.refresh(document)

            return saved
        except Exception:
            for path in stored_files:
                path.unlink(missing_ok=True)
            raise

    async def stage_batch_upload(self, files) -> tuple[dict, list[Document]]:
        """Batch upload: dosyalari kaydeder, Document satirlarini `processing`
        durumunda olusturur ve (batch_id, documents) doner. Eslestirme daha
        sonra arka planda process_batch_document ile yapilir.

        Gecersiz dosyalar (desteklenmeyen format, bos dosya, boyut asimi)
        batch'i durdurmaz; "failed" olarak sayilir ve gecerli dosyalar
        normal islenir.
        """
        batch = _new_batch()
        documents: list[Document] = []
        stored_files: list[Path] = []

        try:
            for upload in files:
                content = await upload.read()

                # Gecersiz dosyalari batch'i durdurmadan atla.
                if not content:
                    batch["failed"] += 1
                    batch.setdefault("failed_details", []).append(
                        {"filename": upload.filename or "unknown", "reason": "empty file"}
                    )
                    continue

                if len(content) > self.settings.max_upload_size_mb * 1024 * 1024:
                    batch["failed"] += 1
                    batch.setdefault("failed_details", []).append(
                        {"filename": upload.filename or "unknown", "reason": "file too large"}
                    )
                    continue

                original_filename = upload.filename or "document"

                # validate_upload 415 firlatirsa dosyayi atla.
                try:
                    validate_upload(original_filename, content)
                except HTTPException:
                    batch["failed"] += 1
                    batch.setdefault("failed_details", []).append(
                        {"filename": original_filename, "reason": "unsupported file type or content mismatch"}
                    )
                    continue

                path, stored_name, checksum = store_document_file(
                    self.settings.storage_path,
                    original_filename,
                    content,
                )
                stored_files.append(Path(path))

                # Duplicate: DB'de ayni checksum varsa dosyayi saklama.
                existing = (
                    self.db.query(Document)
                    .filter(Document.checksum == checksum)
                    .first()
                )

                if existing:
                    Path(path).unlink(missing_ok=True)
                    log_event(
                        self.db,
                        "document_duplicate_upload",
                        "document",
                        existing.id,
                        f"Duplicate upload detected for {existing.original_filename}",
                        metadata={
                            "original_filename": original_filename,
                            "checksum": checksum,
                        },
                        user_email=self.actor_email,
                    )
                    batch["duplicate"] += 1
                    batch.setdefault("duplicate_files", []).append(original_filename)
                    continue

                text = extract_text(original_filename, content)
                metadata = extract_metadata(original_filename, text)

                # Metin çıkarılamadıysa metadata'ya not ekle
                if text.startswith("[") and text.endswith("]"):
                    metadata["extraction_error"] = text

                document = Document(
                    crew_member_id=None,
                    original_filename=original_filename,
                    stored_filename=stored_name,
                    storage_path=path,
                    mime_type="application/pdf" if stored_name.lower().endswith(".pdf") else upload.content_type,
                    file_size=len(content),
                    checksum=checksum,
                    document_type=metadata["document_type"],
                    issue_date=metadata["issue_date"],
                    expiry_date=metadata["expiry_date"],
                    match_status="processing",
                    match_confidence=0,
                    extracted_text=text or None,
                    extracted_metadata=serialize_metadata_for_json(metadata),
                )

                self.db.add(document)
                self.db.flush()
                documents.append(document)

            self.db.commit()

            batch["total"] = len(documents)
            with BATCH_LOCK:
                BATCH_REGISTRY[batch["batch_id"]] = batch

            return batch, documents
        except Exception:
            for path in stored_files:
                path.unlink(missing_ok=True)
            self.db.rollback()
            raise
        finally:
            # Batch'te hic gecerli dosya yoksa bile registry'ye kaydet.
            if batch["batch_id"] not in BATCH_REGISTRY:
                batch["total"] = batch.get("total", 0)
                with BATCH_LOCK:
                    BATCH_REGISTRY[batch["batch_id"]] = batch

    def list_documents(
        self,
        crew_member_id: int | None = None,
        document_type: str | None = None,
        match_status: str | None = None,
        expiry_status: str | None = None,
        offset: int = 0,
        limit: int | None = None,
    ) -> tuple[int, list[Document]]:
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
            documents = [
                document
                for document in documents
                if self.serialize(document)["expiry_status"] == expiry_status
            ]

        total = len(documents)

        if limit is not None:
            documents = documents[offset:offset + limit]

        return total, documents

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

        engine = MatchEngine(self.db, actor_email=self.actor_email)
        engine.manual_override(document, crew_member_id)

        log_event(
            self.db,
            "document_manually_matched",
            "document",
            document.id,
            "Document manually linked to crew member",
            metadata={"crew_member_id": crew_member_id},
            user_email=self.actor_email,
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
            user_email=self.actor_email,
        )

        self.db.delete(document)
        self.db.commit()
