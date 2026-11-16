from fastapi import APIRouter, Depends
from sqlmodel import Session, select, func
from datetime import date
from database import get_session
from models.employee import Employee
from models.department import Department
from models.attendance import Attendance
from models.leave_request import LeaveRequest
from models.wfh_request import WFHRequest
from models.notification import Notification
from models.user import User
from dependencies.auth import get_current_user, get_current_employee, require_roles

router = APIRouter(prefix="/dashboard", tags=["Dashboard & Analytics"])

# 1. Admin & HR Executive Overview
@router.get("/overview")
def get_admin_dashboard(
    session: Session = Depends(get_session),
    _: User = Depends(require_roles(["Admin", "HR", "Manager"]))
):
    today = date.today()

    total_employees = session.exec(select(func.count(Employee.id))).one()
    total_departments = session.exec(select(func.count(Department.id))).one()
    
    # Today's attendance
    present_today = session.exec(
        select(func.count(Attendance.id)).where(Attendance.attendance_date == today)
    ).one()

    # Pending approvals
    pending_leaves = session.exec(
        select(func.count(LeaveRequest.id)).where(LeaveRequest.status == "pending_manager")
    ).one()

    pending_wfh = session.exec(
        select(func.count(WFHRequest.id)).where(WFHRequest.status == "pending_manager")
    ).one()

    return {
        "today_date": str(today),
        "total_employees": total_employees,
        "total_departments": total_departments,
        "attendance_today": {
            "present_count": present_today,
            "absent_count": max(0, total_employees - present_today),
        },
        "pending_actions": {
            "leaves_to_review": pending_leaves,
            "wfh_to_review": pending_wfh,
            "total_pending": pending_leaves + pending_wfh
        }
    }

# 2. Employee Personal Self-Service Summary
@router.get("/my-summary")
def get_employee_dashboard(
    session: Session = Depends(get_session),
    employee: Employee = Depends(get_current_employee),
    current_user: User = Depends(get_current_user)
):
    today = date.today()

    # Today's clock-in status
    attendance = session.exec(
        select(Attendance).where(
            Attendance.employee_id == employee.id,
            Attendance.attendance_date == today
        )
    ).first()

    # Pending leaves count
    my_pending_leaves = session.exec(
        select(func.count(LeaveRequest.id)).where(
            LeaveRequest.employee_id == employee.id,
            LeaveRequest.status == "pending_manager"
        )
    ).one()

    # Pending WFH count
    my_pending_wfh = session.exec(
        select(func.count(WFHRequest.id)).where(
            WFHRequest.employee_id == employee.id,
            WFHRequest.status == "pending_manager"
        )
    ).one()

    # Unread notifications count
    unread_notifs = session.exec(
        select(func.count(Notification.id)).where(
            Notification.user_id == current_user.id,
            Notification.is_read == False
        )
    ).one()

    return {
        "employee_name": f"{employee.firstname} {employee.lastname}",
        "employee_code": employee.employee_code,
        "today_attendance": {
            "clocked_in": attendance.check_in is not None if attendance else False,
            "check_in": attendance.check_in if attendance else None,
            "check_out": attendance.check_out if attendance else None,
            "status": attendance.status if attendance else "not_clocked_in"
        },
        "pending_requests": {
            "leaves": my_pending_leaves,
            "wfh": my_pending_wfh
        },
        "unread_notifications": unread_notifs
    }
