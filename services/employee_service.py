from typing import Optional
from fastapi import HTTPException, status
from sqlmodel import Session, select

from models.department import Department
from models.designation import Designation
from models.employee import Employee
from models.shift import Shift
from models.user import User
from schemas.employee import EmployeeCreate, EmployeeResponse, EmployeeUpdate
from services.approval_service import get_visible_employee_ids


def format_employee(session: Session, emp: Employee) -> EmployeeResponse:
    dept = session.get(Department, emp.department_id) if emp.department_id else None
    desig = session.get(Designation, emp.designation_id) if emp.designation_id else None
    mgr = session.get(Employee, emp.manager_id) if emp.manager_id else None
    shift = session.get(Shift, emp.shift_id) if emp.shift_id else None
    user = session.get(User, emp.user_id) if emp.user_id else None

    return EmployeeResponse(
        id=emp.id,
        employee_code=emp.employee_code,
        user_id=emp.user_id,
        firstname=emp.firstname,
        lastname=emp.lastname,
        email=emp.email,
        phone=emp.phone,
        date_of_birth=emp.date_of_birth,
        joining_date=emp.joining_date,
        department_id=emp.department_id,
        designation_id=emp.designation_id,
        manager_id=emp.manager_id,
        shift_id=emp.shift_id,
        department_name=dept.name if dept else None,
        designation_title=desig.title if desig else None,
        manager_name=f"{mgr.firstname} {mgr.lastname}".strip() if mgr else None,
        shift_name=shift.name if shift else "General Shift",
        role=user.role if user else "Employee",
        leadership_title=user.leadership_title if user else None,
        employee_status=emp.employee_status,
    )


