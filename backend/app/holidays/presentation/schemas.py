from datetime import date
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class HolidayBase(BaseModel):
    name: str | None = Field(default=None, max_length=100)
    date: date


class HolidayCreate(HolidayBase):
    pass


class HolidayUpdate(BaseModel):
    # Optional in JSON, can be string or null
    name: str | None = Field(default=None, max_length=50)

    @field_validator("name")
    @classmethod
    def normalize_name(cls, v: str | None) -> str | None:
        # Field not provided → Pydantic leaves it at default (None),
        # but __fields_set__ will tell you if it was sent.
        if v is None:
            return None

        # If string, trim whitespace
        stripped = v.strip()
        # Treat empty/whitespace-only as "clear" (None)
        if stripped == "":
            return None

        return stripped


class HolidayRead(HolidayBase):
    id: UUID
    model_config = ConfigDict(from_attributes=True)
