from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime, date, timezone

class LeaveRequest(SQLModel, table=True):
    __tablename__ = "leave_requests"

    id: Optional[int] = Field(default=None, primary_key=True)
    employee_id: int = Field(foreign_key="employees.id", index=True)
    leave_type_id: int = Field(foreign_key="leave_types.id")
    start_date: date
    end_date: date
    reason: str
    status: str = Field(default="pending_manager")
    applied_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
