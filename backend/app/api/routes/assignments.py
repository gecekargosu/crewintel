from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_staff_read, require_roles
from app.api.routes.crew import get_crew_member_or_404
from app.api.routes.ships import get_ship_or_404
from app.db.database import get_db
from app.models.user import User
from app.models.assignment import ShipCrewAssignment
from app.schemas.assignment import AssignmentCreate, AssignmentResponse, AssignmentUpdate
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


@router.post("/", response_model=AssignmentResponse, status_code=status.HTTP_201_CREATED)
def create_assignment(
    assignment_data: AssignmentCreate,
    db: Session = Depends(get_db),
    actor: User = Depends(require_roles("admin", "hr")),
):
    validate_references(assignment_data.ship_id, assignment_data.crew_member_id, db)
    assignment = ShipCrewAssignment(**assignment_data.model_dump())
    try:
        db.add(assignment)
        db.flush()

        # Atama yapınca personelin müsaitliğini güncelle
        from app.models.crew_member import CrewMember
        crew = db.get(CrewMember, assignment_data.crew_member_id)
        if crew and crew.availability == "available":
            crew.availability = "on_board"

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

    # Atama silinince personelin müsaitliğini geri yükle
    from app.models.crew_member import CrewMember
    crew = db.get(CrewMember, crew_id)
    if crew and crew.availability == "on_board":
        # Başka aktif ataması varsa 'on_board' kalsın
        other_assignments = db.query(ShipCrewAssignment).filter(
            ShipCrewAssignment.crew_member_id == crew_id,
            ShipCrewAssignment.id != assignment_id_val,
        ).count()
        if other_assignments == 0:
            crew.availability = "available"

    log_event(db, "assignment_deleted", "ship_crew_assignment", assignment_id_val,
              f"Assignment deleted: crew {crew_id} → ship {ship_id}",
              user_email=actor.email)
    db.commit()
