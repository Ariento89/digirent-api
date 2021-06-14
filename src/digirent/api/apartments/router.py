from datetime import date
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, File, UploadFile
from fastapi.param_functions import Body
from digirent.app.error import ApplicationError
from sqlalchemy.orm.session import Session
from digirent.app import Application
import digirent.api.dependencies as dependencies
from digirent.database.enums import FurnishType, HouseType
from digirent.database.models import (
    Amenity,
    Apartment,
    ApartmentApplication,
    Landlord,
    Tenant,
)
from .schema import (
    ApartmentCreateSchema,
    ApartmentSchema,
    ApartmentUpdateSchema,
    TenantApartmentSchema,
)

router = APIRouter()


@router.post(
    "/",
    status_code=201,
    response_model=ApartmentSchema,
)
async def create_apartment(
    data: ApartmentCreateSchema,
    landlord: Landlord = Depends(dependencies.get_current_active_landlord),
    application: Application = Depends(dependencies.get_application),
    session: Session = Depends(dependencies.get_database_session),
):
    try:
        payload = data.dict()
        amenities = data.amenities
        if amenities:
            amenities = [session.query(Amenity).get(x) for x in amenities]
            if any(x is None for x in amenities):
                raise HTTPException(404, "Amenity not found")
        payload["amenities"] = amenities
        return application.create_apartment(session, landlord, **payload)
    except ApplicationError as e:
        if "not found" in str(e).lower():
            raise HTTPException(404, str(e))
        raise HTTPException(401, str(e))


@router.put(
    "/{apartment_id}",
    status_code=200,
    response_model=ApartmentSchema,
)
def update_apartment(
    apartment_id: UUID,
    data: ApartmentUpdateSchema,
    session: Session = Depends(dependencies.get_database_session),
    landlord: Landlord = Depends(dependencies.get_current_active_landlord),
    application: Application = Depends(dependencies.get_application),
):
    try:
        payload = data.dict(exclude_none=True)
        if "amenities" in payload:
            amenities = payload["amenities"]
            amenities = [
                session.query(Amenity).filter(Amenity.title == x).first()
                for x in amenities
            ]
            payload["amenities"] = amenities
        return application.update_apartment(session, landlord, apartment_id, **payload)
    except ApplicationError as e:
        if "not found" in str(e).lower():
            raise HTTPException(404, str(e))
        raise HTTPException(400, str(e))


@router.post(
    "/{apartment_id}/images",
    response_model=ApartmentSchema,
)
def upload_image(
    apartment_id: UUID,
    image: UploadFile = File(...),
    landlord: Landlord = Depends(dependencies.get_current_active_landlord),
    session: Session = Depends(dependencies.get_database_session),
    app: Application = Depends(dependencies.get_application),
):
    try:
        apartment: Apartment = app.apartment_service.get(session, apartment_id)
        if not apartment:
            raise HTTPException(404, "Apartment not found")
        return app.upload_apartment_image(
            landlord, apartment, image.file, image.filename
        )
    except ApplicationError as e:
        raise HTTPException(400, str(e))


@router.post(
    "/{apartment_id}/videos",
    response_model=ApartmentSchema,
)
def upload_videos(
    apartment_id: UUID,
    video: UploadFile = File(...),
    landlord: Landlord = Depends(dependencies.get_current_active_landlord),
    session: Session = Depends(dependencies.get_database_session),
    app: Application = Depends(dependencies.get_application),
):
    try:
        apartment: Apartment = app.apartment_service.get(session, apartment_id)
        if not apartment:
            raise HTTPException(404, "Apartment not found")
        return app.upload_apartment_video(
            landlord, apartment, video.file, video.filename
        )
    except ApplicationError as e:
        raise HTTPException(400, str(e))


@router.get("/", response_model=List[ApartmentSchema])
def fetch_apartments(
    session: Session = Depends(dependencies.get_database_session),
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
    is_descending: Optional[bool] = False,
    landlord_id: Optional[UUID] = None,
    house_type: Optional[HouseType] = None,
    furnish_type: Optional[FurnishType] = None,
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
    query = (
        query.order_by(Apartment.created_at.desc())
        if is_descending
        else query.order_by(Apartment.created_at.asc())
    )
    return query.all()


@router.get("/house-types", response_model=List[str])
def fetch_supported_house_types():
    return [x.value for x in HouseType]


@router.get("/tenant", response_model=List[TenantApartmentSchema])
def fetch_apartments_as_tenant(
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    available_from: Optional[date] = None,
    available_to: Optional[date] = None,
    is_descending: Optional[bool] = False,
    landlord_id: Optional[UUID] = None,
    session: Session = Depends(dependencies.get_database_session),
    tenant: Tenant = Depends(dependencies.get_current_active_tenant),
):
    query = session.query(Apartment)
    query = query.filter(Apartment.is_archived.is_(False))
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
    query = (
        query.order_by(Apartment.created_at.desc())
        if is_descending
        else query.order_by(Apartment.created_at.asc())
    )
    all_apartments = query.all()
    result = []
    for apartment in all_apartments:
        tenant_apartment_application = (
            session.query(ApartmentApplication)
            .filter(ApartmentApplication.tenant_id == tenant)
            .filter(ApartmentApplication.apartment_id == apartment.id)
        )
        applied = tenant_apartment_application is not None
        result.append({"applied": applied, "apartment": apartment})
    return result


@router.get("/{apartment_id}", response_model=ApartmentSchema)
def get_apartment(
    apartment_id: UUID,
    landlord: Landlord = Depends(dependencies.get_optional_current_active_landlord),
    session: Session = Depends(dependencies.get_database_session),
):
    apartment = session.query(Apartment).get(apartment_id)
    if landlord and apartment.landlord_id == landlord.id:
        return apartment
    if landlord and apartment.is_archived:
        raise HTTPException(404, "Apartment not found")
    if apartment.is_archived:
        raise HTTPException(404, "Apartment not found")
    return apartment


@router.delete("/{apartment_id}/images", response_model=ApartmentSchema)
def delete_apartment_image(
    apartment_id: UUID,
    images: List[str] = Body(...),
    session: Session = Depends(dependencies.get_database_session),
    app: Application = Depends(dependencies.get_application),
    landlord: Landlord = Depends(dependencies.get_current_active_landlord),
):
    apartment = (
        session.query(Apartment)
        .filter(Apartment.apartment_id == apartment_id)
        .filter(Apartment.landlord_id == landlord.id)
        .one_or_none()
    )
    if not apartment:
        raise HTTPException(404, "Apartment not found")
    for image in images:
        app.delete_apartment_image(apartment, image)
    return apartment


@router.delete("/{apartment_id}/videos", response_model=ApartmentSchema)
def delete_apartment_video(
    apartment_id: UUID,
    videos: List[str] = Body(...),
    session: Session = Depends(dependencies.get_database_session),
    app: Application = Depends(dependencies.get_application),
    landlord: Landlord = Depends(dependencies.get_current_active_landlord),
):
    apartment = (
        session.query(Apartment)
        .filter(Apartment.apartment_id == apartment_id)
        .filter(Apartment.landlord_id == landlord.id)
        .one_or_none()
    )
    if not apartment:
        raise HTTPException(404, "Apartment not found")
    for video in videos:
        app.delete_apartment_video(apartment, video)
    return apartment


@router.put("/{apartment_id}/archive", response_model=ApartmentSchema)
def archive_apartment(
    apartment_id: UUID,
    session: Session = Depends(dependencies.get_database_session),
    landlord: Landlord = Depends(dependencies.get_current_active_landlord),
):
    apartment = (
        session.query(Apartment)
        .filter(Apartment.id == apartment_id)
        .filter(Apartment.landlord_id == landlord.id)
        .one_or_none()
    )
    if not apartment:
        raise HTTPException(404, "Apartment not found")
    if apartment.is_archived:
        raise HTTPException(400, "Apartment is already archived")
    # TODO more validation
    apartment.is_archived = True
    session.commit()
    return apartment


@router.put("/{apartment_id}/unarchive", response_model=ApartmentSchema)
def unarchive_apartment(
    apartment_id: UUID,
    session: Session = Depends(dependencies.get_database_session),
    landlord: Landlord = Depends(dependencies.get_current_active_landlord),
):
    apartment = (
        session.query(Apartment)
        .filter(Apartment.id == apartment_id)
        .filter(Apartment.landlord_id == landlord.id)
        .one_or_none()
    )
    if not apartment:
        raise HTTPException(404, "Apartment not found")
    if not apartment.is_archived:
        raise HTTPException(400, "Apartment is not archived")
    # TODO more validation
    apartment.is_archived = False
    session.commit()
    return apartment
