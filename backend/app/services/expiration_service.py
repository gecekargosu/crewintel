from datetime import date

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.document import Document
from app.services.document_processing import document_expiry_status


class ExpirationService:

    def __init__(self, db: Session):
        self.db = db
        self.settings = get_settings()

    def get_status(self, document: Document) -> str:
        return document_expiry_status(
            document.expiry_date,
            date.today(),
            self.settings.expiry_urgent_days,
            self.settings.expiry_approaching_days,
        )

    def serialize(self, document: Document) -> dict:
        from app.schemas.document import DocumentResponse

        data = DocumentResponse.model_validate(document).model_dump()
        data["expiry_status"] = self.get_status(document)
        return data

    def _get_documents(self) -> list[Document]:
        return (
            self.db.query(Document)
            .order_by(Document.expiry_date.asc().nullslast(), Document.id.asc())
            .all()
        )

    def _get_by_status(self, status: str) -> list[Document]:
        documents = self._get_documents()
        return [
            document
            for document in documents
            if self.get_status(document) == status
        ]

    def get_expired_documents(self) -> list[Document]:
        return self._get_by_status("expired")

    def get_urgent_documents(self) -> list[Document]:
        return self._get_by_status("urgent")

    def get_approaching_documents(self) -> list[Document]:
        return self._get_by_status("approaching")

    def get_valid_documents(self) -> list[Document]:
        return self._get_by_status("valid")

    def get_documents_without_expiry(self) -> list[Document]:
        return self._get_by_status("no_date")

    def get_summary(self) -> dict:
        documents = self._get_documents()

        summary = {
            "total": len(documents),
            "expired": 0,
            "urgent": 0,
            "approaching": 0,
            "valid": 0,
            "no_date": 0,
        }

        for document in documents:
            status = self.get_status(document)

            if status in summary:
                summary[status] += 1

        return summary
