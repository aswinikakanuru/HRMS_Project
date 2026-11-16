from fastapi import APIRouter, Depends, status
from sqlmodel import Session
from typing import Optional
from database import get_session
from schemas.designation import DesignationCreate, DesignationResponse
from dependencies.auth import get_current_user, require_roles
from services.designation_service import (
    create_designation as create_designation_service,
    get_all_designations,
    get_designation_by_id,
)

router = APIRouter(prefix="/designations", tags=["Designations"])

@router.post("/", response_model=DesignationResponse, status_code=status.HTTP_201_CREATED)
def create_designation(
    desig_data: DesignationCreate,
    session: Session = Depends(get_session),
    _: None = Depends(require_roles(["Admin", "HR"]))
):
    return create_designation_service(session, desig_data)

@router.get("/", response_model=list[DesignationResponse])
def list_designations(
    department_id: Optional[int] = None,
    session: Session = Depends(get_session),
    current_user = Depends(get_current_user)
):
    return get_all_designations(session, department_id)

@router.get("/{designation_id}", response_model=DesignationResponse)
def get_designation(
    designation_id: int,
    session: Session = Depends(get_session),
    current_user = Depends(get_current_user)
):
    return get_designation_by_id(session, designation_id)
