from pydantic import BaseModel,ConfigDict
from typing import Optional
from datetime import date,datetime

class AttendanceCreate(BaseModel):
    employee_id:int
    attendance_date:date
    check_in:Optional[datetime]=None
    check_out:Optional[datetime]=None
    status:str="present"
    remarks: Optional[str] = None

class AttendanceUpdate(BaseModel):
    check_in:Optional[datetime]=None
    check_out:Optional[datetime]=None
    status:Optional[str]=None
    remarks: Optional[str] = None

class AttendanceResponse(BaseModel):
    id:int
    employee_id:int
    attendance_date:date
    check_in:Optional[datetime]=None
    check_out:Optional[datetime]=None
    status:str
    remarks: Optional[str] = None

    model_config=ConfigDict(from_attributes=True)

class AttendanceClockResponse(BaseModel):
    action:str
    attendance:AttendanceResponse
