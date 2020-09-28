from digirent.database.models import UserRole
from ..schema import BaseSchema, OrmSchema


class BaseUserSchema(BaseSchema):
    first_name: str
    last_name: str
    username: str
    email: str
    phone_number: str


class UserCreateSchema(BaseUserSchema):
    password: str


class UserSchema(OrmSchema, BaseUserSchema):
    role: UserRole
