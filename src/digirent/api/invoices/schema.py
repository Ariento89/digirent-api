from datetime import date
from typing import Optional
from uuid import UUID
from digirent.api.schema import BaseSchema, OrmSchema
from digirent.database.enums import InvoiceStatus, InvoiceType


class InvoiceBaseSchema(BaseSchema):
    status: InvoiceStatus
    amount: float
    description: str
    payment_id: str
    payment_action_date: Optional[date]
    next_date: date
    type: InvoiceType


class InvoiceSchema(OrmSchema, InvoiceBaseSchema):
    user_id: Optional[UUID]
    apartment_application_id: Optional[UUID]
