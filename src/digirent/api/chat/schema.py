from typing import List
from uuid import UUID
from datetime import datetime
from digirent.api.schema import BasePaginationSchema, BaseSchema, OrmSchema


class ChatMessageSchema(OrmSchema):
    from_user_id: UUID
    to_user_id: UUID
    message: str


class ChatMessagePaginationSchema(BasePaginationSchema):
    data: List[ChatMessageSchema]


class ChatUserSchema(BaseSchema):
    from_user_id: UUID
    to_user_id: UUID
    message: str
    timestamp: datetime


class ChatUserPaginationSchema(BasePaginationSchema):
    data: List[ChatUserSchema]
