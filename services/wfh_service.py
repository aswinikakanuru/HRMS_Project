from sqlmodel import Session, select
from datetime import datetime, timezone
from fastapi import HTTPException, status
from models.wfh_request import WFHRequest
from models.employee import Employee
from schemas.wfh import WFHApplyRequest, WFHReviewRequest
from services.notification_service import send_notification

def apply_wfh(session: Session, employee_id: int, data: WFHApplyRequest) -> WFHRequest:
    if data.end_date < data.start_date:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="End date cannot be earlier than start date")

    overlap_query = select(WFHRequest).where(
        WFHRequest.employee_id == employee_id,
        WFHRequest.status.in_(["pending_manager", "approved"]),
        WFHRequest.start_date <= data.end_date,
        WFHRequest.end_date >= data.start_date
    )
    if session.exec(overlap_query).first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You already have an active or pending WFH request during these dates")

    new_wfh = WFHRequest(
        employee_id=employee_id,
        start_date=data.start_date,
        end_date=data.end_date,
        reason=data.reason,
        status="pending_manager"
    )
    session.add(new_wfh)
    session.commit()
    session.refresh(new_wfh)

    # Notify Manager
    emp = session.get(Employee, employee_id)
    if emp and emp.manager_id:
        mgr = session.get(Employee, emp.manager_id)
        if mgr and mgr.user_id:
            send_notification(
                session=session,
                user_id=mgr.user_id,
                title="New WFH Application",
                message=f"{emp.firstname} {emp.lastname} requested WFH ({data.start_date} to {data.end_date}). Reason: {data.reason}"
            )

    return new_wfh

def get_employee_wfh_requests(session: Session, employee_id: int) -> list[WFHRequest]:
    statement = (
        select(WFHRequest)
        .where(WFHRequest.employee_id == employee_id)
        .order_by(WFHRequest.applied_at.desc())
    )
    return session.exec(statement).all()

def get_pending_wfh(session: Session) -> list[WFHRequest]:
    statement = select(WFHRequest).where(WFHRequest.status == "pending_manager")
    return session.exec(statement).all()

def review_wfh(session: Session, wfh_id: int, review_data: WFHReviewRequest) -> WFHRequest:
    wfh_req = session.get(WFHRequest, wfh_id)
    if not wfh_req:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="WFH request not found")

    action = review_data.action.lower()
    if action not in ["approved", "rejected"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Action must be 'approved' or 'rejected'")

    wfh_req.status = action
    session.add(wfh_req)
    session.commit()
    session.refresh(wfh_req)

    # Notify employee of decision
    emp = session.get(Employee, wfh_req.employee_id)
    if emp and emp.user_id:
        send_notification(
            session=session,
            user_id=emp.user_id,
            title="Work From Home Decision",
            message=f"Your WFH request from {wfh_req.start_date} to {wfh_req.end_date} was {action}. Comments: {review_data.comments or 'None'}"
        )

    return wfh_req
