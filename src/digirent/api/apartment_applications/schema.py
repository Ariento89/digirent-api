from typing import Optional
from uuid import UUID
from digirent.database.enums import ApartmentApplicationStatus
from ..schema import BaseSchema, OrmSchema


class ApartmentApplicationBaseSchema(BaseSchema):
    apartment_id: UUID
    tenant_id: UUID
    stage: Optional[ApartmentApplicationStatus]


class ApartmentApplicationSchema(ApartmentApplicationBaseSchema, OrmSchema):
    pass
