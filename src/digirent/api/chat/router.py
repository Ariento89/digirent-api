import json
from uuid import UUID
from fastapi import APIRouter, WebSocket, Depends
from typing import List, Optional, Any
from fastapi.exceptions import HTTPException
from fastapi.param_functions import Query
from sqlalchemy import or_
from sqlalchemy.orm.session import Session
from starlette import status
from starlette.types import Message
from digirent.api.chat.chat import ChatEvent, ChatEventType, ChatManager
from digirent.api.chat.schema import ChatMessagePaginationSchema
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


@router.get("/{user_id}", response_model=ChatMessagePaginationSchema)
def fetch_chat_messages(
    user_id: UUID,
    desc: bool = True,
    page: int = 1,
    page_size: int = 20,
    user: Session = Depends(get_current_user),
    session: Session = Depends(get_database_session),
):
    if user_id == user.id:
        raise HTTPException(400, "user_id must be different from authenticated user id")
    between = [user.id, user_id]
    query = session.query(ChatMessage).filter(
        or_(ChatMessage.from_user.in_(between), ChatMessage.to_user.in_(between))
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
    between: List[str] = Query(...),
    desc: bool = True,
    page: int = 1,
    page_size: int = 20,
    admin: Session = Depends(get_current_admin_user),
    session: Session = Depends(get_database_session),
):
    if len(between) != 2 or (between[0] == between[1]):
        raise HTTPException(400, "between must contain two unique ids")
    between = [UUID(x) for x in between]
    query = session.query(ChatMessage).filter(
        or_(ChatMessage.from_user.in_(between), ChatMessage.to_user.in_(between))
    )
    if desc:
        query = query.order_by(ChatMessage.created_at.desc())
    else:
        query = query.order_by(ChatMessage.created_at.asc())
    count = query.count()
    query = query.offset((page - 1) * page_size).limit(page_size)
    return {"page": page, "page_size": page_size, "count": count, "data": query.all()}
