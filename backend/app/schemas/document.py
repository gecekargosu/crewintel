from datetime import date, datetime
from pydantic import BaseModel, ConfigDict, Field


class DocumentMatchUpdate(BaseModel):
    crew_member_id: int = Field(gt=0)


class DocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    crew_member_id: int | None
    original_filename: str
    mime_type: str | None
    file_size: int
    checksum: str
    document_type: str
    document_number: str | None
    issue_date: date | None
    expiry_date: date | None
    match_status: str
    match_confidence: int
    extracted_metadata: dict | None
    source: str
    created_at: datetime
    updated_at: datetime
    expiry_status: str | None = None
    duplicate: bool = False
    archived: bool = False
