from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import require_roles, require_staff_read
from app.api.routes.crew import get_crew_member_or_404
from app.api.routes.ships import get_ship_or_404
from app.db.database import get_db
from app.models.assignment import ShipCrewAssignment
from app.models.user import User
from app.schemas.assignment import (
    AssignmentCreate,
    AssignmentResponse,
    AssignmentUpdate,
)
from app.services.audit import log_event

router = APIRouter(prefix="/api/assignments", tags=["Assignments"])


def get_assignment_or_404(assignment_id: int, db: Session) -> ShipCrewAssignment:
    assignment = db.get(ShipCrewAssignment, assignment_id)
    if assignment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assignment not found.")
    return assignment


def validate_references(ship_id: int, crew_member_id: int, db: Session) -> None:
    get_ship_or_404(ship_id, db)
    get_crew_member_or_404(crew_member_id, db)


def validate_assignment_dates(assignment: ShipCrewAssignment) -> None:
    if assignment.end_date is not None and assignment.end_date < assignment.start_date:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="end_date cannot be before start_date.")


def validate_no_overlap(
    db: Session,
    crew_member_id: int,
    start_date,
    end_date,
    exclude_id: int | None = None,
) -> None:
    """Aynı personel aynı tarihlerde iki gemide olamaz.

    Önceden aynı kişi için çakışan iki aktif atama sessizce kaydediliyordu
    (personel iki gemide birden görünüyordu). Bitiş tarihi boş olan atama
    süresiz kabul edilir.
    """
    if start_date is None:
        return
    query = db.query(ShipCrewAssignment).filter(
        ShipCrewAssignment.crew_member_id == crew_member_id,
        ShipCrewAssignment.status == "active",
    )
    if exclude_id is not None:
        query = query.filter(ShipCrewAssignment.id != exclude_id)

    for existing in query.all():
        # [start, end] aralıklarında kesişim var mı? (bitiş boş = süresiz)
        existing_ends_after = existing.end_date is None or existing.end_date >= start_date
        new_ends_after = end_date is None or existing.start_date <= end_date
        if existing_ends_after and new_ends_after:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "Bu personelin belirtilen tarihlerde aktif bir ataması var "
                    f"(gemi #{existing.ship_id}, {existing.start_date}"
                    + (f" - {existing.end_date}" if existing.end_date else " - süresiz")
                    + ")."
                ),
            )


@router.post("/", response_model=AssignmentResponse, status_code=status.HTTP_201_CREATED)
def create_assignment(
    assignment_data: AssignmentCreate,
    db: Session = Depends(get_db),
    actor: User = Depends(require_roles("admin", "hr")),
):
    validate_references(assignment_data.ship_id, assignment_data.crew_member_id, db)
    if (assignment_data.status or "active") == "active":
        validate_no_overlap(
            db,
            assignment_data.crew_member_id,
            assignment_data.start_date,
            assignment_data.end_date,
        )
    assignment = ShipCrewAssignment(**assignment_data.model_dump())
    try:
        db.add(assignment)
        db.flush()
        log_event(db, "assignment_created", "ship_crew_assignment", assignment.id,
                  f"Assignment created: crew {assignment.crew_member_id} → ship {assignment.ship_id}",
                  user_email=actor.email)
        db.commit()
        db.refresh(assignment)
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Assignment could not be created.") from error
    return assignment


@router.get("/", response_model=list[AssignmentResponse])
def list_assignments(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_staff_read),
):
    return db.query(ShipCrewAssignment).order_by(ShipCrewAssignment.id).all()


@router.get("/{assignment_id}", response_model=AssignmentResponse)
def get_assignment(
    assignment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_staff_read),
):
    return get_assignment_or_404(assignment_id, db)


@router.put("/{assignment_id}", response_model=AssignmentResponse)
def update_assignment(
    assignment_id: int,
    assignment_data: AssignmentUpdate,
    db: Session = Depends(get_db),
    actor: User = Depends(require_roles("admin", "hr")),
):
    assignment = get_assignment_or_404(assignment_id, db)
    updates = assignment_data.model_dump(exclude_unset=True)
    effective_ship_id = updates.get("ship_id", assignment.ship_id)
    effective_crew_member_id = updates.get("crew_member_id", assignment.crew_member_id)
    validate_references(effective_ship_id, effective_crew_member_id, db)
    for field_name, value in updates.items():
        setattr(assignment, field_name, value)
    validate_assignment_dates(assignment)
    if assignment.status == "active":
        validate_no_overlap(
            db,
            assignment.crew_member_id,
            assignment.start_date,
            assignment.end_date,
            exclude_id=assignment.id,
        )
    try:
        log_event(db, "assignment_updated", "ship_crew_assignment", assignment.id,
                  f"Assignment updated: crew {assignment.crew_member_id} → ship {assignment.ship_id}",
                  user_email=actor.email)
        db.commit()
        db.refresh(assignment)
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Assignment could not be updated.") from error
    return assignment


@router.delete("/{assignment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_assignment(
    assignment_id: int,
    db: Session = Depends(get_db),
    actor: User = Depends(require_roles("admin", "hr")),
):
    assignment = get_assignment_or_404(assignment_id, db)
    assignment_id_val = assignment.id
    crew_id = assignment.crew_member_id
    ship_id = assignment.ship_id
    db.delete(assignment)
    log_event(db, "assignment_deleted", "ship_crew_assignment", assignment_id_val,
              f"Assignment deleted: crew {crew_id} → ship {ship_id}",
              user_email=actor.email)
    db.commit()
