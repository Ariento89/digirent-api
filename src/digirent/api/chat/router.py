import json
from uuid import UUID
from fastapi import APIRouter, WebSocket, Depends
from typing import Optional, Any
from fastapi.exceptions import HTTPException
from sqlalchemy import or_, func
from sqlalchemy.orm.session import Session
from starlette import status
from starlette.types import Message
from digirent.api.chat.chat import ChatEvent, ChatEventType, ChatManager
from digirent.api.chat.schema import (
    ChatMessagePaginationSchema,
    ChatUserPaginationSchema,
)
import digirent.api.dependencies as deps
from digirent.api.dependencies import (
    get_current_admin_user,
    get_current_user,
    get_database_session,
)
from digirent.database.models import ChatMessage, User

router = APIRouter()


class ChatManagerEndpoint:
    def __init__(self, chat_manager: ChatManager):
        self.chat_manager: ChatManager = chat_manager
        self.encoding = "json"

    async def decode(self, websocket: WebSocket, message: Message) -> Any:
        if self.encoding == "bytes":
            if "bytes" not in message:
                await websocket.close(code=status.WS_1003_UNSUPPORTED_DATA)
                raise RuntimeError("Expected bytes websocket messages, but got text")
            return message["bytes"]

        elif self.encoding == "json":
            if message.get("text") is not None:
                text = message["text"]
            else:
                text = message["bytes"].decode("utf-8")

            try:
                return json.loads(text)
            except json.decoder.JSONDecodeError:
                await websocket.close(code=status.WS_1003_UNSUPPORTED_DATA)
                raise RuntimeError("Malformed JSON data received.")

        elif self.encoding == "text":
            if "text" not in message:
                await websocket.close(code=status.WS_1003_UNSUPPORTED_DATA)
                raise RuntimeError("Expected text websocket messages, but got bytes")
            return message["text"]

        assert (
            self.encoding is None
        ), f"Unsupported 'encoding' attribute {self.encoding}"
        return message["text"] if message.get("text") else message["bytes"]

    async def on_connect(self, websocket: WebSocket):
        await websocket.accept()
        await self.chat_manager.handle_event(
            ChatEvent(event_type=ChatEventType.USER_CONNECTED, data={}), websocket
        )

    async def on_receive(self, websocket: WebSocket, data: dict):
        try:
            event = ChatEvent(**data)
            await self.chat_manager.handle_event(event, websocket)
        except Exception:
            pass

    async def on_disconnect(self, websocket: WebSocket):
        """
        User has disconnected
        """
        await self.chat_manager.handle_event(
            ChatEvent(event_type=ChatEventType.USER_DISCONNECTED, data={}), websocket
        )


@router.websocket("/ws/{token}")
async def chat(websocket: WebSocket, user: User = Depends(deps.user_from_websocket)):
    if user is None:
        await websocket.close()
        return
    chat_manager: Optional[ChatManager] = websocket.get("chat_manager")
    if chat_manager is None:
        raise RuntimeError("Chat manager is unavailable")
    manager_endpoint = ChatManagerEndpoint(chat_manager)
    websocket.state.user = user
    await manager_endpoint.on_connect(websocket)
    try:
        while True:
            message: Message = await websocket.receive()
            if message["type"] == "websocket.receive":
                data = await manager_endpoint.decode(websocket, message)
                await manager_endpoint.on_receive(websocket, data)
            elif message["type"] == "websocket.disconnect":
                break
    except Exception as exc:
        raise exc from None
    finally:
        await manager_endpoint.on_disconnect(websocket)


@router.get("/users", response_model=ChatUserPaginationSchema)
def fetch_users_chat_list(
    page: int = 1,
    page_size: int = 20,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_database_session),
):
    """Fetch list of users the authenticated user has chatted with"""
    last_message = func.last(ChatMessage.message)
    last_time = func.last(ChatMessage.created_at)
    chat_messages_query = (
        session.query(
            last_message.label("message"),
            last_time.label("timestamp"),
            ChatMessage.from_user_id,
            ChatMessage.to_user_id,
        )
        .filter(
            or_(ChatMessage.from_user_id == user.id, ChatMessage.to_user_id == user.id)
        )
        .group_by(ChatMessage.from_user_id, ChatMessage.to_user_id)
    )
    # TODO fix count to account for duplicates due to from_user_id and to_user_id grouping
    count = chat_messages_query.count()
    chat_messages = (
        chat_messages_query.offset((page - 1) * page_size).limit(page_size).all()
    )
    result_dict = {}
    for chat_message in chat_messages:
        other_user_id = (
            chat_message.from_user_id
            if chat_message.from_user_id != user.id
            else chat_message.to_user_id
        )
        if other_user_id in result_dict:
            other_user_dict = result_dict[other_user_id]
            if chat_message.timestamp >= other_user_dict["timestamp"]:
                other_user_dict["timestamp"] = chat_message.timestamp
                other_user_dict["message"] = chat_message.message
                other_user_dict["from_user_id"] = chat_message.from_user_id
                other_user_dict["to_user_id"] = chat_message.to_user_id
        else:
            result_dict[other_user_id] = {
                "message": chat_message.message,
                "timestamp": chat_message.timestamp,
                "from_user": session.query(User).get(chat_message.from_user_id),
                "to_user": session.query(User).get(chat_message.to_user_id),
            }
    result_list = [values for _, values in result_dict.items()]
    return {"count": count, "page": page, "page_size": page_size, "data": result_list}


@router.get("/{user_id}", response_model=ChatMessagePaginationSchema)
def fetch_chat_messages(
    user_id: UUID,
    desc: bool = True,
    page: int = 1,
    page_size: int = 20,
    user: Session = Depends(get_current_user),
    session: Session = Depends(get_database_session),
):
    """
    Returns chat message between authenticated user and specified user_id
    """
    if user_id == user.id:
        raise HTTPException(400, "user_id must be different from authenticated user id")
    between = [user.id, user_id]
    query = session.query(ChatMessage).filter(
        or_(ChatMessage.from_user_id.in_(between), ChatMessage.to_user_id.in_(between))
    )
    if desc:
        query = query.order_by(ChatMessage.created_at.desc())
    else:
        query = query.order_by(ChatMessage.created_at.asc())
    count = query.count()
    query = query.offset((page - 1) * page_size).limit(page_size)
    return {"page": page, "page_size": page_size, "count": count, "data": query.all()}


@router.get("/", response_model=ChatMessagePaginationSchema)
def fetch_chat_messages_between_two_users(
    user1: UUID,
    user2: UUID,
    desc: bool = True,
    page: int = 1,
    page_size: int = 20,
    admin: Session = Depends(get_current_admin_user),
    session: Session = Depends(get_database_session),
):
    """
    Allow admin fetch chat message between two users
    """
    if user1 == user2:
        raise HTTPException(400, "user ids must be unique")
    between = [user1, user2]
    query = session.query(ChatMessage).filter(
        or_(ChatMessage.from_user_id.in_(between), ChatMessage.to_user_id.in_(between))
    )
    if desc:
        query = query.order_by(ChatMessage.created_at.desc())
    else:
        query = query.order_by(ChatMessage.created_at.asc())
    count = query.count()
    query = query.offset((page - 1) * page_size).limit(page_size)
    return {"page": page, "page_size": page_size, "count": count, "data": query.all()}
