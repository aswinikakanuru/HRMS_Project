from datetime import date, datetime, timedelta, timezone
from fastapi import APIRouter, Depends
from sqlmodel import Session, func, select

from database import get_session
from dependencies.auth import get_current_employee, get_current_user, require_roles
from models.attendance import Attendance
from models.department import Department
from models.designation import Designation
from models.employee import Employee
from models.leave_request import LeaveRequest
from models.notification import Notification
from models.overtime_request import OvertimeRequest
from models.regularisation_request import RegularisationRequest
from models.shift import Shift
from models.user import User
from models.wfh_request import WFHRequest
from services.approval_service import filter_pending_for_reviewer

IST = timezone(timedelta(hours=5, minutes=30))

router = APIRouter(prefix="/dashboard", tags=["Dashboard & Analytics"])


@router.get("/overview")
def get_admin_dashboard(
    session: Session = Depends(get_session),
    current_user: User = Depends(require_roles(["Leadership", "Admin", "HR", "Manager"])),
    current_emp: Employee = Depends(get_current_employee),
):
    today = datetime.now(IST).date()

    total_employees = session.exec(select(func.count(Employee.id))).one()
    total_departments = session.exec(select(func.count(Department.id))).one()
    present_today = session.exec(
        select(func.count(Attendance.id)).where(Attendance.attendance_date == today)
    ).one()

    leaves = filter_pending_for_reviewer(
        session,
        session.exec(select(LeaveRequest).where(LeaveRequest.status.in_(["pending_manager", "pending_hr", "pending_leadership"]))).all(),
        current_user,
        current_emp,
    )
    wfhs = filter_pending_for_reviewer(
        session,
        session.exec(select(WFHRequest).where(WFHRequest.status.in_(["pending_manager", "pending_hr", "pending_leadership"]))).all(),
        current_user,
        current_emp,
    )
    regs = filter_pending_for_reviewer(
        session,
        session.exec(select(RegularisationRequest).where(RegularisationRequest.status.in_(["pending_manager", "pending_hr", "pending_leadership"]))).all(),
        current_user,
        current_emp,
    )
    ots = filter_pending_for_reviewer(
        session,
        session.exec(select(OvertimeRequest).where(OvertimeRequest.status.in_(["pending_manager", "pending_hr", "pending_leadership"]))).all(),
        current_user,
        current_emp,
    )

    return {
        "today_date": str(today),
        "total_employees": total_employees,
        "total_departments": total_departments,
        "today_attendance": {
            "present": present_today,
            "absent": max(0, total_employees - present_today),
        },
        "attendance_today": {
            "present_count": present_today,
            "absent_count": max(0, total_employees - present_today),
        },
        "pending_approvals": {
            "leaves": len(leaves),
            "wfh": len(wfhs),
            "regularisations": len(regs),
            "overtime": len(ots),
            "total": len(leaves) + len(wfhs) + len(regs) + len(ots),
        },
        "pending_actions": {
            "leaves_to_review": len(leaves),
            "wfh_to_review": len(wfhs),
            "regularisations_to_review": len(regs),
            "overtime_to_review": len(ots),
            "total_pending": len(leaves) + len(wfhs) + len(regs) + len(ots),
        },
    }


@router.get("/my-summary")
def get_employee_dashboard(
    session: Session = Depends(get_session),
    employee: Employee = Depends(get_current_employee),
    current_user: User = Depends(get_current_user),
):
    today = datetime.now(IST).date()

    attendance = session.exec(
        select(Attendance).where(
            Attendance.employee_id == employee.id,
            Attendance.attendance_date == today,
        )
    ).first()

    pending_statuses = ["pending_manager", "pending_hr", "pending_leadership"]
    my_pending_leaves = session.exec(
        select(func.count(LeaveRequest.id)).where(
            LeaveRequest.employee_id == employee.id,
            LeaveRequest.status.in_(pending_statuses),
        )
    ).one()

    my_pending_wfh = session.exec(
        select(func.count(WFHRequest.id)).where(
            WFHRequest.employee_id == employee.id,
            WFHRequest.status.in_(pending_statuses),
        )
    ).one()

    my_pending_regs = session.exec(
        select(func.count(RegularisationRequest.id)).where(
            RegularisationRequest.employee_id == employee.id,
            RegularisationRequest.status.in_(pending_statuses),
        )
    ).one()

    my_pending_ot = session.exec(
        select(func.count(OvertimeRequest.id)).where(
            OvertimeRequest.employee_id == employee.id,
            OvertimeRequest.status.in_(pending_statuses),
        )
    ).one()

    unread_notifs = session.exec(
        select(func.count(Notification.id)).where(
            Notification.user_id == current_user.id,
            Notification.is_read == False,
        )
    ).one()

    dept = session.get(Department, employee.department_id) if employee.department_id else None
    desig = session.get(Designation, employee.designation_id) if employee.designation_id else None
    mgr = session.get(Employee, employee.manager_id) if employee.manager_id else None
    shift = session.get(Shift, employee.shift_id) if employee.shift_id else session.exec(select(Shift).where(Shift.code == "GS")).first()

    att_hours = 0.0
    if attendance:
        att_hours = attendance.work_hours or 0.0
        if attendance.check_in and attendance.check_out and att_hours == 0.0:
            p_in = attendance.check_in if attendance.check_in.tzinfo else attendance.check_in.replace(tzinfo=IST)
            p_out = attendance.check_out if attendance.check_out.tzinfo else attendance.check_out.replace(tzinfo=IST)
            att_hours = round(max(0.0, (p_out - p_in).total_seconds() / 3600.0), 2)

    return {
        "employee_id": employee.id,
        "employee_code": employee.employee_code,
        "employee_name": f"{employee.firstname} {employee.lastname}".strip(),
        "employee_email": employee.email,
        "department": dept.name if dept else "Engineering",
        "designation": desig.title if desig else "Software Engineer",
        "manager_name": f"{mgr.firstname} {mgr.lastname}".strip() if mgr else None,
        "manager_email": mgr.email if mgr else None,
        "role": current_user.role,
        "leadership_title": current_user.leadership_title,
        "shift": {
            "id": shift.id,
            "name": shift.name,
            "code": shift.code,
            "start_time": shift.start_time,
            "end_time": shift.end_time,
            "grace_period_mins": shift.grace_period_mins,
            "full_day_hours": shift.full_day_hours,
        } if shift else {"name": "General Shift", "start_time": "09:00", "end_time": "18:00"},
        "today_attendance": {
            "clocked_in": attendance.check_in is not None if attendance else False,
            "check_in": attendance.check_in if attendance else None,
            "check_out": attendance.check_out if attendance else None,
            "work_hours": att_hours,
            "status": "Present" if (attendance and attendance.check_in) else "Absent",
            "is_late": attendance.is_late if attendance else False,
            "late_minutes": attendance.late_minutes if attendance else 0,
            "is_regularised": attendance.is_regularised if attendance else False,
            "remarks": attendance.remarks if attendance else None,
        },
        "pending_requests": {
            "leaves": my_pending_leaves,
            "wfh": my_pending_wfh,
            "regularisations": my_pending_regs,
            "overtime": my_pending_ot,
        },
        "unread_notifications": unread_notifs,
    }
