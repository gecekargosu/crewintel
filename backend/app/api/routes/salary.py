"""Maaş/Bütçe takibi — ödeme kayıtları."""


from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_roles
from app.db.database import get_db
from app.models.user import User


router = APIRouter(prefix="/api/salary", tags=["Salary"])

_payments: list[dict] = []
_payment_id_counter = 0


class PaymentCreate(BaseModel):
    crew_member_id: int
    amount: float = Field(gt=0)
    currency: str = "USD"
    payment_type: str = "salary"  # salary, bonus, advance, other
    description: str = ""
    payment_date: str = ""


def _serialize(p: dict) -> dict:
    return {
        "id": p["id"],
        "crew_member_id": p["crew_member_id"],
        "amount": p["amount"],
        "currency": p.get("currency", "USD"),
        "payment_type": p.get("payment_type", "salary"),
        "description": p.get("description", ""),
        "payment_date": p.get("payment_date", ""),
        "created_at": p.get("created_at", ""),
        "user_email": p.get("user_email", ""),
    }


@router.get("/", response_model=list[dict])
def list_payments(
    crew_member_id: int | None = None,
    current_user: User = Depends(get_current_user),
):
    results = _payments
    if crew_member_id is not None:
        results = [p for p in results if p.get("crew_member_id") == crew_member_id]
    return [_serialize(p) for p in sorted(results, key=lambda x: x["id"], reverse=True)]


@router.post("/", status_code=status.HTTP_201_CREATED)
def create_payment(
    payload: PaymentCreate,
    current_user: User = Depends(require_roles("admin", "hr")),
):
    global _payment_id_counter
    _payment_id_counter += 1
    payment = {
        "id": _payment_id_counter,
        "crew_member_id": payload.crew_member_id,
        "amount": payload.amount,
        "currency": payload.currency,
        "payment_type": payload.payment_type,
        "description": payload.description,
        "payment_date": payload.payment_date or datetime.now().strftime("%Y-%m-%d"),
        "created_at": datetime.now().isoformat(),
        "user_email": current_user.email,
    }
    _payments.append(payment)
    return _serialize(payment)


@router.delete("/{payment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_payment(
    payment_id: int,
    current_user: User = Depends(require_roles("admin")),
):
    global _payments
    _payments = [p for p in _payments if p["id"] != payment_id]
