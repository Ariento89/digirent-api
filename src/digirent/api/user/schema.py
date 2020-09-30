from datetime import date, datetime
from typing import Optional
from digirent.database.models import UserRole
from ..schema import BaseSchema, OrmSchema


class BaseUserSchema(BaseSchema):
    first_name: str
    last_name: str
    email: str
    phone_number: str
    dob: Optional[date]


class UserCreateSchema(BaseUserSchema):
    password: str


class UserSchema(OrmSchema, BaseUserSchema):
    dob: Optional[date]
    role: UserRole
