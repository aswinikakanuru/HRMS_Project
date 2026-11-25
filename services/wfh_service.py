from typing import Optional
from fastapi import HTTPException, status
from sqlmodel import Session, select

from models.department import Department
from models.employee import Employee
from models.user import User
from models.wfh_request import WFHRequest
from schemas.wfh import WFHApplyRequest, WFHResponse, WFHReviewRequest
from services.approval_service import (
    filter_pending_for_reviewer,
    get_employee_user,
    get_initial_approval_state,
    notify_initial_approvers,
    process_tier_review,
)


def _format_wfh(session: Session, w: WFHRequest) -> WFHResponse:
    emp = session.get(Employee, w.employee_id)
    user = get_employee_user(session, emp)
    dept = session.get(Department, emp.department_id) if emp and emp.department_id else None
    return WFHResponse(
        id=w.id,
        employee_id=w.employee_id,
        employee_name=f"{emp.firstname} {emp.lastname}".strip() if emp else f"Emp {w.employee_id}",
        employee_code=emp.employee_code if emp else None,
        employee_role=user.role if user else "Employee",
        department_name=dept.name if dept else None,
        start_date=w.start_date,
        end_date=w.end_date,
        reason=w.reason,
        status=w.status,
        manager_status=w.manager_status or "pending",
        manager_comments=w.manager_comments,
        hr_status=w.hr_status or "pending",
        hr_comments=w.hr_comments,
        leadership_status=w.leadership_status or "skipped",
        leadership_comments=w.leadership_comments,
        applied_at=w.applied_at,
    )


def apply_wfh(session: Session, employee_id: int, data: WFHApplyRequest) -> WFHResponse:
    if data.end_date < data.start_date:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="End date cannot be earlier than start date")

    overlap_query = select(WFHRequest).where(
        WFHRequest.employee_id == employee_id,
        WFHRequest.status.in_(["pending_manager", "pending_hr", "pending_leadership", "approved"]),
        WFHRequest.start_date <= data.end_date,
        WFHRequest.end_date >= data.start_date,
    )
    if session.exec(overlap_query).first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You already have an active or pending WFH request during these dates")

    emp = session.get(Employee, employee_id)
    req_user = get_employee_user(session, emp)
    init_state = get_initial_approval_state(session, req_user, emp)

    new_wfh = WFHRequest(
        employee_id=employee_id,
        start_date=data.start_date,
        end_date=data.end_date,
        reason=data.reason,
        status=init_state["status"],
        manager_status=init_state["manager_status"],
        hr_status=init_state["hr_status"],
        leadership_status=init_state["leadership_status"],
    )
    session.add(new_wfh)
    session.commit()
    session.refresh(new_wfh)

    if init_state["status"] != "approved" and emp:
        notify_initial_approvers(
            session,
            req_user,
            emp,
            init_state["status"],
            "New WFH Application",
            f"{emp.firstname} {emp.lastname} requested WFH ({data.start_date} to {data.end_date}). Reason: {data.reason}",
        )

    return _format_wfh(session, new_wfh)


def get_employee_wfh_requests(session: Session, employee_id: int) -> list[WFHResponse]:
    rows = session.exec(
        select(WFHRequest)
        .where(WFHRequest.employee_id == employee_id)
        .order_by(WFHRequest.applied_at.desc())
    ).all()
    return [_format_wfh(session, w) for w in rows]


def get_pending_wfh(
    session: Session,
    reviewer_user: User,
    reviewer_emp: Optional[Employee],
) -> list[WFHResponse]:
    rows = session.exec(
        select(WFHRequest).where(
            WFHRequest.status.in_(["pending_manager", "pending_hr", "pending_leadership"])
        )
    ).all()
    filtered = filter_pending_for_reviewer(session, rows, reviewer_user, reviewer_emp)
    return [_format_wfh(session, w) for w in filtered]


def review_wfh(
    session: Session,
    wfh_id: int,
    review_data: WFHReviewRequest,
    reviewer_user: User,
    reviewer_emp: Optional[Employee],
) -> WFHResponse:
    wfh_req = session.get(WFHRequest, wfh_id)
    if not wfh_req:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="WFH request not found")

    req_emp = session.get(Employee, wfh_req.employee_id)
    process_tier_review(
        session=session,
        req_obj=wfh_req,
        requester_emp=req_emp,
        reviewer_user=reviewer_user,
        reviewer_emp=reviewer_emp,
        raw_action=review_data.action,
        comments=review_data.comments,
        request_label="Work From Home",
    )
    session.add(wfh_req)
    session.commit()
    session.refresh(wfh_req)
    return _format_wfh(session, wfh_req)
