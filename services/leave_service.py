from datetime import datetime, timezone
from typing import Optional
from fastapi import HTTPException, status
from sqlmodel import Session, select

from models.department import Department
from models.employee import Employee
from models.leave_approval import LeaveApproval
from models.leave_request import LeaveRequest
from models.leave_type import LeaveType
from models.user import User
from schemas.leave import LeaveApplyRequest, LeaveResponse, LeaveReviewRequest, LeaveTypeCreate
from services.approval_service import (
    filter_pending_for_reviewer,
    get_employee_user,
    get_initial_approval_state,
    notify_initial_approvers,
    process_tier_review,
)


def create_leave_type(session: Session, data: LeaveTypeCreate) -> LeaveType:
    existing = session.exec(select(LeaveType).where(LeaveType.name == data.name)).first()
    if existing:
        existing.annual_quota = data.annual_quota
        existing.description = data.description
        existing.is_active = True
        session.add(existing)
        session.commit()
        session.refresh(existing)
        return existing
    leave_type = LeaveType(**data.model_dump())
    session.add(leave_type)
    session.commit()
    session.refresh(leave_type)
    return leave_type


def get_active_leave_types(session: Session) -> list[LeaveType]:
    types = session.exec(select(LeaveType).where(LeaveType.is_active == True)).all()
    seen = set()
    unique_types = []
    for t in types:
        key = (t.name or "").strip().lower()
        if key and key not in seen:
            seen.add(key)
            unique_types.append(t)
    return unique_types


def get_leave_balances(session: Session, employee_id: int) -> list[dict]:
    leave_types = get_active_leave_types(session)
    balances = []
    seen = set()

    for lt in leave_types:
        key = (lt.name or "").strip().lower()
        if key in seen:
            continue
        seen.add(key)

        approved_leaves = session.exec(
            select(LeaveRequest).where(
                LeaveRequest.employee_id == employee_id,
                LeaveRequest.leave_type_id == lt.id,
                LeaveRequest.status == "approved",
            )
        ).all()

        used_days = sum((l.end_date - l.start_date).days + 1 for l in approved_leaves)
        remaining_days = max(0, lt.annual_quota - used_days)

        balances.append({
            "leave_type_id": lt.id,
            "leave_type": lt.name,
            "leave_type_name": lt.name,
            "annual_quota": lt.annual_quota,
            "used_days": used_days,
            "remaining_days": remaining_days,
        })

    return balances


def _format_leave(session: Session, l: LeaveRequest) -> LeaveResponse:
    emp = session.get(Employee, l.employee_id)
    user = get_employee_user(session, emp)
    dept = session.get(Department, emp.department_id) if emp and emp.department_id else None
    return LeaveResponse(
        id=l.id,
        employee_id=l.employee_id,
        employee_name=f"{emp.firstname} {emp.lastname}".strip() if emp else f"Emp {l.employee_id}",
        employee_code=emp.employee_code if emp else None,
        employee_role=user.role if user else "Employee",
        department_name=dept.name if dept else None,
        leave_type_id=l.leave_type_id,
        start_date=l.start_date,
        end_date=l.end_date,
        reason=l.reason,
        status=l.status,
        manager_status=l.manager_status or "pending",
        manager_comments=l.manager_comments,
        hr_status=l.hr_status or "pending",
        hr_comments=l.hr_comments,
        leadership_status=l.leadership_status or "skipped",
        leadership_comments=l.leadership_comments,
        applied_at=l.applied_at,
    )


def apply_leave(session: Session, employee_id: int, data: LeaveApplyRequest) -> LeaveResponse:
    if data.end_date < data.start_date:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="End date cannot be earlier than start date")

    leave_type = session.get(LeaveType, data.leave_type_id)
    if not leave_type or not leave_type.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or inactive leave type")

    requested_days = (data.end_date - data.start_date).days + 1
    approved_leaves = session.exec(
        select(LeaveRequest).where(
            LeaveRequest.employee_id == employee_id,
            LeaveRequest.leave_type_id == data.leave_type_id,
            LeaveRequest.status == "approved",
        )
    ).all()
    used_days = sum((l.end_date - l.start_date).days + 1 for l in approved_leaves)
    remaining_days = max(0, leave_type.annual_quota - used_days)

    if requested_days > remaining_days:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Insufficient leave balance. You requested {requested_days} day(s), but only have {remaining_days} day(s) remaining for {leave_type.name}.",
        )

    overlap_query = select(LeaveRequest).where(
        LeaveRequest.employee_id == employee_id,
        LeaveRequest.status.in_(["pending_manager", "pending_hr", "pending_leadership", "approved"]),
        LeaveRequest.start_date <= data.end_date,
        LeaveRequest.end_date >= data.start_date,
    )
    if session.exec(overlap_query).first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You already have an active or pending leave during these dates")

    emp = session.get(Employee, employee_id)
    req_user = get_employee_user(session, emp)
    init_state = get_initial_approval_state(session, req_user, emp)

    new_leave = LeaveRequest(
        employee_id=employee_id,
        leave_type_id=data.leave_type_id,
        start_date=data.start_date,
        end_date=data.end_date,
        reason=data.reason,
        status=init_state["status"],
        manager_status=init_state["manager_status"],
        hr_status=init_state["hr_status"],
        leadership_status=init_state["leadership_status"],
    )
    session.add(new_leave)
    session.commit()
    session.refresh(new_leave)

    if init_state["status"] != "approved" and emp:
        notify_initial_approvers(
            session,
            req_user,
            emp,
            init_state["status"],
            "New Leave Application",
            f"{emp.firstname} {emp.lastname} applied for leave ({data.start_date} to {data.end_date}). Reason: {data.reason}",
        )

    return _format_leave(session, new_leave)


def get_employee_leaves(session: Session, employee_id: int) -> list[LeaveResponse]:
    rows = session.exec(
        select(LeaveRequest)
        .where(LeaveRequest.employee_id == employee_id)
        .order_by(LeaveRequest.applied_at.desc())
    ).all()
    return [_format_leave(session, l) for l in rows]


def get_pending_leaves(
    session: Session,
    reviewer_user: User,
    reviewer_emp: Optional[Employee],
) -> list[LeaveResponse]:
    rows = session.exec(
        select(LeaveRequest).where(
            LeaveRequest.status.in_(["pending_manager", "pending_hr", "pending_leadership"])
        )
    ).all()
    filtered = filter_pending_for_reviewer(session, rows, reviewer_user, reviewer_emp)
    return [_format_leave(session, l) for l in filtered]


def review_leave(
    session: Session,
    leave_id: int,
    review_data: LeaveReviewRequest,
    reviewer_user: User,
    reviewer_emp: Optional[Employee],
) -> LeaveApproval:
    leave_req = session.get(LeaveRequest, leave_id)
    if not leave_req:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Leave request not found")

    req_emp = session.get(Employee, leave_req.employee_id)
    new_status, level = process_tier_review(
        session=session,
        req_obj=leave_req,
        requester_emp=req_emp,
        reviewer_user=reviewer_user,
        reviewer_emp=reviewer_emp,
        raw_action=review_data.action,
        comments=review_data.comments,
        request_label="Leave",
    )

    decision = "rejected" if new_status == "rejected" else "approved"
    approval = LeaveApproval(
        leave_request_id=leave_req.id,
        approver_user_id=reviewer_user.id,
        approval_level=level,
        decision=decision,
        comments=review_data.comments or f"{decision.capitalize()} by {level}",
        acted_at=datetime.now(timezone.utc),
    )
    session.add(leave_req)
    session.add(approval)
    session.commit()
    session.refresh(approval)
    return approval
