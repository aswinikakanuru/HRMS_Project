from fastapi import APIRouter, Depends
from fastapi.responses import Response
from sqlmodel import Session

from database import get_session
from models.employee import Employee
from models.user import User
from schemas.attendance import AttendanceResponse, AttendanceClockResponse
from dependencies.auth import get_current_employee, require_roles
from services.attendance_service import (
    clock_in as clock_in_service,
    clock_out as clock_out_service,
    get_today_attendance as get_today_attendance_service,
    get_my_attendance_history as get_my_attendance_history_service,
    export_attendance_csv as export_attendance_csv_service,
)

router = APIRouter(prefix="/attendance", tags=["Attendance"])

# 1. CLOCK IN
@router.post("/clock-in", response_model=AttendanceClockResponse)
def clock_in(
    session: Session = Depends(get_session),
    employee: Employee = Depends(get_current_employee)
):
    return clock_in_service(session, employee.id)

# 2. CLOCK OUT
@router.post("/clock-out", response_model=AttendanceClockResponse)
def clock_out(
    session: Session = Depends(get_session),
    employee: Employee = Depends(get_current_employee)
):
    return clock_out_service(session, employee.id)

# 3. GET TODAY'S ATTENDANCE STATUS
@router.get("/today", response_model=AttendanceResponse)
def get_today_attendance(
    session: Session = Depends(get_session),
    employee: Employee = Depends(get_current_employee)
):
    return get_today_attendance_service(session, employee.id)

# 4. MY ATTENDANCE HISTORY
@router.get("/my-history", response_model=list[AttendanceResponse])
def get_my_attendance_history(
    session: Session = Depends(get_session),
    employee: Employee = Depends(get_current_employee)
):
    return get_my_attendance_history_service(session, employee.id)

# 5. HR / Admin: Export All Attendance to CSV
@router.get("/export-csv")
def export_attendance_csv(
    session: Session = Depends(get_session),
    _: User = Depends(require_roles(["Admin", "HR"]))
) -> Response:
    return export_attendance_csv_service(session)
