from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.assignment import ShipCrewAssignment
from app.models.crew_member import CrewMember
from app.schemas.crew_member import CrewMemberCreate, CrewMemberResponse, CrewMemberUpdate
from app.services.audit import log_event


router = APIRouter(prefix="/api/crew", tags=["Crew"])


def get_crew_member_or_404(crew_member_id: int, db: Session) -> CrewMember:
    crew_member = db.get(CrewMember, crew_member_id)
    if crew_member is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Crew member not found.")
    return crew_member


@router.post("/", response_model=CrewMemberResponse, status_code=status.HTTP_201_CREATED)
def create_crew_member(member: CrewMemberCreate, db: Session = Depends(get_db)):
    crew_member = CrewMember(**member.model_dump())
    try:
        db.add(crew_member)
        db.flush()
        log_event(db, "crew_created", "crew_member", crew_member.id,
                  f"Crew member created: {crew_member.first_name} {crew_member.last_name}")
        db.commit()
        db.refresh(crew_member)
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Crew member conflicts with an existing record.") from error
    except SQLAlchemyError as error:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Crew member could not be created.") from error
    return crew_member


@router.get("/", response_model=list[CrewMemberResponse])
def list_crew_members(
    name: str | None = None,
    surname: str | None = None,
    position: str | None = None,
    nationality: str | None = None,
    status_filter: str | None = Query(default=None, alias="status"),
    ship_id: int | None = Query(default=None, gt=0),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    db: Session = Depends(get_db),
):
    try:
        query = db.query(CrewMember)
        if name:
            query = query.filter(CrewMember.first_name.ilike(f"%{name.strip()}%"))
        if surname:
            query = query.filter(CrewMember.last_name.ilike(f"%{surname.strip()}%"))
        if position:
            query = query.filter(CrewMember.position.ilike(f"%{position.strip()}%"))
        if nationality:
            query = query.filter(CrewMember.nationality.ilike(f"%{nationality.strip()}%"))
        if status_filter:
            query = query.filter(CrewMember.status == status_filter.strip())
        if ship_id:
            query = query.join(ShipCrewAssignment).filter(ShipCrewAssignment.ship_id == ship_id).distinct()
        return query.order_by(CrewMember.id).offset(offset).limit(limit).all()
    except SQLAlchemyError as error:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Crew members are temporarily unavailable.") from error


@router.get("/{crew_member_id}", response_model=CrewMemberResponse)
def get_crew_member(crew_member_id: int, db: Session = Depends(get_db)):
    return get_crew_member_or_404(crew_member_id, db)


@router.put("/{crew_member_id}", response_model=CrewMemberResponse)
def update_crew_member(crew_member_id: int, member: CrewMemberUpdate, db: Session = Depends(get_db)):
    crew_member = get_crew_member_or_404(crew_member_id, db)
    for field_name, value in member.model_dump(exclude_unset=True).items():
        setattr(crew_member, field_name, value)
    try:
        log_event(db, "crew_updated", "crew_member", crew_member.id,
                  f"Crew member updated: {crew_member.first_name} {crew_member.last_name}")
        db.commit()
        db.refresh(crew_member)
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Crew member conflicts with an existing record.") from error
    except SQLAlchemyError as error:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Crew member could not be updated.") from error
    return crew_member


@router.delete("/{crew_member_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_crew_member(crew_member_id: int, db: Session = Depends(get_db)):
    crew_member = get_crew_member_or_404(crew_member_id, db)
    crew_member_id_val = crew_member.id
    name = f"{crew_member.first_name} {crew_member.last_name}"
    try:
        db.delete(crew_member)
        log_event(db, "crew_deleted", "crew_member", crew_member_id_val,
                  f"Crew member deleted: {name}")
        db.commit()
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Crew member has related records and cannot be deleted.") from error
    except SQLAlchemyError as error:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Crew member could not be deleted.") from error
