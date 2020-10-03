from datetime import date, datetime
from typing import Optional
from digirent.database.models import UserRole
from ..schema import BaseSchema, OrmSchema


class BaseAmenitySchema(BaseSchema):
    title: str


class AmenityCreateSchema(BaseAmenitySchema):
    pass


class AmenitySchema(OrmSchema, BaseAmenitySchema):
    pass
