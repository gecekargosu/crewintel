"""Maaş / ödeme takibi.

Önceki sürümde ödemeler bellekte (`list`) tutuluyordu — sunucu yeniden
başlayınca tüm kayıtlar kayboluyordu. Bu sürümde PostgreSQL tablosu
kullanılır ve her değişiklik denetim kaydına yazılır.
"""

from datetime import date
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import require_roles, require_staff_read
from app.db.database import get_db
from app.models.crew_member import CrewMember
from app.models.payment import Payment
from app.models.user import User
from app.services.audit import log_event

router = APIRouter(prefix="/api/salary", tags=["Salary"])

PAYMENT_TYPES = ("salary", "bonus", "advance", "other")


class PaymentCreate(BaseModel):
    crew_member_id: int
    amount: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    currency: str = Field(default="USD", min_length=2, max_length=10)
    payment_type: str = "salary"
    description: str = ""
    payment_date: date | None = None


class PaymentUpdate(BaseModel):
    amount: Decimal | None = Field(default=None, gt=0, max_digits=12, decimal_places=2)
    currency: str | None = Field(default=None, min_length=2, max_length=10)
    payment_type: str | None = None
    description: str | None = None
    payment_date: date | None = None


def _serialize(payment: Payment) -> dict:
    return {
        "id": payment.id,
        "crew_member_id": payment.crew_member_id,
        "amount": float(payment.amount),
        "currency": payment.currency,
        "payment_type": payment.payment_type,
        "description": payment.description or "",
        "payment_date": payment.payment_date.isoformat() if payment.payment_date else "",
        "created_at": payment.created_at.isoformat() if payment.created_at else "",
    }


def _validate_type(payment_type: str) -> str:
    value = (payment_type or "salary").strip().lower()
    if value not in PAYMENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Geçersiz ödeme tipi: {payment_type}. Seçenekler: {', '.join(PAYMENT_TYPES)}.",
        )
    return value


def _require_crew(crew_member_id: int, db: Session) -> CrewMember:
    crew = db.get(CrewMember, crew_member_id)
    if crew is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Personel bulunamadı.")
    return crew


@router.get("/")
def list_payments(
    crew_member_id: int | None = Query(default=None),
    year: int | None = Query(default=None, ge=1900, le=2200),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_staff_read),
):
    query = db.query(Payment)
    if crew_member_id is not None:
        query = query.filter(Payment.crew_member_id == crew_member_id)
    if year is not None:
        query = query.filter(func.extract("year", Payment.payment_date) == year)

    payments = query.order_by(Payment.payment_date.desc(), Payment.id.desc()).all()
    return [_serialize(payment) for payment in payments]


@router.get("/summary")
def salary_summary(
    year: int | None = Query(default=None, ge=1900, le=2200),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_staff_read),
):
    """Para birimi ve türe göre toplamlar (dashboard kartı için)."""
    query = db.query(
        Payment.currency,
        Payment.payment_type,
        func.sum(Payment.amount).label("total"),
        func.count(Payment.id).label("count"),
    )
    if year is not None:
        query = query.filter(func.extract("year", Payment.payment_date) == year)

    rows = query.group_by(Payment.currency, Payment.payment_type).all()

    totals: dict[str, float] = {}
    by_type: list[dict] = []
    for currency, payment_type, total, count in rows:
        amount = float(total or 0)
        totals[currency] = round(totals.get(currency, 0.0) + amount, 2)
        by_type.append(
            {
                "currency": currency,
                "payment_type": payment_type,
                "total": round(amount, 2),
                "count": int(count),
            }
        )

    return {"totals_by_currency": totals, "breakdown": by_type}


@router.post("/", status_code=status.HTTP_201_CREATED)
def create_payment(
    payload: PaymentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "hr")),
):
    _require_crew(payload.crew_member_id, db)

    payment = Payment(
        crew_member_id=payload.crew_member_id,
        amount=payload.amount,
        currency=payload.currency.upper(),
        payment_type=_validate_type(payload.payment_type),
        description=payload.description,
        payment_date=payload.payment_date or date.today(),
        created_by_user_id=current_user.id,
    )
    db.add(payment)
    db.flush()

    log_event(
        db,
        "payment_created",
        "payment",
        payment.id,
        f"Payment {payment.amount} {payment.currency} for crew #{payment.crew_member_id}",
        metadata={"payment_date": str(payment.payment_date)},
        user_email=current_user.email,
    )

    db.commit()
    db.refresh(payment)
    return _serialize(payment)


@router.put("/{payment_id}")
def update_payment(
    payment_id: int,
    payload: PaymentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "hr")),
):
    payment = db.get(Payment, payment_id)
    if payment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ödeme kaydı bulunamadı.")

    if payload.amount is not None:
        payment.amount = payload.amount
    if payload.currency is not None:
        payment.currency = payload.currency.upper()
    if payload.payment_type is not None:
        payment.payment_type = _validate_type(payload.payment_type)
    if payload.description is not None:
        payment.description = payload.description
    if payload.payment_date is not None:
        payment.payment_date = payload.payment_date

    log_event(
        db,
        "payment_updated",
        "payment",
        payment.id,
        f"Payment updated: {payment.amount} {payment.currency}",
        user_email=current_user.email,
    )

    db.commit()
    db.refresh(payment)
    return _serialize(payment)


@router.delete("/{payment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_payment(
    payment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin")),
):
    payment = db.get(Payment, payment_id)
    if payment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ödeme kaydı bulunamadı.")

    log_event(
        db,
        "payment_deleted",
        "payment",
        payment.id,
        f"Payment deleted: {payment.amount} {payment.currency}",
        user_email=current_user.email,
    )

    db.delete(payment)
    db.commit()
