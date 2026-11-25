from typing import Optional
from datetime import date
from sqlmodel import SQLModel, Field


class Employee(SQLModel, table=True):
    __tablename__ = "employees"

    id: Optional[int] = Field(default=None, primary_key=True)
    employee_code: str = Field(unique=True, index=True)
    user_id: Optional[int] = Field(default=None, foreign_key="users.id", unique=True)
    firstname: str
    lastname: str
    email: str = Field(unique=True, index=True)
    phone: Optional[str] = None
    date_of_birth: Optional[date] = None
    joining_date: date
    department_id: int = Field(foreign_key="departments.id")
    designation_id: int = Field(foreign_key="designations.id")
    manager_id: Optional[int] = Field(default=None, foreign_key="employees.id")
    shift_id: Optional[int] = Field(default=None, foreign_key="shifts.id")
    employee_status: str = Field(default="active")
