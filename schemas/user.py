from pydantic import BaseModel, EmailStr, ConfigDict, Field
from datetime import datetime

class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)

class UserResponse(BaseModel):
    id: int
    name: str
    email: EmailStr
    role: str
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
