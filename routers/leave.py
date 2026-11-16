from fastapi import APIRouter, Depends, status
from sqlmodel import Session
from database import get_session
from models.employee import Employee
from models.user import User
from schemas.leave import (
    LeaveTypeCreate,
    LeaveTypeResponse,
    LeaveApplyRequest,
    LeaveResponse,
    LeaveReviewRequest,
    LeaveApprovalResponse,
)
from dependencies.auth import get_current_user, get_current_employee, require_roles
from services.leave_service import (
    create_leave_type as create_leave_type_service,
    get_active_leave_types,
    get_leave_balances as get_leave_balances_service,
    apply_leave as apply_leave_service,
    get_employee_leaves,
    get_pending_leaves as get_pending_leaves_service,
    review_leave as review_leave_service,
)

router = APIRouter(prefix="/leaves", tags=["Leaves"])

# 1. Manage Leave Types (Admin & HR only)
@router.post("/types", response_model=LeaveTypeResponse, status_code=status.HTTP_201_CREATED)
def create_leave_type(
    data: LeaveTypeCreate,
    session: Session = Depends(get_session),
    _: None = Depends(require_roles(["Admin", "HR"]))
):
    return create_leave_type_service(session, data)

@router.get("/types", response_model=list[LeaveTypeResponse])
def list_leave_types(
    session: Session = Depends(get_session),
    _ = Depends(get_current_user)
):
    return get_active_leave_types(session)

# 2. View My Leave Balances (Quota vs Used vs Remaining)
@router.get("/balances")
def get_my_leave_balances(
    session: Session = Depends(get_session),
    employee: Employee = Depends(get_current_employee)
):
    return get_leave_balances_service(session, employee.id)

# 3. Employee: Apply for Leave
@router.post("/apply", response_model=LeaveResponse, status_code=status.HTTP_201_CREATED)
def apply_leave(
    data: LeaveApplyRequest,
    session: Session = Depends(get_session),
    employee: Employee = Depends(get_current_employee)
):
    return apply_leave_service(session, employee.id, data)

# 4. Employee: View My Leave Requests
@router.get("/my-leaves", response_model=list[LeaveResponse])
def get_my_leaves(
    session: Session = Depends(get_session),
    employee: Employee = Depends(get_current_employee)
):
    return get_employee_leaves(session, employee.id)

# 5. Manager / HR: View Pending Leaves
@router.get("/pending", response_model=list[LeaveResponse])
def get_pending_leaves(
    session: Session = Depends(get_session),
    _: User = Depends(require_roles(["Admin", "HR", "Manager"]))
):
    return get_pending_leaves_service(session)

# 6. Manager / HR: Review Approve / Reject Leave
@router.post("/{leave_id}/review", response_model=LeaveApprovalResponse)
def review_leave(
    leave_id: int,
    review_data: LeaveReviewRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_roles(["Admin", "HR", "Manager"]))
):
    return review_leave_service(session, leave_id, review_data, current_user.id)
