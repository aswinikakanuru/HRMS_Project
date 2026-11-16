from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime

class NotificationCreate(BaseModel):
    user_id: int
    title: str
    message: str

class NotificationUpdate(BaseModel):
    is_read: Optional[bool] = None

class NotificationResponse(BaseModel):
    id: int
    user_id: int
    title: str
    message: str
    is_read: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
