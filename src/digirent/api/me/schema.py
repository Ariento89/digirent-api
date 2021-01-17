from datetime import date
from typing import Optional
from digirent.database.enums import HouseType
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
    phone_number: Optional[str]
    role: UserRole
    is_active: bool
    profile_percentage: Optional[float]
    copy_id_uploaded: bool
    proof_of_income_uploaded: bool
    proof_of_enrollment_uploaded: bool
    profile_image_url: Optional[str]


class ProfileUpdateSchema(BaseSchema):
    first_name: Optional[str]
    last_name: Optional[str]
    dob: Optional[date]
    email: Optional[str]
    phone_number: Optional[str]
    city: Optional[str]
    gender: Optional[Gender]
    description: Optional[str]


class LookingForSchema(BaseSchema):
    house_type: HouseType
    city: str
    max_budget: float


class BankDetailSchema(BaseSchema):
    account_name: str
    account_number: str


class PasswordUpdateSchema(BaseSchema):
    old_password: str
    new_password: str
