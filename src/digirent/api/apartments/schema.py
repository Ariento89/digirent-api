from datetime import date, datetime
from typing import List, Optional
from digirent.database.enums import HouseType
from digirent.database.models import UserRole
from ..schema import BaseSchema, OrmSchema


class BaseApartmentSchema(BaseSchema):
    name: str
    monthly_price: float
    utilities_price: float
    address: str
    country: str
    state: str
    city: str
    description: str
    house_type: HouseType
    bedrooms: int
    bathrooms: int
    size: float
    furnish_type: str
    available_from: date
    available_to: date
    amenities: List[str]


class ApartmentCreateSchema(BaseApartmentSchema):
    pass


class ApartmentUpdateSchema(BaseSchema):
    name: Optional[str]
    monthly_price: Optional[float]
    utilities_price: Optional[float]
    address: Optional[str]
    country: Optional[str]
    state: Optional[str]
    city: Optional[str]
    description: Optional[str]
    house_type: Optional[HouseType]
    bedrooms: Optional[int]
    bathrooms: Optional[int]
    size: Optional[float]
    furnish_type: Optional[str]
    available_from: Optional[date]
    available_to: Optional[date]
    amenities: Optional[List[str]]


class AmenitySchema(OrmSchema, BaseApartmentSchema):
    pass
