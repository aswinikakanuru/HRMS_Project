from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import Response
from sqlmodel import Session

from database import get_session
from dependencies.auth import get_current_employee, get_current_user, require_roles
from models.employee import Employee
from models.user import User
from schemas.attendance import (
    AttendanceClockResponse,
    AttendanceResponse,
    OvertimeApplyRequest,
    OvertimeResponse,
    OvertimeReviewRequest,
    RegularisationApplyRequest,
    RegularisationResponse,
    RegularisationReviewRequest,
)
from services.attendance_service import (
    apply_overtime as apply_overtime_service,
    apply_regularisation as apply_regularisation_service,
    clock_in as clock_in_service,
    clock_out as clock_out_service,
    export_attendance_csv as export_attendance_csv_service,
    get_my_attendance_history as get_my_attendance_history_service,
    get_my_overtime as get_my_overtime_service,
    get_my_regularisations as get_my_regularisations_service,
    get_pending_overtime as get_pending_overtime_service,
    get_pending_regularisations as get_pending_regularisations_service,
    get_team_attendance as get_team_attendance_service,
    get_today_attendance as get_today_attendance_service,
    review_overtime as review_overtime_service,
    review_regularisation as review_regularisation_service,
)

router = APIRouter(prefix="/attendance", tags=["Attendance, Regularisation & Overtime"])


# 1. CLOCK IN / CLOCK OUT
@router.post("/clock-in", response_model=AttendanceClockResponse)
def clock_in(
    session: Session = Depends(get_session),
    employee: Employee = Depends(get_current_employee),
):
    return clock_in_service(session, employee.id)


@router.post("/clock-out", response_model=AttendanceClockResponse)
def clock_out(
    session: Session = Depends(get_session),
    employee: Employee = Depends(get_current_employee),
):
    return clock_out_service(session, employee.id)


@router.get("/today", response_model=AttendanceResponse)
def get_today_attendance(
    session: Session = Depends(get_session),
    employee: Employee = Depends(get_current_employee),
):
    return get_today_attendance_service(session, employee.id)


@router.get("/my-history", response_model=list[AttendanceResponse])
def get_my_attendance_history(
    session: Session = Depends(get_session),
    employee: Employee = Depends(get_current_employee),
):
    return get_my_attendance_history_service(session, employee.id)


@router.get("/team", response_model=list[AttendanceResponse])
def get_team_attendance(
    q: Optional[str] = Query(None, description="Search employee name, code, or email"),
    department_id: Optional[int] = Query(None, description="Filter by department"),
    manager_id: Optional[int] = Query(None, description="Filter by manager"),
    session: Session = Depends(get_session),
    current_user: User = Depends(require_roles(["Leadership", "Admin", "Manager", "HR"])),
    current_emp: Employee = Depends(get_current_employee),
):
    return get_team_attendance_service(session, current_user, current_emp, q=q, department_id=department_id, manager_id=manager_id)


@router.get("/export-csv")
def export_attendance_csv(
    session: Session = Depends(get_session),
    _: User = Depends(require_roles(["Admin", "HR", "Leadership"])),
) -> Response:
    return export_attendance_csv_service(session)


# 2. ATTENDANCE REGULARISATION
@router.post("/regularisations/apply", response_model=RegularisationResponse, status_code=status.HTTP_201_CREATED)
def apply_regularisation(
    data: RegularisationApplyRequest,
    session: Session = Depends(get_session),
    employee: Employee = Depends(get_current_employee),
):
    return apply_regularisation_service(session, employee, data)


@router.get("/regularisations/my", response_model=list[RegularisationResponse])
def my_regularisations(
    session: Session = Depends(get_session),
    employee: Employee = Depends(get_current_employee),
):
    return get_my_regularisations_service(session, employee.id)


@router.get("/regularisations/pending", response_model=list[RegularisationResponse])
def pending_regularisations(
    session: Session = Depends(get_session),
    current_user: User = Depends(require_roles(["Leadership", "Admin", "Manager", "HR"])),
    current_emp: Employee = Depends(get_current_employee),
):
    return get_pending_regularisations_service(session, current_user, current_emp)


@router.post("/regularisations/{req_id}/review", response_model=RegularisationResponse)
def review_regularisation(
    req_id: int,
    review_data: RegularisationReviewRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_roles(["Leadership", "Admin", "Manager", "HR"])),
    current_emp: Employee = Depends(get_current_employee),
):
    return review_regularisation_service(session, req_id, review_data, current_user, current_emp)


# 3. OVERTIME (OT) TRACKING
@router.post("/overtime/apply", response_model=OvertimeResponse, status_code=status.HTTP_201_CREATED)
def apply_overtime(
    data: OvertimeApplyRequest,
    session: Session = Depends(get_session),
    employee: Employee = Depends(get_current_employee),
):
    return apply_overtime_service(session, employee, data)


@router.get("/overtime/my", response_model=list[OvertimeResponse])
def my_overtime(
    session: Session = Depends(get_session),
    employee: Employee = Depends(get_current_employee),
):
    return get_my_overtime_service(session, employee.id)


@router.get("/overtime/pending", response_model=list[OvertimeResponse])
def pending_overtime(
    session: Session = Depends(get_session),
    current_user: User = Depends(require_roles(["Leadership", "Admin", "Manager", "HR"])),
    current_emp: Employee = Depends(get_current_employee),
):
    return get_pending_overtime_service(session, current_user, current_emp)


@router.post("/overtime/{req_id}/review", response_model=OvertimeResponse)
def review_overtime(
    req_id: int,
    review_data: OvertimeReviewRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_roles(["Leadership", "Admin", "Manager", "HR"])),
    current_emp: Employee = Depends(get_current_employee),
):
    return review_overtime_service(session, req_id, review_data, current_user, current_emp)
