from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_staff_read
from app.db.database import get_db
from app.models.user import User
from app.models.document import Document
from app.services.expiration_service import ExpirationService
from app.schemas.document import DocumentResponse


router = APIRouter(
    prefix="/api/expiration",
    tags=["Expiration"],
)


def serialize_documents(
    service: ExpirationService,
    documents: list[Document],
) -> list[dict]:
    return [
        service.serialize(document)
        for document in documents
    ]


@router.get("/summary")
def expiration_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_staff_read),
):
    service = ExpirationService(db)
    return service.get_summary()


@router.get(
    "/expired",
    response_model=list[DocumentResponse],
)
def expired_documents(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_staff_read),
):
    service = ExpirationService(db)

    return serialize_documents(
        service,
        service.get_expired_documents(),
    )


@router.get(
    "/urgent",
    response_model=list[DocumentResponse],
)
def urgent_documents(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_staff_read),
):
    service = ExpirationService(db)

    return serialize_documents(
        service,
        service.get_urgent_documents(),
    )


@router.get(
    "/approaching",
    response_model=list[DocumentResponse],
)
def approaching_documents(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_staff_read),
):
    service = ExpirationService(db)

    return serialize_documents(
        service,
        service.get_approaching_documents(),
    )


@router.get(
    "/valid",
    response_model=list[DocumentResponse],
)
def valid_documents(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_staff_read),
):
    service = ExpirationService(db)

    return serialize_documents(
        service,
        service.get_valid_documents(),
    )


@router.get(
    "/no-date",
    response_model=list[DocumentResponse],
)
def documents_without_expiry(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_staff_read),
):
    service = ExpirationService(db)

    return serialize_documents(
        service,
        service.get_documents_without_expiry(),
    )
