from sqlmodel import SQLModel,Field
from datetime import datetime,date
from typing import Optional
from sqlalchemy import UniqueConstraint

class Attendance(SQLModel,table=True):
    __tablename__="attendance"

    __table_args__ = (
        UniqueConstraint(
            "employee_id",
            "attendance_date",
            name="unique_employee_attendance"
        ),
    )
    id:Optional[int]=Field(default=None,primary_key=True)
    employee_id:int=Field(foreign_key="employees.id",index=True)
    attendance_date:date
    check_in:Optional[datetime]=None
    check_out:Optional[datetime]=None
    status:str=Field(default="present")
    remarks:Optional[str]=None

