from typing import List
from uuid import UUID
from datetime import datetime
from digirent.api.schema import BasePaginationSchema, BaseSchema, OrmSchema


class ChatMessageSchema(OrmSchema):
    from_user_id: UUID
    to_user_id: UUID
    message: str


class UserSchema(BaseSchema):
    id: UUID
    first_name: str
    last_name: str

    class Config:
        orm_mode = True


class ChatMessagePaginationSchema(BasePaginationSchema):
    data: List[ChatMessageSchema]


class ChatUserSchema(BaseSchema):
    from_user: UserSchema
    to_user: UserSchema
    message: str
    timestamp: datetime


class ChatUserPaginationSchema(BasePaginationSchema):
    data: List[ChatUserSchema]
