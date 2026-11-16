from fastapi import APIRouter, Depends, status
from sqlmodel import Session
from database import get_session
from models.employee import Employee
from schemas.employee import EmployeeCreate, EmployeeUpdate, EmployeeResponse
from dependencies.auth import get_current_user, get_current_employee, require_roles
from services.employee_service import (
    create_employee as create_employee_service,
    get_all_employees,
    get_employee_by_id,
    update_employee as update_employee_service,
)

router = APIRouter(prefix="/employees", tags=["Employees"])

@router.post("/", response_model=EmployeeResponse, status_code=status.HTTP_201_CREATED)
def create_employee(
    emp_data: EmployeeCreate,
    session: Session = Depends(get_session),
    _: None = Depends(require_roles(["Admin", "HR"]))
):
    return create_employee_service(session, emp_data)

@router.get("/me", response_model=EmployeeResponse)
def get_my_profile(current_employee: Employee = Depends(get_current_employee)):
    return current_employee

@router.get("/", response_model=list[EmployeeResponse])
def list_employees(
    session: Session = Depends(get_session),
    current_user = Depends(get_current_user)
):
    return get_all_employees(session)

@router.get("/{employee_id}", response_model=EmployeeResponse)
def get_employee(
    employee_id: int,
    session: Session = Depends(get_session),
    current_user = Depends(get_current_user)
):
    return get_employee_by_id(session, employee_id)

@router.put("/{employee_id}", response_model=EmployeeResponse)
def update_employee(
    employee_id: int,
    emp_data: EmployeeUpdate,
    session: Session = Depends(get_session),
    _: None = Depends(require_roles(["Admin", "HR"]))
):
    return update_employee_service(session, employee_id, emp_data)
