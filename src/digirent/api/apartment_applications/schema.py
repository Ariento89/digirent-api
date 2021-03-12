from typing import List, Optional
from datetime import datetime
from uuid import UUID
from digirent.database.enums import ApartmentApplicationStatus
from ..schema import BaseSchema, OrmSchema


class TenantInApplicationSchema(OrmSchema):
    first_name: str
    last_name: str
    email: str
    profile_percentage: float
    age: Optional[int]
    gender: Optional[str]
    city: Optional[str]
    profile_image_url: Optional[str]


class ApartmentApplicationBaseSchema(BaseSchema):
    apartment_id: UUID
    tenant: TenantInApplicationSchema
    status: Optional[ApartmentApplicationStatus]


class ApartmentApplicationSchema(ApartmentApplicationBaseSchema, OrmSchema):
    pass


class SignrequestSignerSchema(BaseSchema):
    needs_to_sign: bool
    signed_on: Optional[datetime]
    email: str
    signed: bool
    declined: bool
    declined_on: Optional[datetime]

    class Config:
        extra = "allow"


class SignrequestSignrequestSchema(BaseSchema):
    signers: List[SignrequestSignerSchema]

    class Config:
        extra = "allow"


class SignrequestDocumentSchema(BaseSchema):
    uuid: UUID
    external_id: UUID
    status: str
    signrequest: SignrequestSignrequestSchema

    class Config:
        extra = "allow"


class SignrequestEventSchema(BaseSchema):
    uuid: UUID
    status: str
    event_type: str
    timestamp: datetime
    event_hash: str
    document: SignrequestDocumentSchema

    class Config:
        extra = "allow"
