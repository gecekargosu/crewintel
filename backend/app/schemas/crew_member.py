from datetime import date, datetime
import re

from pydantic import BaseModel, ConfigDict, Field, field_validator


class CrewMemberBase(BaseModel):
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    date_of_birth: date | None = None
    nationality: str | None = Field(default=None, max_length=100)
    passport_number: str | None = Field(default=None, max_length=100)
    seaman_book_number: str | None = Field(default=None, max_length=100)
    position: str = Field(min_length=1, max_length=100)
    rank: str | None = Field(default=None, max_length=100)
    phone: str | None = Field(default=None, max_length=50)
    email: str | None = Field(default=None, max_length=255)
    address: str | None = None
    emergency_contact_name: str | None = Field(default=None, max_length=200)
    emergency_contact_phone: str | None = Field(default=None, max_length=50)
    birth_place: str | None = Field(default=None, max_length=150)
    hometown: str | None = Field(default=None, max_length=150)
    marital_status: str | None = Field(default=None, max_length=50)
    experience_years: int | None = Field(default=None, ge=0)
    sea_service_months: int | None = Field(default=None, ge=0)
    languages: str | None = None
    education_summary: str | None = None
    notes: str | None = None
    profile_data: dict | None = None
    status: str = Field(default="active", min_length=1, max_length=50)
    availability: str | None = Field(
        default="available",
        pattern="^(available|on_board|on_leave|not_available)$",
    )

    @field_validator("first_name", "last_name", "position", "status")
    @classmethod
    def required_text_cannot_be_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("This field cannot be blank.")
        return value

    @field_validator("email")
    @classmethod
    def email_must_be_valid(cls, value: str | None) -> str | None:
        if value is None or value == "":
            return None
        value = value.strip().lower()
        if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", value):
            raise ValueError("Invalid email address.")
        return value


class CrewMemberCreate(CrewMemberBase):
    pass


class CrewMemberUpdate(BaseModel):
    first_name: str | None = Field(default=None, min_length=1, max_length=100)
    last_name: str | None = Field(default=None, min_length=1, max_length=100)
    date_of_birth: date | None = None
    nationality: str | None = Field(default=None, max_length=100)
    passport_number: str | None = Field(default=None, max_length=100)
    seaman_book_number: str | None = Field(default=None, max_length=100)
    position: str | None = Field(default=None, min_length=1, max_length=100)
    rank: str | None = Field(default=None, max_length=100)
    phone: str | None = Field(default=None, max_length=50)
    email: str | None = Field(default=None, max_length=255)
    address: str | None = None
    emergency_contact_name: str | None = Field(default=None, max_length=200)
    emergency_contact_phone: str | None = Field(default=None, max_length=50)
    status: str | None = Field(default=None, min_length=1, max_length=50)
    birth_place: str | None = Field(default=None, max_length=150)
    hometown: str | None = Field(default=None, max_length=150)
    marital_status: str | None = Field(default=None, max_length=50)
    experience_years: int | None = Field(default=None, ge=0)
    sea_service_months: int | None = Field(default=None, ge=0)
    languages: str | None = None
    education_summary: str | None = None
    notes: str | None = None
    profile_data: dict | None = None

    @field_validator("first_name", "last_name", "position", "status")
    @classmethod
    def update_text_cannot_be_blank(cls, value: str | None) -> str | None:
        if value is not None and not value.strip():
            raise ValueError("This field cannot be blank.")
        return value.strip() if value is not None else value

    @field_validator("email")
    @classmethod
    def update_email_must_be_valid(cls, value: str | None) -> str | None:
        return CrewMemberBase.email_must_be_valid(value)


class CrewMemberResponse(CrewMemberBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime
