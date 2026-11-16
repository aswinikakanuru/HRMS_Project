from sqlmodel import SQLModel,Field
from typing import Optional

class LeaveType(SQLModel,table=True):
    __tablename__="leave_types"
    id:Optional[int]=Field(default=None,primary_key=True)
    name:str=Field(unique=True,index=True)
    annual_quota:int=Field(default=0)
    description:Optional[str]=None
    is_active:bool=Field(default=True)
