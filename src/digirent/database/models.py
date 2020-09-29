from datetime import datetime
from typing import List, Optional
from uuid import UUID
from sqlalchemy import (
    Column,
    String,
    Text,
    Float,
    Integer,
    ForeignKey,
    JSON,
    Boolean,
    DateTime,
    Date,
)
from sqlalchemy.orm.session import DEACTIVE
from sqlalchemy_utils import ChoiceType, EmailType, UUIDType
from .base import Base
from .mixins import EntityMixin, TimestampMixin
from enum import Enum


class UserRole(str, Enum):
    ADMIN = "admin"
    TENANT = "tenant"
    LANDLORD = "landlord"


class Gender(str, Enum):
    MALE = "male"
    FEMALE = "female"


class User(Base, EntityMixin, TimestampMixin):
    __tablename__ = "users"
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    dob = Column(Date, nullable=True)
    phone_number = Column(String, nullable=False, unique=True)
    email = Column(EmailType, nullable=False, unique=True)
    hashed_password = Column(Text, nullable=False)
    email_verified = Column(Boolean, nullable=False, default=False)
    phone_verified = Column(Boolean, nullable=False, default=False)
    is_suspended = Column(Boolean, nullable=False, default=False)
    suspended_reason = Column(String, nullable=True)
    role = Column(ChoiceType(UserRole, impl=String()), nullable=False)
    gender = Column(ChoiceType(Gender, impl=String()), nullable=True)
    city = Column(String, nullable=True)
    description = Column(String, nullable=True)

    def __init__(
        self,
        first_name: str,
        last_name: str,
        email: str,
        phone_number: str,
        hashed_password: str,
        role: UserRole,
        dob: datetime = None,
    ) -> None:
        self.first_name = first_name
        self.last_name = last_name
        self.dob = dob
        self.phone_number = phone_number
        self.email = email
        self.hashed_password = hashed_password
        self.role = role
        self.email_verified = False
        self.phone_verified = False
        self.is_suspended = False
        self.suspended_reason = None

    @property
    def is_active(self):
        if self.is_suspended:
            return False
        return all([self.email_verified, self.phone_verified])
