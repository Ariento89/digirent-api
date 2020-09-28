import uuid
from sqlalchemy_utils import UUIDType, EmailType
from sqlalchemy import Column, Text, DateTime
from sqlalchemy import func
from sqlalchemy.sql import func
from sqlalchemy import Column, DateTime


class TimestampMixin:
    """Defines fields to record timestamp for record creation and modification.
    """

    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=True, onupdate=func.now())


class EntityMixin:
    id = Column(UUIDType(binary=False), primary_key=True, default=uuid.uuid4)
