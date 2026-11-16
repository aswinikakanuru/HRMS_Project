from sqlmodel import Session, select
from typing import Optional
from fastapi import HTTPException, status
from models.designation import Designation
from models.department import Department
from schemas.designation import DesignationCreate

def create_designation(session: Session, desig_data: DesignationCreate) -> Designation:
    if desig_data.department_id:
        dept = session.get(Department, desig_data.department_id)
        if not dept:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Department does not exist")

    desig = Designation(**desig_data.model_dump())
    session.add(desig)
    session.commit()
    session.refresh(desig)
    return desig

def get_all_designations(session: Session, department_id: Optional[int] = None) -> list[Designation]:
    query = select(Designation)
    if department_id:
        query = query.where(Designation.department_id == department_id)
    return session.exec(query).all()

def get_designation_by_id(session: Session, designation_id: int) -> Designation:
    desig = session.get(Designation, designation_id)
    if not desig:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Designation not found")
    return desig
