from uuid import UUID
from ..schema import BaseSchema, OrmSchema
from digirent.database.enums import BookingRequestStatus


class InviteBaseSchema(BaseSchema):
    apartment_id: UUID
    tenant_id: UUID


class InviteCreateSchema(InviteBaseSchema):
    pass


class InviteSchema(InviteBaseSchema, OrmSchema):
    status: BookingRequestStatus
