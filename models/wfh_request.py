from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime, date, timezone


class WFHRequest(SQLModel, table=True):
    __tablename__ = "wfh_requests"

    id: Optional[int] = Field(default=None, primary_key=True)
    employee_id: int = Field(foreign_key="employees.id", index=True)
    start_date: date
    end_date: date
    reason: str
    status: str = Field(default="pending_manager")
    manager_status: str = Field(default="pending")
    manager_comments: Optional[str] = None
    hr_status: str = Field(default="pending")
    hr_comments: Optional[str] = None
    leadership_status: str = Field(default="skipped")
    leadership_comments: Optional[str] = None
    applied_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
