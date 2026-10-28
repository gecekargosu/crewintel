from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ContractBase(BaseModel):
    crew_member_id: int = Field(gt=0)
    ship_id: int = Field(gt=0)
    contract_number: str = Field(min_length=1, max_length=100)
    contract_type: str = Field(min_length=1, max_length=100)
    start_date: date
    end_date: date | None = None
    status: str = Field(default="active", min_length=1, max_length=50)
    notes: str | None = None

    @model_validator(mode="after")
    def end_date_must_not_precede_start_date(self):
        if self.end_date is not None and self.end_date < self.start_date:
            raise ValueError("end_date cannot be before start_date.")
        return self


class ContractCreate(ContractBase):
    pass


class ContractUpdate(BaseModel):
    crew_member_id: int | None = Field(default=None, gt=0)
    ship_id: int | None = Field(default=None, gt=0)
    contract_number: str | None = Field(default=None, min_length=1, max_length=100)
    contract_type: str | None = Field(default=None, min_length=1, max_length=100)
    start_date: date | None = None
    end_date: date | None = None
    status: str | None = Field(default=None, min_length=1, max_length=50)
    notes: str | None = None


class ContractResponse(ContractBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime
