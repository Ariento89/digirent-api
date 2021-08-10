from datetime import date
from typing import List, Literal, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm.session import Session
import digirent.api.dependencies as dependencies
from digirent.database.enums import FurnishType, HouseType
from digirent.database.models import (
    Admin,
    Amenity,
    Apartment,
    Landlord,
)
from .schema import (
    ApartmentSchema,
)

router = APIRouter()


@router.get("/", response_model=List[ApartmentSchema])
def fetch_apartments(
    session: Session = Depends(dependencies.get_database_session),
    admin: Admin = Depends(dependencies.get_current_admin_user),
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    min_size: Optional[float] = None,
    max_size: Optional[float] = None,
    min_bedrooms: Optional[int] = None,
    max_bedrooms: Optional[int] = None,
    min_bathrooms: Optional[int] = None,
    max_bathrooms: Optional[int] = None,
    available_from: Optional[date] = None,
    available_to: Optional[date] = None,
    landlord_id: Optional[UUID] = None,
    house_type: Optional[HouseType] = None,
    furnish_type: Optional[FurnishType] = None,
    ameneties: Optional[List[UUID]] = Query(None),
    sort_by: Optional[Literal["price", "date"]] = None,
    sort_order: Optional[Literal["asc", "desc"]] = None,
):

    query = session.query(Apartment)
    query = query.filter(Apartment.is_archived.is_(False))
    if min_price is not None:
        query = query.filter(Apartment.monthly_price >= min_price)
    if max_price is not None:
        query = query.filter(Apartment.monthly_price <= max_price)
    if min_size is not None:
        query = query.filter(Apartment.size >= min_size)
    if max_size is not None:
        query = query.filter(Apartment.size <= max_size)
    if min_bedrooms is not None:
        query = query.filter(Apartment.bedrooms >= min_bedrooms)
    if max_bedrooms is not None:
        query = query.filter(Apartment.bedrooms <= max_bedrooms)
    if min_bathrooms is not None:
        query = query.filter(Apartment.bathrooms >= min_bathrooms)
    if max_bathrooms is not None:
        query = query.filter(Apartment.bathrooms <= max_bathrooms)
    if latitude is not None and longitude is not None:
        center = "POINT({} {})".format(longitude, latitude)
        query = query.filter(Apartment.location.ST_Distance_Sphere(center) < 5000)
    if landlord_id is not None:
        landlord: Landlord = session.query(Landlord).get(landlord_id)
        if not landlord:
            raise HTTPException(404, "Landlord not found")
        query = query.filter(Apartment.landlord_id == landlord_id)
    if available_from is not None:
        query = query.filter(Apartment.available_from <= available_from).filter(
            Apartment.available_to >= available_from
        )
    if available_to is not None:
        query = query.filter(Apartment.available_from <= available_to).filter(
            Apartment.available_to >= available_to
        )
    if house_type is not None:
        query = query.filter(Apartment.house_type == house_type)
    if furnish_type is not None:
        query = query.filter(Apartment.furnish_type == furnish_type)
    if ameneties is not None:
        for amenity in ameneties:
            query = query.filter(Apartment.amenities.any(Amenity.id == amenity))
    sort_col = Apartment.total_price if sort_by == "price" else Apartment.created_at
    sort_expr = sort_col.desc() if sort_order == "desc" else sort_col.asc()
    query = query.order_by(sort_expr)
    return query.all()


@router.get("/{apartment_id}", response_model=ApartmentSchema)
def get_apartment(
    apartment_id: UUID,
    admin: Admin = Depends(dependencies.get_current_admin_user),
    session: Session = Depends(dependencies.get_database_session),
):
    apartment = session.query(Apartment).get(apartment_id)
    if apartment is None:
        raise HTTPException(404, "Apartment not found")
    return apartment
