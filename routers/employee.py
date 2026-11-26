from typing import Optional
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlmodel import Session

from database import get_session
from dependencies.auth import get_current_employee, get_current_user, require_roles
from models.employee import Employee
from models.user import User
from schemas.employee import EmployeeCreate, EmployeeDirectoryItem, EmployeeResponse, EmployeeUpdate
from services.approval_service import get_visible_employee_ids
from services.employee_service import (
    create_employee as create_employee_service,
    delete_employee as delete_employee_service,
    format_employee,
    get_employee_by_id,
    get_scoped_employees,
    remove_my_profile_pic,
    search_company_directory,
    update_employee as update_employee_service,
    update_my_profile_pic,
)

router = APIRouter(prefix="/employees", tags=["Employees"])


@router.post("/", response_model=EmployeeResponse, status_code=status.HTTP_201_CREATED)
def create_employee(
    emp_data: EmployeeCreate,
    session: Session = Depends(get_session),
    _: User = Depends(require_roles(["Admin"])),
):
    """Only Admin can onboard new employees and create their login email & password."""
    return create_employee_service(session, emp_data)


@router.get("/me", response_model=EmployeeResponse)
def get_my_profile(
    session: Session = Depends(get_session),
    current_employee: Employee = Depends(get_current_employee),
):
    return format_employee(session, current_employee)


@router.post("/me/profile-pic", response_model=EmployeeResponse)
async def upload_my_profile_pic(
    file: UploadFile = File(...),
    session: Session = Depends(get_session),
    current_employee: Employee = Depends(get_current_employee),
):
    """Upload or replace the signed-in employee's optional profile picture."""
    file_bytes = await file.read()
    return update_my_profile_pic(
        session=session,
        emp=current_employee,
        file_bytes=file_bytes,
        content_type=file.content_type or "",
        filename=file.filename,
    )


@router.delete("/me/profile-pic", response_model=EmployeeResponse)
def delete_my_profile_pic(
    session: Session = Depends(get_session),
    current_employee: Employee = Depends(get_current_employee),
):
    """Remove the signed-in employee's profile picture."""
    return remove_my_profile_pic(session=session, emp=current_employee)


@router.get("/directory", response_model=list[EmployeeDirectoryItem])
def company_people_directory(
    q: Optional[str] = Query(None, description="Search anyone by name, EMP ID, email, role, or manager"),
    session: Session = Depends(get_session),
    _: User = Depends(get_current_user),
):
    """Global company directory search available to every logged-in employee."""
    return search_company_directory(session, q=q)


@router.get("/", response_model=list[EmployeeResponse])
def list_employees(
    q: Optional[str] = Query(None, description="Search employee name, code, email, department, or designation"),
    department_id: Optional[int] = Query(None, description="Filter by department"),
    manager_id: Optional[int] = Query(None, description="Filter by reporting manager"),
    scope: str = Query("auto", description="'assigned' or 'all' (CEO/HR/Admin only)"),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
    current_emp: Employee = Depends(get_current_employee),
):
    return get_scoped_employees(
        session=session,
        current_user=current_user,
        current_emp=current_emp,
        q=q,
        department_id=department_id,
        manager_id=manager_id,
        scope=scope,
    )


@router.get("/{employee_id}", response_model=EmployeeResponse)
def get_employee(
    employee_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
    current_emp: Employee = Depends(get_current_employee),
):
    visible_ids = get_visible_employee_ids(session, current_user, current_emp)
    if visible_ids is not None and employee_id not in visible_ids:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view employees assigned to your team/department.",
        )
    return get_employee_by_id(session, employee_id)


@router.put("/{employee_id}", response_model=EmployeeResponse)
def update_employee(
    employee_id: int,
    emp_data: EmployeeUpdate,
    session: Session = Depends(get_session),
    _: User = Depends(require_roles(["Admin"])),
):
    return update_employee_service(session, employee_id, emp_data)


@router.delete("/{employee_id}")
def delete_employee(
    employee_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_roles(["Admin"])),
):
    """Only Admin can delete an employee and revoke their login access."""
    return delete_employee_service(session, employee_id, current_user)
