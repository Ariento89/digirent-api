from typing import List, Optional
from uuid import UUID
from sqlalchemy import Column, String, Text, Float, Integer, ForeignKey, JSON, Boolean
from sqlalchemy_utils import ChoiceType, EmailType, UUIDType
from .base import Base
from .mixins import EntityMixin, TimestampMixin
from enum import Enum


class UserRole(str, Enum):
    ADMIN = "admin"
    REGULAR = "regular"


class User(Base, EntityMixin, TimestampMixin):
    __tablename__ = "users"
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    username = Column(String, nullable=False, unique=True)
    phone_number = Column(String, nullable=False, unique=True)
    email = Column(EmailType, nullable=False, unique=True)
    hashed_password = Column(Text, nullable=False)
    email_verified = Column(Boolean, nullable=False, default=False)
    phone_verified = Column(Boolean, nullable=False, default=False)
    is_suspended = Column(Boolean, nullable=False, default=False)
    suspended_reason = Column(String, nullable=True)
    role = Column(
        ChoiceType(UserRole, impl=String()), nullable=False, default=UserRole.REGULAR
    )

    def __init__(
        self,
        first_name: str,
        last_name: str,
        username: str,
        email: str,
        phone_number: str,
        hashed_password: str,
        role: UserRole = UserRole.REGULAR,
    ) -> None:
        self.first_name = first_name
        self.last_name = last_name
        self.username = username
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
