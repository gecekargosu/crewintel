from datetime import date, datetime, time

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from app.api.deps import require_roles
from app.db.database import get_db
from app.models.audit_log import AuditLog
from app.models.user import User


router = APIRouter(prefix="/api/audit-logs", tags=["Audit Logs"])


class AuditLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    action: str
    entity: str
    entity_id: int | None
    message: str
    status: str
    user_email: str | None
    metadata_json: dict | None
    created_at: datetime


@router.get("/", response_model=list[AuditLogResponse])
def list_audit_logs(
    action: str | None = None,
    entity: str | None = None,
    entity_id: int | None = Query(default=None, gt=0),
    status: str | None = None,
    date_from: date | None = Query(default=None, description="Start date (inclusive), format: YYYY-MM-DD"),
    date_to: date | None = Query(default=None, description="End date (inclusive), format: YYYY-MM-DD"),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin")),
) -> list[AuditLog]:
    query = db.query(AuditLog)
    if action:
        query = query.filter(AuditLog.action == action.strip())
    if entity:
        query = query.filter(AuditLog.entity == entity.strip())
    if entity_id is not None:
        query = query.filter(AuditLog.entity_id == entity_id)
    if status:
        query = query.filter(AuditLog.status == status.strip())
    if date_from is not None:
        query = query.filter(AuditLog.created_at >= datetime.combine(date_from, time.min))
    if date_to is not None:
        query = query.filter(AuditLog.created_at <= datetime.combine(date_to, time.max))
    return query.order_by(AuditLog.created_at.desc()).offset(offset).limit(limit).all()
