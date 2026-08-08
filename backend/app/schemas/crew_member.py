from datetime import datetime

from pydantic import BaseModel, ConfigDict


class CrewMemberCreate(BaseModel):
    first_name: str
    last_name: str
    position: str
    nationality: str | None = None


class CrewMemberResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    first_name: str
    last_name: str
    position: str
    nationality: str | None
    created_at: datetime