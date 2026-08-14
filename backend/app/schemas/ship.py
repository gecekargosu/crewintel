from datetime import datetime
import re

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ShipBase(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    imo_number: str | None = None
    flag: str | None = Field(default=None, max_length=100)
    ship_type: str | None = Field(default=None, max_length=100)
    company: str | None = Field(default=None, max_length=200)
    status: str = Field(default="active", min_length=1, max_length=50)

    @field_validator("name", "status")
    @classmethod
    def text_cannot_be_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("This field cannot be blank.")
        return value

    @field_validator("imo_number")
    @classmethod
    def imo_number_must_have_seven_digits(cls, value: str | None) -> str | None:
        if value is None or value == "":
            return None
        value = value.strip()
        if not re.fullmatch(r"\d{7}", value):
            raise ValueError("IMO number must contain exactly seven digits.")
        return value


class ShipCreate(ShipBase):
    pass


class ShipUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    imo_number: str | None = None
    flag: str | None = Field(default=None, max_length=100)
    ship_type: str | None = Field(default=None, max_length=100)
    company: str | None = Field(default=None, max_length=200)
    status: str | None = Field(default=None, min_length=1, max_length=50)

    @field_validator("name", "status")
    @classmethod
    def update_text_cannot_be_blank(cls, value: str | None) -> str | None:
        if value is not None and not value.strip():
            raise ValueError("This field cannot be blank.")
        return value.strip() if value is not None else value

    @field_validator("imo_number")
    @classmethod
    def update_imo_number_must_have_seven_digits(cls, value: str | None) -> str | None:
        return ShipBase.imo_number_must_have_seven_digits(value)


class ShipResponse(ShipBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime
