import csv
import io
from datetime import date, datetime, timedelta, timezone
from typing import Optional
from fastapi import HTTPException, status
from fastapi.responses import Response
from sqlmodel import Session, select

from models.attendance import Attendance
from models.department import Department
from models.employee import Employee
from models.overtime_request import OvertimeRequest
from models.regularisation_request import RegularisationRequest
from models.shift import Shift
from models.user import User
from schemas.attendance import (
    AttendanceResponse,
    OvertimeApplyRequest,
    OvertimeResponse,
    OvertimeReviewRequest,
    RegularisationApplyRequest,
    RegularisationResponse,
    RegularisationReviewRequest,
)
from services.approval_service import (
    filter_pending_for_reviewer,
    get_employee_user,
    get_initial_approval_state,
    get_visible_employee_ids,
    notify_initial_approvers,
    process_tier_review,
)

# Indian Standard Time (IST = UTC+05:30)
IST = timezone(timedelta(hours=5, minutes=30))


def get_now_ist() -> datetime:
    """Returns current datetime in Indian Standard Time (IST)."""
    return datetime.now(IST)


def _parse_hhmm(hhmm: str) -> tuple[int, int]:
    try:
        parts = hhmm.strip().split(":")
        return int(parts[0]), int(parts[1])
    except Exception:
        return 9, 0


def format_duration_hm(hours_float: float) -> str:
    total_mins = max(0, int(round(hours_float * 60)))
    hrs, mins = divmod(total_mins, 60)
    return f"{hrs}h {mins:02d}m"


def evaluate_shift_rules(
    shift: Optional[Shift],
    check_in: datetime,
    check_out: Optional[datetime] = None,
) -> dict:
    """
    Evaluate Late-In / Early-Out against shift timings (e.g. 09:00 - 18:00),
    calculate elapsed time between Clock-In and Clock-Out, and mark Present.
    """
    grace_mins = shift.grace_period_mins if shift else 15
    full_hours = shift.full_day_hours if shift else 9.0

    start_str = shift.start_time if shift else "09:00"
    end_str = shift.end_time if shift else "18:00"
    sh, sm = _parse_hhmm(start_str)
    eh, em = _parse_hhmm(end_str)

    p_in = check_in if check_in.tzinfo else check_in.replace(tzinfo=IST)
    shift_start_dt = p_in.replace(hour=sh, minute=sm, second=0, microsecond=0)
    shift_end_dt = p_in.replace(hour=eh, minute=em, second=0, microsecond=0)
    if shift_end_dt <= shift_start_dt:
        shift_end_dt += timedelta(days=1)

    is_late = False
    late_minutes = 0
    diff_in_mins = int((p_in - shift_start_dt).total_seconds() // 60)
    if diff_in_mins > grace_mins:
        is_late = True
        late_minutes = diff_in_mins

    is_early_out = False
    early_out_minutes = 0
    work_hours = 0.0
    detected_ot_hours = 0.0

    if check_out is not None:
        p_out = check_out if check_out.tzinfo else check_out.replace(tzinfo=IST)
        work_hours = round(max(0.0, (p_out - p_in).total_seconds() / 3600.0), 2)

        diff_out_mins = int((shift_end_dt - p_out).total_seconds() // 60)
        if diff_out_mins > grace_mins:
            is_early_out = True
            early_out_minutes = diff_out_mins

        if work_hours > full_hours:
            detected_ot_hours = round(work_hours - full_hours, 2)

    return {
        "is_late": is_late,
        "late_minutes": late_minutes,
        "is_early_out": is_early_out,
        "early_out_minutes": early_out_minutes,
        "work_hours": work_hours,
        "detected_ot_hours": detected_ot_hours,
        "status": "Present",
        "deduction_reason": None,
    }


def _get_employee_shift(session: Session, employee_id: int) -> Optional[Shift]:
    emp = session.get(Employee, employee_id)
    if emp and emp.shift_id:
        s = session.get(Shift, emp.shift_id)
        if s:
            return s
    return session.exec(select(Shift).where(Shift.code == "GS")).first()


def _format_attendance(session: Session, att: Attendance) -> AttendanceResponse:
    emp = session.get(Employee, att.employee_id)
    dept = session.get(Department, emp.department_id) if emp and emp.department_id else None
    shift = session.get(Shift, att.shift_id) if att.shift_id else _get_employee_shift(session, att.employee_id)
    # Normalize legacy Half Day status to Present/Absent for clean display
    display_status = "Present" if att.check_in else "Absent"
    if att.status in ["On Time", "Late", "Present", "Absent"]:
        display_status = "Present" if att.check_in else "Absent"
    elif att.status == "Half Day" and att.check_in:
        display_status = "Present"

    calc_hours = att.work_hours or 0.0
    if att.check_in and att.check_out and calc_hours == 0.0:
        p_in = att.check_in if att.check_in.tzinfo else att.check_in.replace(tzinfo=IST)
        p_out = att.check_out if att.check_out.tzinfo else att.check_out.replace(tzinfo=IST)
        calc_hours = round(max(0.0, (p_out - p_in).total_seconds() / 3600.0), 2)

    return AttendanceResponse(
        id=att.id,
        employee_id=att.employee_id,
        employee_name=f"{emp.firstname} {emp.lastname}".strip() if emp else f"Emp {att.employee_id}",
        employee_code=emp.employee_code if emp else None,
        department_name=dept.name if dept else None,
        shift_id=shift.id if shift else None,
        shift_name=shift.name if shift else "General Shift",
        attendance_date=att.attendance_date,
        check_in=att.check_in,
        check_out=att.check_out,
        work_hours=calc_hours,
        status=display_status,
        is_late=bool(att.is_late),
        late_minutes=att.late_minutes or 0,
        is_early_out=bool(att.is_early_out),
        early_out_minutes=att.early_out_minutes or 0,
        detected_ot_hours=att.detected_ot_hours or 0.0,
        overtime_hours=att.overtime_hours or 0.0,
        ot_approved=bool(att.ot_approved),
        deduction_reason=None,
        is_regularised=bool(att.is_regularised),
        regularisation_remarks=att.regularisation_remarks,
        remarks=att.remarks,
    )


def clock_in(session: Session, employee_id: int) -> dict:
    now_ist = get_now_ist()
    today_ist = now_ist.date()

    attendance = session.exec(
        select(Attendance).where(
            Attendance.employee_id == employee_id,
            Attendance.attendance_date == today_ist,
        )
    ).first()

    if attendance and attendance.check_in:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Already clocked in today at {attendance.check_in.strftime('%I:%M %p')} IST",
        )

    shift = _get_employee_shift(session, employee_id)
    rules = evaluate_shift_rules(shift, now_ist, None)
    shift_label = f"{shift.name} ({shift.start_time}-{shift.end_time})" if shift else "09:00-18:00"
    if rules["is_late"]:
        remarks = f"Late login by {rules['late_minutes']}m at {now_ist.strftime('%I:%M %p')} IST ({shift_label})"
    else:
        remarks = f"On Time login at {now_ist.strftime('%I:%M %p')} IST ({shift_label})"
    if rules["deduction_reason"]:
        remarks = f"{remarks} | {rules['deduction_reason']}"

    if not attendance:
        attendance = Attendance(
            employee_id=employee_id,
            shift_id=shift.id if shift else None,
            attendance_date=today_ist,
            check_in=now_ist,
            status=rules["status"],
            is_late=rules["is_late"],
            late_minutes=rules["late_minutes"],
            deduction_reason=rules["deduction_reason"],
            remarks=remarks,
        )
        session.add(attendance)
    else:
        attendance.shift_id = shift.id if shift else attendance.shift_id
        attendance.check_in = now_ist
        attendance.status = rules["status"]
        attendance.is_late = rules["is_late"]
        attendance.late_minutes = rules["late_minutes"]
        attendance.deduction_reason = rules["deduction_reason"]
        attendance.remarks = remarks

    session.commit()
    session.refresh(attendance)
    return {"action": "CLOCK_IN_SUCCESS", "attendance": _format_attendance(session, attendance)}


def clock_out(session: Session, employee_id: int) -> dict:
    now_ist = get_now_ist()
    today_ist = now_ist.date()

    attendance = session.exec(
        select(Attendance).where(
            Attendance.employee_id == employee_id,
            Attendance.attendance_date == today_ist,
        )
    ).first()

    if not attendance or not attendance.check_in:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot clock out without clocking in first today.",
        )

    shift = session.get(Shift, attendance.shift_id) if attendance.shift_id else _get_employee_shift(session, employee_id)
    check_in_dt = attendance.check_in
    if check_in_dt.tzinfo is None:
        check_in_dt = check_in_dt.replace(tzinfo=IST)

    rules = evaluate_shift_rules(shift, check_in_dt, now_ist)

    attendance.check_out = now_ist
    attendance.work_hours = rules["work_hours"]
    attendance.is_late = rules["is_late"]
    attendance.late_minutes = rules["late_minutes"]
    attendance.is_early_out = rules["is_early_out"]
    attendance.early_out_minutes = rules["early_out_minutes"]
    attendance.detected_ot_hours = rules["detected_ot_hours"]
    attendance.status = rules["status"]
    attendance.deduction_reason = rules["deduction_reason"]

    if rules["is_early_out"]:
        logout_info = f"Early logout by {rules['early_out_minutes']}m at {now_ist.strftime('%I:%M %p')} IST"
    else:
        logout_info = f"Shift completed at {now_ist.strftime('%I:%M %p')} IST"

    existing_remarks = attendance.remarks or ""
    attendance.remarks = f"{existing_remarks} | {logout_info} ({rules['work_hours']:.2f}h worked)"
    if rules["deduction_reason"]:
        attendance.remarks += f" | {rules['deduction_reason']}"

    session.add(attendance)
    session.commit()
    session.refresh(attendance)
    return {"action": "CLOCK_OUT_SUCCESS", "attendance": _format_attendance(session, attendance)}


def get_today_attendance(session: Session, employee_id: int) -> AttendanceResponse:
    today_ist = get_now_ist().date()
    attendance = session.exec(
        select(Attendance).where(
            Attendance.employee_id == employee_id,
            Attendance.attendance_date == today_ist,
        )
    ).first()
    if not attendance:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not clocked in today")
    return _format_attendance(session, attendance)


def get_my_attendance_history(session: Session, employee_id: int) -> list[AttendanceResponse]:
    records = session.exec(
        select(Attendance)
        .where(Attendance.employee_id == employee_id)
        .order_by(Attendance.attendance_date.desc())
    ).all()
    return [_format_attendance(session, r) for r in records]


def get_team_attendance(
    session: Session,
    current_user: User,
    current_emp: Optional[Employee],
    q: Optional[str] = None,
    department_id: Optional[int] = None,
    manager_id: Optional[int] = None,
) -> list[AttendanceResponse]:
    visible_ids = get_visible_employee_ids(session, current_user, current_emp)
    emp_query = select(Employee)
    if visible_ids is not None:
        if not visible_ids:
            return []
        emp_query = emp_query.where(Employee.id.in_(visible_ids))
    if department_id:
        emp_query = emp_query.where(Employee.department_id == department_id)
    if manager_id:
        emp_query = emp_query.where(Employee.manager_id == manager_id)

    emps = session.exec(emp_query).all()
    if q:
        term = q.strip().lower()
        emps = [
            e for e in emps
            if term in f"{e.firstname} {e.lastname}".lower()
            or term in e.employee_code.lower()
            or term in e.email.lower()
        ]
    emp_ids = [e.id for e in emps]
    if not emp_ids:
        return []

    records = session.exec(
        select(Attendance)
        .where(Attendance.employee_id.in_(emp_ids))
        .order_by(Attendance.attendance_date.desc(), Attendance.id.desc())
    ).all()
    return [_format_attendance(session, r) for r in records[:100]]


def export_attendance_csv(session: Session) -> Response:
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Record ID", "Employee ID", "Date (IST)", "Check In (IST)", "Check Out (IST)",
        "Work Hours", "Status", "Late (mins)", "Early Out (mins)", "Approved OT", "Regularised", "Remarks"
    ])

    records = session.exec(select(Attendance).order_by(Attendance.attendance_date.desc())).all()
    for r in records:
        writer.writerow([
            r.id,
            r.employee_id,
            r.attendance_date,
            r.check_in.strftime("%Y-%m-%d %I:%M:%S %p") if r.check_in else "",
            r.check_out.strftime("%Y-%m-%d %I:%M:%S %p") if r.check_out else "",
            r.work_hours or 0.0,
            r.status,
            r.late_minutes or 0,
            r.early_out_minutes or 0,
            r.overtime_hours or 0.0,
            "Yes" if r.is_regularised else "No",
            r.remarks or "",
        ])

    output.seek(0)
    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=attendance_report.csv"},
    )


# ---------------- REGULARISATION REQUESTS ---------------- #

def _format_regularisation(session: Session, r: RegularisationRequest) -> RegularisationResponse:
    emp = session.get(Employee, r.employee_id)
    user = get_employee_user(session, emp)
    dept = session.get(Department, emp.department_id) if emp and emp.department_id else None
    return RegularisationResponse(
        id=r.id,
        employee_id=r.employee_id,
        employee_name=f"{emp.firstname} {emp.lastname}".strip() if emp else f"Emp {r.employee_id}",
        employee_code=emp.employee_code if emp else None,
        employee_role=user.role if user else "Employee",
        department_name=dept.name if dept else None,
        attendance_date=r.attendance_date,
        requested_check_in=r.requested_check_in,
        requested_check_out=r.requested_check_out,
        reason=r.reason,
        status=r.status,
        manager_status=r.manager_status,
        manager_comments=r.manager_comments,
        hr_status=r.hr_status,
        hr_comments=r.hr_comments,
        leadership_status=r.leadership_status,
        leadership_comments=r.leadership_comments,
        applied_at=r.applied_at,
    )


def apply_regularisation(
    session: Session,
    employee: Employee,
    data: RegularisationApplyRequest,
) -> RegularisationResponse:
    if data.requested_check_in >= data.requested_check_out:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Requested check-in time must be earlier than check-out time.",
        )

    req_user = get_employee_user(session, employee)
    init_state = get_initial_approval_state(session, req_user, employee)

    reg = RegularisationRequest(
        employee_id=employee.id,
        attendance_date=data.attendance_date,
        requested_check_in=data.requested_check_in,
        requested_check_out=data.requested_check_out,
        reason=data.reason,
        status=init_state["status"],
        manager_status=init_state["manager_status"],
        hr_status=init_state["hr_status"],
        leadership_status=init_state["leadership_status"],
    )
    session.add(reg)
    session.commit()
    session.refresh(reg)

    if init_state["status"] == "approved":
        _apply_approved_regularisation(session, reg)
    else:
        notify_initial_approvers(
            session,
            req_user,
            employee,
            init_state["status"],
            "New Attendance Regularisation",
            f"{employee.firstname} {employee.lastname} requested regularisation for {data.attendance_date}. Reason: {data.reason}",
        )

    return _format_regularisation(session, reg)


def _apply_approved_regularisation(session: Session, reg: RegularisationRequest) -> None:
    shift = _get_employee_shift(session, reg.employee_id)
    rules = evaluate_shift_rules(shift, reg.requested_check_in, reg.requested_check_out)
    new_status = "Present"

    att = session.exec(
        select(Attendance).where(
            Attendance.employee_id == reg.employee_id,
            Attendance.attendance_date == reg.attendance_date,
        )
    ).first()
    if not att:
        att = Attendance(
            employee_id=reg.employee_id,
            shift_id=shift.id if shift else None,
            attendance_date=reg.attendance_date,
            check_in=reg.requested_check_in,
            check_out=reg.requested_check_out,
            work_hours=rules["work_hours"],
            status=new_status,
            is_late=False,
            late_minutes=0,
            is_early_out=False,
            early_out_minutes=0,
            detected_ot_hours=rules["detected_ot_hours"],
            deduction_reason=None if new_status != "Half Day" else rules["deduction_reason"],
            is_regularised=True,
            regularisation_remarks=f"Regularised: {reg.reason}",
            remarks=f"Regularised ({rules['work_hours']:.2f}h): {reg.reason}",
        )
        session.add(att)
    else:
        att.shift_id = att.shift_id or (shift.id if shift else None)
        att.check_in = reg.requested_check_in
        att.check_out = reg.requested_check_out
        att.work_hours = rules["work_hours"]
        att.status = new_status
        att.is_late = False
        att.late_minutes = 0
        att.is_early_out = False
        att.early_out_minutes = 0
        att.detected_ot_hours = rules["detected_ot_hours"]
        att.deduction_reason = None if new_status != "Half Day" else rules["deduction_reason"]
        att.is_regularised = True
        att.regularisation_remarks = f"Regularised: {reg.reason}"
        att.remarks = f"Regularised ({rules['work_hours']:.2f}h): {reg.reason}"
        session.add(att)
    session.commit()


def get_my_regularisations(session: Session, employee_id: int) -> list[RegularisationResponse]:
    rows = session.exec(
        select(RegularisationRequest)
        .where(RegularisationRequest.employee_id == employee_id)
        .order_by(RegularisationRequest.applied_at.desc())
    ).all()
    return [_format_regularisation(session, r) for r in rows]


def get_pending_regularisations(
    session: Session,
    reviewer_user: User,
    reviewer_emp: Optional[Employee],
) -> list[RegularisationResponse]:
    rows = session.exec(
        select(RegularisationRequest).where(
            RegularisationRequest.status.in_(["pending_manager", "pending_hr", "pending_leadership"])
        )
    ).all()
    filtered = filter_pending_for_reviewer(session, rows, reviewer_user, reviewer_emp)
    return [_format_regularisation(session, r) for r in filtered]


def review_regularisation(
    session: Session,
    req_id: int,
    review_data: RegularisationReviewRequest,
    reviewer_user: User,
    reviewer_emp: Optional[Employee],
) -> RegularisationResponse:
    reg = session.get(RegularisationRequest, req_id)
    if not reg:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Regularisation request not found")

    req_emp = session.get(Employee, reg.employee_id)
    new_status, _ = process_tier_review(
        session=session,
        req_obj=reg,
        requester_emp=req_emp,
        reviewer_user=reviewer_user,
        reviewer_emp=reviewer_emp,
        raw_action=review_data.action,
        comments=review_data.comments,
        request_label="Attendance Regularisation",
    )
    session.add(reg)
    session.commit()
    session.refresh(reg)

    if new_status == "approved":
        _apply_approved_regularisation(session, reg)

    return _format_regularisation(session, reg)


# ---------------- OVERTIME (OT) REQUESTS ---------------- #

def _format_overtime(session: Session, r: OvertimeRequest) -> OvertimeResponse:
    emp = session.get(Employee, r.employee_id)
    user = get_employee_user(session, emp)
    dept = session.get(Department, emp.department_id) if emp and emp.department_id else None
    return OvertimeResponse(
        id=r.id,
        employee_id=r.employee_id,
        employee_name=f"{emp.firstname} {emp.lastname}".strip() if emp else f"Emp {r.employee_id}",
        employee_code=emp.employee_code if emp else None,
        employee_role=user.role if user else "Employee",
        department_name=dept.name if dept else None,
        ot_date=r.ot_date,
        ot_hours=r.ot_hours,
        reason=r.reason,
        status=r.status,
        manager_status=r.manager_status,
        manager_comments=r.manager_comments,
        hr_status=r.hr_status,
        hr_comments=r.hr_comments,
        leadership_status=r.leadership_status,
        leadership_comments=r.leadership_comments,
        applied_at=r.applied_at,
    )


def apply_overtime(
    session: Session,
    employee: Employee,
    data: OvertimeApplyRequest,
) -> OvertimeResponse:
    if data.ot_hours <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Overtime hours must be greater than 0.",
        )

    req_user = get_employee_user(session, employee)
    init_state = get_initial_approval_state(session, req_user, employee)

    ot_req = OvertimeRequest(
        employee_id=employee.id,
        ot_date=data.ot_date,
        ot_hours=round(data.ot_hours, 2),
        reason=data.reason,
        status=init_state["status"],
        manager_status=init_state["manager_status"],
        hr_status=init_state["hr_status"],
        leadership_status=init_state["leadership_status"],
    )
    session.add(ot_req)
    session.commit()
    session.refresh(ot_req)

    if init_state["status"] == "approved":
        _apply_approved_overtime(session, ot_req)
    else:
        notify_initial_approvers(
            session,
            req_user,
            employee,
            init_state["status"],
            "New Overtime Claim",
            f"{employee.firstname} {employee.lastname} claimed {data.ot_hours}h OT on {data.ot_date}. Reason: {data.reason}",
        )

    return _format_overtime(session, ot_req)


def _apply_approved_overtime(session: Session, ot_req: OvertimeRequest) -> None:
    shift = _get_employee_shift(session, ot_req.employee_id)
    att = session.exec(
        select(Attendance).where(
            Attendance.employee_id == ot_req.employee_id,
            Attendance.attendance_date == ot_req.ot_date,
        )
    ).first()
    if not att:
        att = Attendance(
            employee_id=ot_req.employee_id,
            shift_id=shift.id if shift else None,
            attendance_date=ot_req.ot_date,
            status="On Time",
            work_hours=0.0,
            overtime_hours=round(ot_req.ot_hours, 2),
            ot_approved=True,
            remarks=f"Approved OT ({ot_req.ot_hours}h): {ot_req.reason}",
        )
        session.add(att)
    else:
        att.overtime_hours = round((att.overtime_hours or 0.0) + ot_req.ot_hours, 2)
        att.ot_approved = True
        session.add(att)
    session.commit()


def get_my_overtime(session: Session, employee_id: int) -> list[OvertimeResponse]:
    rows = session.exec(
        select(OvertimeRequest)
        .where(OvertimeRequest.employee_id == employee_id)
        .order_by(OvertimeRequest.applied_at.desc())
    ).all()
    return [_format_overtime(session, r) for r in rows]


def get_pending_overtime(
    session: Session,
    reviewer_user: User,
    reviewer_emp: Optional[Employee],
) -> list[OvertimeResponse]:
    rows = session.exec(
        select(OvertimeRequest).where(
            OvertimeRequest.status.in_(["pending_manager", "pending_hr", "pending_leadership"])
        )
    ).all()
    filtered = filter_pending_for_reviewer(session, rows, reviewer_user, reviewer_emp)
    return [_format_overtime(session, r) for r in filtered]


def review_overtime(
    session: Session,
    req_id: int,
    review_data: OvertimeReviewRequest,
    reviewer_user: User,
    reviewer_emp: Optional[Employee],
) -> OvertimeResponse:
    ot_req = session.get(OvertimeRequest, req_id)
    if not ot_req:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Overtime request not found")

    req_emp = session.get(Employee, ot_req.employee_id)
    new_status, _ = process_tier_review(
        session=session,
        req_obj=ot_req,
        requester_emp=req_emp,
        reviewer_user=reviewer_user,
        reviewer_emp=reviewer_emp,
        raw_action=review_data.action,
        comments=review_data.comments,
        request_label="Overtime Claim",
    )
    session.add(ot_req)
    session.commit()
    session.refresh(ot_req)

    if new_status == "approved":
        _apply_approved_overtime(session, ot_req)

    return _format_overtime(session, ot_req)
