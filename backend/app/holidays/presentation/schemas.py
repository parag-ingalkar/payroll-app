from datetime import date
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict


class HolidayBase(BaseModel):
    holiday_date: date = Field(..., description="The date of the holiday.")
    holiday_name: str | None = Field(None, description="The name of the holiday.")
    is_paid: bool = Field(True, description="Indicates if the holiday is paid.")


class HolidayCreate(HolidayBase):
    pass


class HolidayUpdate(BaseModel):
    holiday_name: str | None = Field(None, description="The new name of the holiday.")
    is_paid: bool | None = Field(None, description="Indicates if the holiday is paid.")


class HolidayResponse(HolidayBase):
    id: UUID = Field(..., description="The unique identifier of the holiday.")
    business_id: UUID = Field(..., description="The unique identifier of the business.")

    model_config = ConfigDict(from_attributes=True)
