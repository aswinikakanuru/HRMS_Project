from sqlmodel import Session
from datetime import datetime, timezone
from models.notification import Notification

def send_notification(session: Session, user_id: int, title: str, message: str) -> Notification:
    """Create an in-app notification for a user."""
    notif = Notification(
        user_id=user_id,
        title=title,
        message=message,
        is_read=False,
        created_at=datetime.now(timezone.utc)
    )
    session.add(notif)
    session.commit()
    session.refresh(notif)
    return notif
