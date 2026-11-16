from typing import Optional
from datetime import datetime
from pydantic import BaseModel,ConfigDict

class DepartmentCreate(BaseModel):
    name:str
    description:Optional[str]=None

class DepartmentUpdate(BaseModel):
    name:Optional[str]=None
    description:Optional[str]=None
    is_active:Optional[bool]=None

class DepartmentResponse(BaseModel):
    id:int
    name:str
    description:Optional[str]=None
    is_active:bool
    model_config=ConfigDict(from_attributes=True)


