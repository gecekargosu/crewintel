from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_staff_read, require_roles
from app.api.routes.crew import get_crew_member_or_404
from app.api.routes.ships import get_ship_or_404
from app.db.database import get_db
from app.models.user import User
from app.models.contract import Contract
from app.schemas.contract import ContractCreate, ContractResponse, ContractUpdate
from app.services.audit import log_event


router = APIRouter(prefix="/api/contracts", tags=["Contracts"])


def get_contract_or_404(contract_id: int, db: Session) -> Contract:
    contract = db.get(Contract, contract_id)
    if contract is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contract not found.")
    return contract


def validate_references(ship_id: int, crew_member_id: int, db: Session) -> None:
    get_ship_or_404(ship_id, db)
    get_crew_member_or_404(crew_member_id, db)


def validate_contract_dates(contract: Contract) -> None:
    if contract.end_date is not None and contract.end_date < contract.start_date:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="end_date cannot be before start_date.")


@router.post("/", response_model=ContractResponse, status_code=status.HTTP_201_CREATED)
def create_contract(
    contract_data: ContractCreate,
    db: Session = Depends(get_db),
    actor: User = Depends(require_roles("admin", "hr")),
):
    validate_references(contract_data.ship_id, contract_data.crew_member_id, db)
    contract = Contract(**contract_data.model_dump())
    try:
        db.add(contract)
        db.flush()
        log_event(db, "contract_created", "contract", contract.id,
                  f"Contract created: {contract.contract_number}", user_email=actor.email)
        db.commit()
        db.refresh(contract)
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Contract number already exists.") from error
    return contract


@router.get("/", response_model=list[ContractResponse])
def list_contracts(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_staff_read),
):
    return db.query(Contract).order_by(Contract.id).all()


@router.get("/{contract_id}", response_model=ContractResponse)
def get_contract(
    contract_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_staff_read),
):
    return get_contract_or_404(contract_id, db)


@router.put("/{contract_id}", response_model=ContractResponse)
def update_contract(
    contract_id: int,
    contract_data: ContractUpdate,
    db: Session = Depends(get_db),
    actor: User = Depends(require_roles("admin", "hr")),
):
    contract = get_contract_or_404(contract_id, db)
    updates = contract_data.model_dump(exclude_unset=True)
    effective_ship_id = updates.get("ship_id", contract.ship_id)
    effective_crew_member_id = updates.get("crew_member_id", contract.crew_member_id)
    validate_references(effective_ship_id, effective_crew_member_id, db)
    for field_name, value in updates.items():
        setattr(contract, field_name, value)
    validate_contract_dates(contract)
    try:
        log_event(db, "contract_updated", "contract", contract.id,
                  f"Contract updated: {contract.contract_number}", user_email=actor.email)
        db.commit()
        db.refresh(contract)
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Contract number already exists.") from error
    return contract


@router.delete("/{contract_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_contract(
    contract_id: int,
    db: Session = Depends(get_db),
    actor: User = Depends(require_roles("admin", "hr")),
):
    contract = get_contract_or_404(contract_id, db)
    contract_id_val = contract.id
    number = contract.contract_number
    db.delete(contract)
    log_event(db, "contract_deleted", "contract", contract_id_val,
              f"Contract deleted: {number}", user_email=actor.email)
    db.commit()
