from uuid import UUID
from fastapi import APIRouter, Depends
from fastapi.exceptions import HTTPException
from sqlalchemy.orm.session import Session
from digirent.database.models import (
    Notification,
    User,
)
from .schema import NotificationSchema, PaginatedNotificationSchema
import digirent.api.dependencies as dependencies


router = APIRouter()


@router.get("/", response_model=PaginatedNotificationSchema)
def fetch_user_notifications(
    page: int,
    page_size: int,
    session: Session = Depends(dependencies.get_database_session),
    user: User = Depends(dependencies.get_current_active_user),
):
    """Fetch notifications of a particular user in descending order"""
    offset = (page - 1) * page_size
    limit = page_size
    notifications_query = session.query(Notification).filter(
        Notification.user_id == user.id
    )
    count = notifications_query.count()
    notifications_query = notifications_query.order_by(Notification.created_at.desc())
    notifications_query = notifications_query.offset(offset).limit(limit)
    data = notifications_query.all()
    return {"page": page, "page_size": page_size, "count": count, "data": data}


@router.post("/{notification_id}/read", response_model=NotificationSchema)
def mark_as_read(
    notification_id: UUID,
    session: Session = Depends(dependencies.get_database_session),
    user: User = Depends(dependencies.get_current_active_user),
):
    """Mark user notification as read"""
    notification = (
        session.query(Notification)
        .filter(Notification.id == notification_id)
        .filter(Notification.user_id == user.id)
        .one_or_none()
    )
    if notification is None:
        raise HTTPException(404, "Not found")
    if notification.is_read:
        raise HTTPException(400, "Notification already marked as read")
    notification.is_read = True
    session.commit()
