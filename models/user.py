from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime, timezone


class User(SQLModel, table=True):
    __tablename__ = "users"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    email: str = Field(unique=True, index=True)
    hashed_password: str
    # 5 Roles: Leadership (CEO / Director), Admin, Manager, HR, Employee
    role: str = Field(default="Employee")
    leadership_title: Optional[str] = Field(default=None)  # e.g., "CEO", "Director"
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
