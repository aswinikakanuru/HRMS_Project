from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import date

class Holiday(SQLModel, table=True):
    __tablename__ = "holidays"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    holiday_date: date = Field(unique=True, index=True)
    description: Optional[str] = None
    is_optional: bool = Field(default=False)
