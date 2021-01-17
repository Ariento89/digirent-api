from datetime import date
from typing import Optional
from digirent.database.models import UserRole
from ..schema import BaseSchema, OrmSchema


class BaseUserSchema(BaseSchema):
    first_name: str
    last_name: str
    email: Optional[str]
    phone_number: Optional[str]
    dob: Optional[date]


class UserCreateSchema(BaseUserSchema):
    password: str


class UserSchema(OrmSchema, BaseUserSchema):
    dob: Optional[date]
    role: UserRole
    profile_image_url: Optional[str]
