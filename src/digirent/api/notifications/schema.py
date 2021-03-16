from uuid import UUID
from digirent.api.schema import BasePaginationSchema, OrmSchema
from typing import List, Union
from digirent.database.enums import NotificationType


class NotificationSchema(OrmSchema):
    type: NotificationType
    user_id: UUID
    is_read: bool
    data: Union[dict, list]


class PaginatedNotificationSchema(BasePaginationSchema):
    data: List[NotificationSchema]
