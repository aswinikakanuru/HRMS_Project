from pydantic import BaseModel,ConfigDict
from typing import Optional
from datetime import date,datetime

class WFHApplyRequest(BaseModel):
    start_date:date
    end_date:date
    reason:str

class WFHReviewRequest(BaseModel):
    action:str
    comments: Optional[str] = None

class WFHResponse(BaseModel):
    id:int
    employee_id:int
    start_date:date
    end_date:date
    reason:str
    status:str
    applied_at:datetime

    model_config=ConfigDict(from_attributes=True)