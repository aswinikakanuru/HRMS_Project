from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from database import get_session
from models.notification import Notification
from models.user import User
from schemas.notification import NotificationResponse
from dependencies.auth import get_current_user

router = APIRouter(prefix="/notifications", tags=["Notifications"])

# 1. Get Logged-in User's Notifications
@router.get("/", response_model=list[NotificationResponse])
def get_my_notifications(
    unread_only: bool = False,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    query = select(Notification).where(Notification.user_id == current_user.id)
    if unread_only:
        query = query.where(Notification.is_read == False)
    query = query.order_by(Notification.created_at.desc())
    return session.exec(query).all()

# 2. Mark a Notification as Read
@router.patch("/{notification_id}/read", response_model=NotificationResponse)
def mark_as_read(
    notification_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    notif = session.get(Notification, notification_id)
    if not notif or notif.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")

    notif.is_read = True
    session.add(notif)
    session.commit()
    session.refresh(notif)
    return notif

# 3. Mark All Notifications as Read
@router.patch("/read-all", response_model=dict)
def mark_all_as_read(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    query = select(Notification).where(
        Notification.user_id == current_user.id,
        Notification.is_read == False
    )
    unread_notifications = session.exec(query).all()
    for notif in unread_notifications:
        notif.is_read = True
        session.add(notif)

    session.commit()
    return {"message": f"Marked {len(unread_notifications)} notifications as read."}
