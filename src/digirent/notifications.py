from typing import Union, Optional
from uuid import UUID
from sqlalchemy.orm.session import Session
from fastapi import WebSocket
from digirent.database.models import Notification
from digirent.database.enums import NotificationType
from digirent.database.base import with_db_session


@with_db_session
async def store_and_broadcast_notification(
    websocket: Optional[WebSocket],
    user_id: UUID,
    notification_type: NotificationType,
    data: Union[list, dict],
    session: Session = None,
):
    notification = Notification(
        user_id=user_id, is_read=False, type=notification_type, data=data
    )
    session.add(notification)
    session.commit()
    if websocket:
        await websocket.send_json(
            {
                "eventType": "NOTIFICATION",
                "data": {
                    "notificationType": notification_type.value,
                    "created_at": str(notification.created_at),
                    "payload": data,
                },
            }
        )
