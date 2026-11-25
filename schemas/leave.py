from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import date, datetime


class LeaveTypeCreate(BaseModel):
    name: str
    description: Optional[str] = None
    annual_quota: int


class LeaveTypeUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    annual_quota: Optional[int] = None
    is_active: Optional[bool] = None


class LeaveTypeResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    annual_quota: int
    is_active: bool
    model_config = ConfigDict(from_attributes=True)


class LeaveApplyRequest(BaseModel):
    leave_type_id: int
    start_date: date
    end_date: date
    reason: str


class LeaveResponse(BaseModel):
    id: int
    employee_id: int
    employee_name: Optional[str] = None
    employee_code: Optional[str] = None
    employee_role: Optional[str] = None
    department_name: Optional[str] = None
    leave_type_id: int
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


class LeaveReviewRequest(BaseModel):
    action: str
    comments: Optional[str] = None


class LeaveApprovalResponse(BaseModel):
    id: int
    leave_request_id: int
    approver_user_id: int
    approval_level: str
    decision: str
    comments: Optional[str] = None
    acted_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)
