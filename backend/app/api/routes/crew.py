from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.crew_member import CrewMember
from app.schemas.crew_member import CrewMemberCreate, CrewMemberResponse


router = APIRouter(
    prefix="/api/crew",
    tags=["Crew"]
)


@router.post("/", response_model=CrewMemberResponse)
def create_crew_member(
    member: CrewMemberCreate,
    db: Session = Depends(get_db),
):
    crew_member = CrewMember(
        first_name=member.first_name,
        last_name=member.last_name,
        position=member.position,
        nationality=member.nationality,
    )

    db.add(crew_member)
    db.commit()
    db.refresh(crew_member)

    return crew_member


@router.get("/", response_model=list[CrewMemberResponse])
def list_crew_members(
    db: Session = Depends(get_db),
):
    return db.query(CrewMember).all()