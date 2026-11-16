from sqlmodel import Session, select
from fastapi import HTTPException, status
from models.department import Department
from schemas.department import DepartmentCreate, DepartmentUpdate

def create_department(session: Session, dept_data: DepartmentCreate) -> Department:
    existing = session.exec(select(Department).where(Department.name == dept_data.name)).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Department already exists")
    
    dept = Department(**dept_data.model_dump())
    session.add(dept)
    session.commit()
    session.refresh(dept)
    return dept

def get_all_departments(session: Session) -> list[Department]:
    return session.exec(select(Department)).all()

def get_department_by_id(session: Session, department_id: int) -> Department:
    dept = session.get(Department, department_id)
    if not dept:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Department not found")
    return dept

def update_department(session: Session, department_id: int, dept_data: DepartmentUpdate) -> Department:
    dept = get_department_by_id(session, department_id)
    update_dict = dept_data.model_dump(exclude_unset=True)
    for key, value in update_dict.items():
        setattr(dept, key, value)
    session.add(dept)
    session.commit()
    session.refresh(dept)
    return dept
