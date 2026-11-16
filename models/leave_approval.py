from sqlmodel import SQLModel, Field
from datetime import datetime
from typing import Optional

class LeaveApproval(SQLModel, table=True):
    __tablename__ = "leave_approvals"

    id: Optional[int] = Field(default=None, primary_key=True)
    leave_request_id: int = Field(foreign_key="leave_requests.id", index=True)
    approver_user_id: int = Field(foreign_key="users.id")
    approval_level: str = Field(default="manager")
    decision: str = Field(default="pending")
    comments: Optional[str] = None
    acted_at: Optional[datetime] = None
