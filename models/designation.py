from sqlmodel import SQLModel,Field
from typing import Optional

class Designation(SQLModel,table=True):
    __tablename__="designations"
    id:Optional[int]=Field(default=None,primary_key=True)
    title:str=Field(index=True)
    department_id:Optional[int]=Field(default=None,foreign_key="departments.id")
    description:Optional[str]=None