def create_employee(session: Session, emp_data: EmployeeCreate) -> EmployeeResponse:
    from services.auth_service import hash_password

    clean_email = emp_data.email.strip().lower()
    if session.exec(select(Employee).where(Employee.employee_code == emp_data.employee_code)).first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Employee code already in use")

    if session.exec(select(Employee).where(Employee.email == clean_email)).first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Employee email already in use")

    if session.exec(select(User).where(User.email == clean_email)).first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="A user account with this email already exists")

    if not session.get(Department, emp_data.department_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Department does not exist")

    if not session.get(Designation, emp_data.designation_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Designation does not exist")

    allowed_roles = ["Employee", "Manager", "HR", "Admin", "Leadership"]
    user_role = emp_data.role if emp_data.role in allowed_roles else "Employee"
    leadership_title = emp_data.leadership_title if user_role == "Leadership" else None

    new_user = User(
        name=f"{emp_data.firstname.strip()} {emp_data.lastname.strip()}".strip(),
        email=clean_email,
        hashed_password=hash_password(emp_data.password),
        role=user_role,
        leadership_title=leadership_title,
        is_active=True,
    )
    session.add(new_user)
    session.commit()
    session.refresh(new_user)

    shift_id = emp_data.shift_id
    if not shift_id:
        gs = session.exec(select(Shift).where(Shift.code == "GS")).first()
        if gs:
            shift_id = gs.id

    new_emp = Employee(
        employee_code=emp_data.employee_code.strip().upper(),
        user_id=new_user.id,
        firstname=emp_data.firstname.strip(),
        lastname=emp_data.lastname.strip(),
        email=clean_email,
        phone=emp_data.phone,
        date_of_birth=emp_data.date_of_birth,
        joining_date=emp_data.joining_date,
        department_id=emp_data.department_id,
        designation_id=emp_data.designation_id,
        manager_id=emp_data.manager_id,
        shift_id=shift_id,
        employee_status=emp_data.employee_status,
    )
    session.add(new_emp)
    session.commit()
    session.refresh(new_emp)
    return format_employee(session, new_emp)


def get_scoped_employees(
    session: Session,
    current_user: User,
    current_emp: Optional[Employee],
    q: Optional[str] = None,
    department_id: Optional[int] = None,
    manager_id: Optional[int] = None,
    scope: str = "auto",
) -> list[EmployeeResponse]:
    """
    List & search employees strictly scoped to assigned hierarchy:
    - Manager: Only assigned direct reports (+ self)
    - Employee: Only teammates under same manager (+ self)
    - Director (non-CEO Leadership): Direct reports + indirect reports + department
    - CEO / HR / Admin: All departments & managers (or 'assigned' for direct reports)
    """
    visible_ids = get_visible_employee_ids(session, current_user, current_emp)

    query = select(Employee)
    if visible_ids is not None:
        if not visible_ids:
            return []
        query = query.where(Employee.id.in_(visible_ids))
    elif scope == "assigned" and current_emp:
        query = query.where((Employee.manager_id == current_emp.id) | (Employee.id == current_emp.id))

    if department_id:
        query = query.where(Employee.department_id == department_id)
    if manager_id:
        query = query.where(Employee.manager_id == manager_id)

    emps = session.exec(query.order_by(Employee.firstname, Employee.lastname)).all()
    formatted = [format_employee(session, e) for e in emps]

    if q:
        term = q.strip().lower()
        formatted = [
            item for item in formatted
            if term in f"{item.firstname} {item.lastname}".lower()
            or term in (item.employee_code or "").lower()
            or term in (item.email or "").lower()
            or term in (item.department_name or "").lower()
            or term in (item.designation_title or "").lower()
            or term in (item.manager_name or "").lower()
            or term in (item.role or "").lower()
        ]

    return formatted


def get_all_employees(session: Session) -> list[EmployeeResponse]:
    emps = session.exec(select(Employee)).all()
    return [format_employee(session, e) for e in emps]


def get_employee_by_id(session: Session, employee_id: int) -> EmployeeResponse:
    emp = session.get(Employee, employee_id)
    if not emp:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")
    return format_employee(session, emp)


def get_employee_by_user_id(session: Session, user_id: int) -> Employee:
    emp = session.exec(select(Employee).where(Employee.user_id == user_id)).first()
    if not emp:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No employee profile linked to this user account")
    return emp


def update_employee(session: Session, employee_id: int, emp_data: EmployeeUpdate) -> EmployeeResponse:
    emp = session.get(Employee, employee_id)
    if not emp:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")
    update_dict = emp_data.model_dump(exclude_unset=True)
    for key, value in update_dict.items():
        setattr(emp, key, value)
    session.add(emp)
    session.commit()
    session.refresh(emp)
    return format_employee(session, emp)


def delete_employee(session: Session, employee_id: int, current_user: User) -> dict:
    """Admin-only deletion of an employee and their login account + dependent records."""
    from models.attendance import Attendance
    from models.leave_approval import LeaveApproval
    from models.leave_request import LeaveRequest
    from models.notification import Notification
    from models.overtime_request import OvertimeRequest
    from models.regularisation_request import RegularisationRequest
    from models.wfh_request import WFHRequest

    emp = session.get(Employee, employee_id)
    if not emp:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")

    if emp.user_id and emp.user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot delete your own active Admin account.",
        )

    # Clear reporting manager pointers from any direct reports
    for sub in session.exec(select(Employee).where(Employee.manager_id == emp.id)).all():
        sub.manager_id = None
        session.add(sub)
    session.commit()

    # Delete leave approvals referencing this employee's leave requests or user
    emp_leave_ids = [
        lr.id for lr in session.exec(select(LeaveRequest).where(LeaveRequest.employee_id == emp.id)).all()
    ]
    if emp_leave_ids:
        for la in session.exec(select(LeaveApproval).where(LeaveApproval.leave_request_id.in_(emp_leave_ids))).all():
            session.delete(la)
    if emp.user_id:
        for la in session.exec(select(LeaveApproval).where(LeaveApproval.approver_user_id == emp.user_id)).all():
            session.delete(la)

    for model in (Attendance, LeaveRequest, WFHRequest, RegularisationRequest, OvertimeRequest):
        for row in session.exec(select(model).where(model.employee_id == emp.id)).all():
            session.delete(row)

    linked_user_id = emp.user_id
    if linked_user_id:
        for n in session.exec(select(Notification).where(Notification.user_id == linked_user_id)).all():
            session.delete(n)

    deleted_name = f"{emp.firstname} {emp.lastname}".strip()
    session.delete(emp)
    session.commit()

    if linked_user_id:
        u = session.get(User, linked_user_id)
        if u:
            session.delete(u)
            session.commit()

    return {"message": f"Deleted employee {deleted_name} and login access."}
