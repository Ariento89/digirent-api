from typing import List
from uuid import UUID
from digirent.api.schema import BasePaginationSchema, OrmSchema


class ChatMessageSchema(OrmSchema):
    from_user: UUID
    to_user: UUID
    message: str


class ChatMessagePaginationSchema(BasePaginationSchema):
    data: List[ChatMessageSchema]
