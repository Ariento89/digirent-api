from typing import List, Optional
from uuid import UUID
from datetime import datetime
from digirent.api.schema import BasePaginationSchema, BaseSchema, OrmSchema
from digirent.database.enums import UserRole


class ChatMessageSchema(OrmSchema):
    from_user_id: UUID
    to_user_id: UUID
    message: str


class UserSchema(BaseSchema):
    id: UUID
    first_name: str
    last_name: str
    profile_image_url: Optional[str]
    role: UserRole

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
