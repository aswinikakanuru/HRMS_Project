from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import date

class HolidayCreate(BaseModel):
    name: str
    holiday_date: date
    description: Optional[str] = None
    is_optional: bool = False

class HolidayResponse(BaseModel):
    id: int
    name: str
    holiday_date: date
    description: Optional[str] = None
    is_optional: bool

    model_config = ConfigDict(from_attributes=True)
