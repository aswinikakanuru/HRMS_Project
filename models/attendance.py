from sqlmodel import SQLModel, Field
from datetime import datetime, date
from typing import Optional
from sqlalchemy import UniqueConstraint


class Attendance(SQLModel, table=True):
    __tablename__ = "attendance"

    __table_args__ = (
        UniqueConstraint(
            "employee_id",
            "attendance_date",
            name="unique_employee_attendance"
        ),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    employee_id: int = Field(foreign_key="employees.id", index=True)
    shift_id: Optional[int] = Field(default=None, foreign_key="shifts.id")
    attendance_date: date
    check_in: Optional[datetime] = None
    check_out: Optional[datetime] = None
    work_hours: float = Field(default=0.0)
    status: str = Field(default="present")
    is_late: bool = Field(default=False)
    late_minutes: int = Field(default=0)
    is_early_out: bool = Field(default=False)
    early_out_minutes: int = Field(default=0)
    detected_ot_hours: float = Field(default=0.0)
    overtime_hours: float = Field(default=0.0)
    ot_approved: bool = Field(default=False)
    deduction_reason: Optional[str] = None
    is_regularised: bool = Field(default=False)
    regularisation_remarks: Optional[str] = None
    remarks: Optional[str] = None
