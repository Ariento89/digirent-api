from datetime import date
from uuid import UUID
from typing import Optional
from digirent.database.models import Gender, UserRole
from ..schema import BaseSchema, OrmSchema


class ProfileSchema(OrmSchema):
    first_name: str
    last_name: str
    dob: Optional[date]
    description: Optional[str]
    city: Optional[str]
    gender: Optional[Gender]
    email: str
    phone_number: str
    role: UserRole
    is_active: bool
