from sqlmodel import Session, select
from datetime import datetime, timezone
from fastapi import HTTPException, status
from models.leave_request import LeaveRequest
from models.leave_approval import LeaveApproval
from models.leave_type import LeaveType
from models.employee import Employee
from schemas.leave import LeaveTypeCreate, LeaveApplyRequest, LeaveReviewRequest
from services.notification_service import send_notification

def create_leave_type(session: Session, data: LeaveTypeCreate) -> LeaveType:
    leave_type = LeaveType(**data.model_dump())
    session.add(leave_type)
    session.commit()
    session.refresh(leave_type)
    return leave_type

def get_active_leave_types(session: Session) -> list[LeaveType]:
    return session.exec(select(LeaveType).where(LeaveType.is_active == True)).all()

def get_leave_balances(session: Session, employee_id: int) -> list[dict]:
    leave_types = get_active_leave_types(session)
    balances = []

    for lt in leave_types:
        approved_leaves = session.exec(
            select(LeaveRequest).where(
                LeaveRequest.employee_id == employee_id,
                LeaveRequest.leave_type_id == lt.id,
                LeaveRequest.status == "approved"
            )
        ).all()

        used_days = sum((l.end_date - l.start_date).days + 1 for l in approved_leaves)
        remaining_days = max(0, lt.annual_quota - used_days)

        balances.append({
            "leave_type_id": lt.id,
            "leave_type_name": lt.name,
            "annual_quota": lt.annual_quota,
            "used_days": used_days,
            "remaining_days": remaining_days
        })

    return balances

def apply_leave(session: Session, employee_id: int, data: LeaveApplyRequest) -> LeaveRequest:
    if data.end_date < data.start_date:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="End date cannot be earlier than start date")

    leave_type = session.get(LeaveType, data.leave_type_id)
    if not leave_type or not leave_type.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or inactive leave type")

    # Quota validation
    requested_days = (data.end_date - data.start_date).days + 1
    approved_leaves = session.exec(
        select(LeaveRequest).where(
            LeaveRequest.employee_id == employee_id,
            LeaveRequest.leave_type_id == data.leave_type_id,
            LeaveRequest.status == "approved"
        )
    ).all()
    used_days = sum((l.end_date - l.start_date).days + 1 for l in approved_leaves)
    remaining_days = max(0, leave_type.annual_quota - used_days)

    if requested_days > remaining_days:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Insufficient leave balance. You requested {requested_days} day(s), but only have {remaining_days} day(s) remaining for {leave_type.name}."
        )

    # Collision check
    overlap_query = select(LeaveRequest).where(
        LeaveRequest.employee_id == employee_id,
        LeaveRequest.status.in_(["pending_manager", "approved"]),
        LeaveRequest.start_date <= data.end_date,
        LeaveRequest.end_date >= data.start_date
    )
    if session.exec(overlap_query).first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You already have an active or pending leave during these dates")

    new_leave = LeaveRequest(
        employee_id=employee_id,
        leave_type_id=data.leave_type_id,
        start_date=data.start_date,
        end_date=data.end_date,
        reason=data.reason,
        status="pending_manager"
    )
    session.add(new_leave)
    session.commit()
    session.refresh(new_leave)

    # Notify Manager
    emp = session.get(Employee, employee_id)
    if emp and emp.manager_id:
        mgr = session.get(Employee, emp.manager_id)
        if mgr and mgr.user_id:
            send_notification(
                session=session,
                user_id=mgr.user_id,
                title="New Leave Application",
                message=f"{emp.firstname} {emp.lastname} applied for leave ({data.start_date} to {data.end_date}). Reason: {data.reason}"
            )

    return new_leave

def get_employee_leaves(session: Session, employee_id: int) -> list[LeaveRequest]:
    statement = (
        select(LeaveRequest)
        .where(LeaveRequest.employee_id == employee_id)
        .order_by(LeaveRequest.applied_at.desc())
    )
    return session.exec(statement).all()

def get_pending_leaves(session: Session) -> list[LeaveRequest]:
    statement = select(LeaveRequest).where(LeaveRequest.status == "pending_manager")
    return session.exec(statement).all()

def review_leave(session: Session, leave_id: int, review_data: LeaveReviewRequest, approver_user_id: int) -> LeaveApproval:
    leave_req = session.get(LeaveRequest, leave_id)
    if not leave_req:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Leave request not found")

    action = review_data.action.lower()
    if action not in ["approved", "rejected"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Action must be 'approved' or 'rejected'")

    leave_req.status = action

    approval = LeaveApproval(
        leave_request_id=leave_req.id,
        approver_user_id=approver_user_id,
        approval_level="manager",
        decision=action,
        comments=review_data.comments,
        acted_at=datetime.now(timezone.utc)
    )
    session.add(approval)
    session.commit()
    session.refresh(approval)

    # Notify employee of decision
    emp = session.get(Employee, leave_req.employee_id)
    if emp and emp.user_id:
        send_notification(
            session=session,
            user_id=emp.user_id,
            title="Leave Request Decision",
            message=f"Your leave request from {leave_req.start_date} to {leave_req.end_date} was {action}. Comments: {review_data.comments or 'None'}"
        )

    return approval
