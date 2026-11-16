from sqlmodel import Session, select
from fastapi import HTTPException, status
from models.holiday import Holiday
from schemas.holiday import HolidayCreate

def create_holiday(session: Session, holiday_data: HolidayCreate) -> Holiday:
    existing = session.exec(select(Holiday).where(Holiday.holiday_date == holiday_data.holiday_date)).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="A holiday is already scheduled for this date.")

    new_holiday = Holiday(**holiday_data.model_dump())
    session.add(new_holiday)
    session.commit()
    session.refresh(new_holiday)
    return new_holiday

def get_all_holidays(session: Session) -> list[Holiday]:
    return session.exec(select(Holiday).order_by(Holiday.holiday_date.asc())).all()

def delete_holiday(session: Session, holiday_id: int) -> None:
    holiday = session.get(Holiday, holiday_id)
    if not holiday:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Holiday not found")
    session.delete(holiday)
    session.commit()
