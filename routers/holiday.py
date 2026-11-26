from fastapi import APIRouter, Depends, status
from sqlmodel import Session
from database import get_session
from models.user import User
from schemas.holiday import HolidayCreate, HolidayResponse
from dependencies.auth import get_current_user, require_roles
from services.holiday_service import (
    create_holiday as create_holiday_service,
    get_all_holidays,
    delete_holiday as delete_holiday_service,
)

router = APIRouter(prefix="/holidays", tags=["Holidays"])

# 1. Add a Holiday 
@router.post("/", response_model=HolidayResponse, status_code=status.HTTP_201_CREATED)
def create_holiday(
    holiday_data: HolidayCreate,
    session: Session = Depends(get_session),
    _: User = Depends(require_roles(["Admin", "HR", "Leadership"]))
):
    return create_holiday_service(session, holiday_data)

# 2. View All Upcoming Holidays 
@router.get("/", response_model=list[HolidayResponse])
def list_holidays(
    session: Session = Depends(get_session),
    _: User = Depends(get_current_user)
):
    return get_all_holidays(session)

# 3. Delete a Holiday 
@router.delete("/{holiday_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_holiday(
    holiday_id: int,
    session: Session = Depends(get_session),
    _: User = Depends(require_roles(["Admin", "HR", "Leadership"]))
):
    delete_holiday_service(session, holiday_id)
    return None
