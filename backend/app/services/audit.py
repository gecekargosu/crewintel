from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog


def log_event(
    session: Session,
    action: str,
    entity: str,
    entity_id: int | None,
    message: str,
    status: str = "success",
    metadata: dict | None = None,
    user_email: str | None = None,
) -> None:
    session.add(AuditLog(
        action=action,
        entity=entity,
        entity_id=entity_id,
        message=message,
        status=status,
        metadata_json=metadata,
        user_email=user_email,
    ))
