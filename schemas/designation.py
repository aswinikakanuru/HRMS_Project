from pydantic import BaseModel,ConfigDict
from typing import Optional

class DesignationCreate(BaseModel):
    title:str
    department_id: Optional[int]=None
    description:Optional[str]=None

class DesignationUpdate(BaseModel):
    title:Optional[str]=None
    department_id: Optional[int] = None
    description:Optional[str]=None
  

class DesignationResponse(BaseModel):
    id:int
    title:str
    department_id:Optional[int]=None
    description:Optional[str]=None
    model_config=ConfigDict(from_attributes=True)