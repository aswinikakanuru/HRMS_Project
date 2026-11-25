from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import date, datetime


class AttendanceCreate(BaseModel):
    employee_id: int
    attendance_date: date
    check_in: Optional[datetime] = None
    check_out: Optional[datetime] = None
    status: str = "present"
    remarks: Optional[str] = None


class AttendanceUpdate(BaseModel):
    check_in: Optional[datetime] = None
    check_out: Optional[datetime] = None
    status: Optional[str] = None
    remarks: Optional[str] = None


class AttendanceResponse(BaseModel):
    id: int
    employee_id: int
    employee_name: Optional[str] = None
    employee_code: Optional[str] = None
    department_name: Optional[str] = None
    shift_id: Optional[int] = None
    shift_name: Optional[str] = None
    attendance_date: date
    check_in: Optional[datetime] = None
    check_out: Optional[datetime] = None
    work_hours: float = 0.0
    status: str
    is_late: bool = False
    late_minutes: int = 0
    is_early_out: bool = False
    early_out_minutes: int = 0
    detected_ot_hours: float = 0.0
    overtime_hours: float = 0.0
    ot_approved: bool = False
    deduction_reason: Optional[str] = None
    is_regularised: bool = False
    regularisation_remarks: Optional[str] = None
    remarks: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class AttendanceClockResponse(BaseModel):
    action: str
    attendance: AttendanceResponse


class RegularisationApplyRequest(BaseModel):
    attendance_date: date
    requested_check_in: datetime
    requested_check_out: datetime
    reason: str


class RegularisationReviewRequest(BaseModel):
    action: str
    comments: Optional[str] = None


class RegularisationResponse(BaseModel):
    id: int
    employee_id: int
    employee_name: Optional[str] = None
    employee_code: Optional[str] = None
    employee_role: Optional[str] = None
    department_name: Optional[str] = None
    attendance_date: date
    requested_check_in: datetime
    requested_check_out: datetime
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


class OvertimeApplyRequest(BaseModel):
    ot_date: date
    ot_hours: float
    reason: str


class OvertimeReviewRequest(BaseModel):
    action: str
    comments: Optional[str] = None


class OvertimeResponse(BaseModel):
    id: int
    employee_id: int
    employee_name: Optional[str] = None
    employee_code: Optional[str] = None
    employee_role: Optional[str] = None
    department_name: Optional[str] = None
    ot_date: date
    ot_hours: float
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
