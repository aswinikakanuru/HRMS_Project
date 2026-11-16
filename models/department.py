from sqlmodel import SQLModel,Field
from typing import Optional
class Department(SQLModel,table=True):
    __tablename__="departments"
    id:Optional[int]=Field(default=None,primary_key=True)
    name:str=Field(unique=True,index=True)
    description:Optional[str]=None
    is_active:bool=Field(default=True)
    