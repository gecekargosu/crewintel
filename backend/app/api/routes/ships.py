from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_staff_read, require_roles
from app.db.database import get_db
from app.models.ship import Ship
from app.models.ship_position import ShipPosition
from app.models.assignment import ShipCrewAssignment
from app.models.user import User
from app.schemas.ship import ShipCreate, ShipResponse, ShipUpdate
from app.services.audit import log_event


router = APIRouter(prefix="/api/ships", tags=["Ships"])


def get_ship_or_404(ship_id: int, db: Session) -> Ship:
    ship = db.get(Ship, ship_id)
    if ship is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ship not found.")
    return ship


@router.post("/", response_model=ShipResponse, status_code=status.HTTP_201_CREATED)
def create_ship(
    ship_data: ShipCreate,
    db: Session = Depends(get_db),
    actor: User = Depends(require_roles("admin", "hr")),
):
    ship = Ship(**ship_data.model_dump())
    try:
        db.add(ship)
        db.flush()
        log_event(db, "ship_created", "ship", ship.id, f"Ship created: {ship.name}", user_email=actor.email)
        db.commit()
        db.refresh(ship)
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="IMO number already exists.") from error
    except SQLAlchemyError as error:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Ship could not be created.") from error
    return ship


@router.get("/", response_model=list[ShipResponse])
def list_ships(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_staff_read),
):
    return db.query(Ship).order_by(Ship.id).all()


@router.get("/{ship_id}", response_model=ShipResponse)
def get_ship(
    ship_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_staff_read),
):
    return get_ship_or_404(ship_id, db)


@router.put("/{ship_id}", response_model=ShipResponse)
def update_ship(
    ship_id: int,
    ship_data: ShipUpdate,
    db: Session = Depends(get_db),
    actor: User = Depends(require_roles("admin", "hr")),
):
    ship = get_ship_or_404(ship_id, db)
    for field_name, value in ship_data.model_dump(exclude_unset=True).items():
        setattr(ship, field_name, value)
    try:
        log_event(db, "ship_updated", "ship", ship.id, f"Ship updated: {ship.name}", user_email=actor.email)
        db.commit()
        db.refresh(ship)
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="IMO number already exists.") from error
    return ship


@router.delete("/{ship_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_ship(
    ship_id: int,
    db: Session = Depends(get_db),
    actor: User = Depends(require_roles("admin", "hr")),
):
    ship = get_ship_or_404(ship_id, db)
    ship_id_val = ship.id
    name = ship.name
    try:
        db.delete(ship)
        log_event(db, "ship_deleted", "ship", ship_id_val, f"Ship deleted: {name}", user_email=actor.email)
        db.commit()
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Ship has related records and cannot be deleted.") from error


# ── GEMİ KADRO PLANI (Ship Positions) ────────────────────────────────────────


class PositionCreate(BaseModel):
    position: str = Field(min_length=1, max_length=100)
    required_count: int = Field(default=1, ge=1, le=100)


@router.get("/{ship_id}/staffing", response_model=list[dict])
def ship_staffing(
    ship_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_staff_read),
):
    """Gemideki kadro planı: pozisyon, ihtiyaç, mevcut (aktif atama), açık."""
    get_ship_or_404(ship_id, db)
    positions = db.query(ShipPosition).filter(ShipPosition.ship_id == ship_id).order_by(ShipPosition.position).all()
    filled_counts = dict(
        db.query(ShipCrewAssignment.position, func.count(ShipCrewAssignment.id))
        .filter(ShipCrewAssignment.ship_id == ship_id, ShipCrewAssignment.status == "active")
        .group_by(ShipCrewAssignment.position)
        .all()
    )
    result = []
    for pos in positions:
        filled = filled_counts.get(pos.position, 0)
        result.append({
            "id": pos.id,
            "position": pos.position,
            "required": pos.required_count,
            "filled": filled,
            "open": max(0, pos.required_count - filled),
        })
    return result


@router.post("/{ship_id}/positions", response_model=dict, status_code=status.HTTP_201_CREATED)
def add_ship_position(
    ship_id: int,
    payload: PositionCreate,
    db: Session = Depends(get_db),
    actor: User = Depends(require_roles("admin", "hr")),
):
    get_ship_or_404(ship_id, db)
    existing = db.query(ShipPosition).filter(ShipPosition.ship_id == ship_id, ShipPosition.position == payload.position).first()
    if existing:
        existing.required_count = payload.required_count
        log_event(db, "ship_position_updated", "ship", ship_id, f"Position updated: {payload.position} ({payload.required_count})", user_email=actor.email)
        db.commit()
        return {"id": existing.id, "position": existing.position, "required": existing.required_count}
    position = ShipPosition(ship_id=ship_id, position=payload.position, required_count=payload.required_count)
    db.add(position)
    db.flush()
    log_event(db, "ship_position_added", "ship", ship_id, f"Position added: {payload.position} ({payload.required_count})", user_email=actor.email)
    db.commit()
    return {"id": position.id, "position": position.position, "required": position.required_count}


@router.delete("/positions/{position_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_ship_position(
    position_id: int,
    db: Session = Depends(get_db),
    actor: User = Depends(require_roles("admin", "hr")),
):
    position = db.get(ShipPosition, position_id)
    if position is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Position not found.")
    log_event(db, "ship_position_deleted", "ship", position.ship_id, f"Position deleted: {position.position}", user_email=actor.email)
    db.delete(position)
    db.commit()
