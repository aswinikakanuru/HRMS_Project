from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import date, datetime


class WFHApplyRequest(BaseModel):
    start_date: date
    end_date: date
    reason: str


class WFHReviewRequest(BaseModel):
    action: str
    comments: Optional[str] = None


class WFHResponse(BaseModel):
    id: int
    employee_id: int
    employee_name: Optional[str] = None
    employee_code: Optional[str] = None
    employee_role: Optional[str] = None
    department_name: Optional[str] = None
    start_date: date
    end_date: date
    reason: str
    status: str
    manager_status: str = "pending"
    manager_comments: Optional[str] = None
    hr_status: str = "pending"
    hr_comments: Optional[str] = None
    leadership_status: str = "skipped"
    leadership_comments: Optional[str] = None
    applied_at: datetime

    model_config = ConfigDict(from_attributes=True)
