from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.ship import Ship
from app.schemas.ship import ShipCreate, ShipResponse, ShipUpdate
from app.services.audit import log_event


router = APIRouter(prefix="/api/ships", tags=["Ships"])


def get_ship_or_404(ship_id: int, db: Session) -> Ship:
    ship = db.get(Ship, ship_id)
    if ship is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ship not found.")
    return ship


@router.post("/", response_model=ShipResponse, status_code=status.HTTP_201_CREATED)
def create_ship(ship_data: ShipCreate, db: Session = Depends(get_db)):
    ship = Ship(**ship_data.model_dump())
    try:
        db.add(ship)
        db.flush()
        log_event(db, "ship_created", "ship", ship.id, f"Ship created: {ship.name}")
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
def list_ships(db: Session = Depends(get_db)):
    return db.query(Ship).order_by(Ship.id).all()


@router.get("/{ship_id}", response_model=ShipResponse)
def get_ship(ship_id: int, db: Session = Depends(get_db)):
    return get_ship_or_404(ship_id, db)


@router.put("/{ship_id}", response_model=ShipResponse)
def update_ship(ship_id: int, ship_data: ShipUpdate, db: Session = Depends(get_db)):
    ship = get_ship_or_404(ship_id, db)
    for field_name, value in ship_data.model_dump(exclude_unset=True).items():
        setattr(ship, field_name, value)
    try:
        log_event(db, "ship_updated", "ship", ship.id, f"Ship updated: {ship.name}")
        db.commit()
        db.refresh(ship)
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="IMO number already exists.") from error
    return ship


@router.delete("/{ship_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_ship(ship_id: int, db: Session = Depends(get_db)):
    ship = get_ship_or_404(ship_id, db)
    ship_id_val = ship.id
    name = ship.name
    try:
        db.delete(ship)
        log_event(db, "ship_deleted", "ship", ship_id_val, f"Ship deleted: {name}")
        db.commit()
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Ship has related records and cannot be deleted.") from error
