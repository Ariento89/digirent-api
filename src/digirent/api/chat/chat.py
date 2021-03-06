from collections import OrderedDict
import enum
from uuid import UUID
from fastapi.websockets import WebSocket
from pydantic import BaseModel
from typing import OrderedDict as ODict

from sqlalchemy.orm.session import Session
from digirent.database.base import with_db_session
from digirent.database.models import User, ChatMessage


class ChatEventType(str, enum.Enum):
    # send
    USER_CONNECTED = "USER_CONNECTED"

    # listen
    USER_DISCONNECTED = "USER_DISCONNECTED"

    # send and listen
    MESSAGE = "MESSAGE"


class ChatEvent(BaseModel):
    event_type: ChatEventType
    data: dict

    class Config:
        allow_mutation = False
        fields = {"event_type": "eventType"}
        allow_population_by_field_name = True


class ChatManager:
    """Manages user chat"""

    def __init__(self):
        self.chat_users: ODict[UUID, WebSocket] = OrderedDict()

    @with_db_session
    async def send_message_to_user(
        self, user_id: UUID, sender_id: UUID, message: str, session: Session = None
    ):
        db_message = ChatMessage(
            from_user_id=sender_id, to_user_id=user_id, message=message
        )
        session.add(db_message)
        session.commit()
        from_chatuser = self.chat_users.get(sender_id)
        to_chatuser = self.chat_users.get(user_id)
        event = ChatEvent(
            event_type=ChatEventType.MESSAGE,
            data={"from": str(sender_id), "to": str(user_id), "message": message},
        )
        if from_chatuser:
            await from_chatuser.send_json(event.dict(by_alias=True))
        if to_chatuser:
            await to_chatuser.send_json(event.dict(by_alias=True))

    async def handle_event(self, event: ChatEvent, websocket: WebSocket):
        event_type: ChatEventType = event.event_type
        data: dict = event.data
        user: User = websocket.state.user
        if event_type == ChatEventType.USER_CONNECTED:
            # User has successfully connected
            self.chat_users[user.id] = websocket
            await websocket.send_json(
                ChatEvent(
                    event_type=ChatEventType.USER_CONNECTED,
                    data={"user_id": str(user.id)},
                ).dict(by_alias=True)
            )
        elif event_type == ChatEventType.MESSAGE:
            # user has sent message
            to: UUID = UUID(data["to"])
            from_user: UUID = user.id
            if from_user == to:
                return
            message: str = data["message"]
            await self.send_message_to_user(to, from_user, message)
        elif event_type == ChatEventType.USER_DISCONNECTED:
            print(f"going to drop user {user.id}")
            del self.chat_users[user.id]
