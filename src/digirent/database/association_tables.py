from uuid import UUID
from sqlalchemy import Column, Table, ForeignKey
from sqlalchemy_utils import UUIDType
from .base import Base

apartments_amenities_association_table = Table(
    "apartments_amenities_association",
    Base.metadata,
    Column("apartment_id", UUIDType(binary=False), ForeignKey("apartments.id")),
    Column("amenity_id", UUIDType(binary=False), ForeignKey("amenities.id")),
)
