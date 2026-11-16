from fastapi import APIRouter, Depends, status
from sqlmodel import Session
from database import get_session
from models.employee import Employee
from models.user import User
from schemas.wfh import WFHApplyRequest, WFHReviewRequest, WFHResponse
from dependencies.auth import get_current_employee, require_roles
from services.wfh_service import (
    apply_wfh as apply_wfh_service,
    get_employee_wfh_requests,
    get_pending_wfh as get_pending_wfh_service,
    review_wfh as review_wfh_service,
)

router = APIRouter(prefix="/wfh", tags=["Work From Home"])

# 1. Employee: Apply for WFH
@router.post("/apply", response_model=WFHResponse, status_code=status.HTTP_201_CREATED)
def apply_wfh(
    data: WFHApplyRequest,
    session: Session = Depends(get_session),
    employee: Employee = Depends(get_current_employee)
):
    return apply_wfh_service(session, employee.id, data)

# 2. Employee: View My WFH Requests
@router.get("/my-requests", response_model=list[WFHResponse])
def get_my_wfh_requests(
    session: Session = Depends(get_session),
    employee: Employee = Depends(get_current_employee)
):
    return get_employee_wfh_requests(session, employee.id)

# 3. Manager / HR: View Pending WFH Requests
@router.get("/pending", response_model=list[WFHResponse])
def get_pending_wfh(
    session: Session = Depends(get_session),
    _: User = Depends(require_roles(["Admin", "HR", "Manager"]))
):
    return get_pending_wfh_service(session)

# 4. Manager / HR: Review Approve / Reject WFH
@router.post("/{wfh_id}/review", response_model=WFHResponse)
def review_wfh(
    wfh_id: int,
    review_data: WFHReviewRequest,
    session: Session = Depends(get_session),
    _: User = Depends(require_roles(["Admin", "HR", "Manager"]))
):
    return review_wfh_service(session, wfh_id, review_data)
