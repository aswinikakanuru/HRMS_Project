from pydantic import BaseModel, EmailStr, ConfigDict
from datetime import date
from typing import Optional

class EmployeeCreate(BaseModel):
    employee_code: str
    user_id: Optional[int] = None
    firstname: str
    lastname: str
    email: EmailStr
    phone: Optional[str] = None
    date_of_birth: Optional[date] = None
    joining_date: date
    department_id: int
    designation_id: int
    manager_id: Optional[int] = None
    employee_status: str = "active"

class EmployeeUpdate(BaseModel):
    firstname: Optional[str] = None
    lastname: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    date_of_birth: Optional[date] = None
    joining_date: Optional[date] = None
    department_id: Optional[int] = None
    designation_id: Optional[int] = None
    manager_id: Optional[int] = None
    employee_status: Optional[str] = None

class EmployeeResponse(BaseModel):
    id: int
    employee_code: str
    user_id: Optional[int] = None
    firstname: str
    lastname: str
    email: EmailStr
    phone: Optional[str] = None
    date_of_birth: Optional[date] = None
    joining_date: date
    department_id: int
    designation_id: int
    manager_id: Optional[int] = None
    employee_status: str

    model_config = ConfigDict(from_attributes=True)
