from datetime import date
from uuid import UUID
from typing import List, Optional
from pydantic import validator
from digirent.database.enums import FurnishType, HouseType
from ..schema import BaseSchema, OrmSchema


def ensure_greater_than_zero(key, val):
    if val <= 0:
        raise ValueError(f"{key} must be greater than zero")
    return val


class LandlordInApartmentSchema(OrmSchema):
    first_name: str
    last_name: str
    profile_image_url: Optional[str]


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
    furnish_type: FurnishType
    available_from: date
    available_to: date

    @validator("monthly_price")
    def monthly_price_must_be_greater_than_zero(cls, v):
        return ensure_greater_than_zero("monthlyPrice", v)

    @validator("utilities_price")
    def utilities_price_must_be_greater_than_zero(cls, v):
        return ensure_greater_than_zero("utilitiesPrice", v)

    @validator("bedrooms")
    def bedrooms_must_be_greater_than_zero(cls, v):
        return ensure_greater_than_zero("bedrooms", v)

    @validator("bathrooms")
    def bathrooms_must_be_greater_than_zero(cls, v):
        return ensure_greater_than_zero("bathrooms", v)

    @validator("size")
    def size_must_be_greater_than_zero(cls, v):
        return ensure_greater_than_zero("size", v)


class ApartmentCreateSchema(BaseApartmentSchema):
    longitude: float
    latitude: float
    amenities: List[UUID]


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
    longitude: Optional[float]
    latitude: Optional[float]
    furnish_type: Optional[str]
    available_from: Optional[date]
    available_to: Optional[date]
    amenities: Optional[List[UUID]]

    @validator("monthly_price")
    def monthly_price_must_be_greater_than_zero(cls, v):
        return ensure_greater_than_zero("monthlyPrice", v)

    @validator("utilities_price")
    def utilities_price_must_be_greater_than_zero(cls, v):
        return ensure_greater_than_zero("utilitiesPrice", v)

    @validator("bedrooms")
    def bedrooms_must_be_greater_than_zero(cls, v):
        return ensure_greater_than_zero("bedrooms", v)

    @validator("bathrooms")
    def bathrooms_must_be_greater_than_zero(cls, v):
        return ensure_greater_than_zero("bathrooms", v)

    @validator("size")
    def size_must_be_greater_than_zero(cls, v):
        return ensure_greater_than_zero("size", v)


class ApartmentSchema(OrmSchema, BaseApartmentSchema):
    amenity_titles: List[str]
    total_price: float
    landlord: LandlordInApartmentSchema
    images: List[str]
    videos: List[str]
    latitude: str
    longitude: str


class ApartmentWithContextSchema(BaseSchema):
    context: Optional[dict]
    apartment: ApartmentSchema


class TenantApartmentSchema(BaseSchema):
    applied: bool
    apartment: ApartmentSchema
    is_favorited: bool
