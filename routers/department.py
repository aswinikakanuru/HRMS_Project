from fastapi import APIRouter, Depends, status
from sqlmodel import Session
from database import get_session
from schemas.department import DepartmentCreate, DepartmentUpdate, DepartmentResponse
from dependencies.auth import get_current_user, require_roles
from services.department_service import (
    create_department as create_department_service,
    get_all_departments,
    get_department_by_id,
    update_department as update_department_service,
)

router = APIRouter(prefix="/departments", tags=["Departments"])

@router.post("/", response_model=DepartmentResponse, status_code=status.HTTP_201_CREATED)
def create_department(
    dept_data: DepartmentCreate,
    session: Session = Depends(get_session),
    _: None = Depends(require_roles(["Admin", "HR"]))
):
    return create_department_service(session, dept_data)

@router.get("/", response_model=list[DepartmentResponse])
def list_departments(
    session: Session = Depends(get_session),
    current_user = Depends(get_current_user)
):
    return get_all_departments(session)

@router.get("/{department_id}", response_model=DepartmentResponse)
def get_department(
    department_id: int,
    session: Session = Depends(get_session),
    current_user = Depends(get_current_user)
):
    return get_department_by_id(session, department_id)

@router.put("/{department_id}", response_model=DepartmentResponse)
def update_department(
    department_id: int,
    dept_data: DepartmentUpdate,
    session: Session = Depends(get_session),
    _: None = Depends(require_roles(["Admin", "HR"]))
):
    return update_department_service(session, department_id, dept_data)
