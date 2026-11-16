from sqlmodel import Session, select
from fastapi import HTTPException, status
from models.employee import Employee
from models.department import Department
from models.designation import Designation
from schemas.employee import EmployeeCreate, EmployeeUpdate

def create_employee(session: Session, emp_data: EmployeeCreate) -> Employee:
    # Check duplicate code or email
    if session.exec(select(Employee).where(Employee.employee_code == emp_data.employee_code)).first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Employee code already in use")

    if session.exec(select(Employee).where(Employee.email == emp_data.email)).first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Employee email already in use")

    # Check department & designation exist
    if not session.get(Department, emp_data.department_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Department does not exist")

    if not session.get(Designation, emp_data.designation_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Designation does not exist")

    # If linking to user_id, check it's not already linked
    if emp_data.user_id:
        if session.exec(select(Employee).where(Employee.user_id == emp_data.user_id)).first():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User account is already linked to another employee")

    new_emp = Employee(**emp_data.model_dump())
    session.add(new_emp)
    session.commit()
    session.refresh(new_emp)
    return new_emp

def get_all_employees(session: Session) -> list[Employee]:
    return session.exec(select(Employee)).all()

def get_employee_by_id(session: Session, employee_id: int) -> Employee:
    emp = session.get(Employee, employee_id)
    if not emp:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")
    return emp

def get_employee_by_user_id(session: Session, user_id: int) -> Employee:
    emp = session.exec(select(Employee).where(Employee.user_id == user_id)).first()
    if not emp:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No employee profile linked to this user account")
    return emp

def update_employee(session: Session, employee_id: int, emp_data: EmployeeUpdate) -> Employee:
    emp = get_employee_by_id(session, employee_id)
    update_dict = emp_data.model_dump(exclude_unset=True)
    for key, value in update_dict.items():
        setattr(emp, key, value)
    session.add(emp)
    session.commit()
    session.refresh(emp)
    return emp
