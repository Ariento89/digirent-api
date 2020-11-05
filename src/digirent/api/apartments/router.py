from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, File, UploadFile
from digirent.app.error import ApplicationError
from sqlalchemy.orm.session import Session
from digirent.app import Application
import digirent.api.dependencies as dependencies
from digirent.database.models import Amenity, Apartment, Landlord, User
from .schema import ApartmentCreateSchema, ApartmentSchema, ApartmentUpdateSchema

router = APIRouter()


@router.post(
    "/",
    status_code=201,
    response_model=ApartmentSchema,
)
async def create_apartment(
    data: ApartmentCreateSchema,
    landlord: Landlord = Depends(dependencies.get_current_landlord),
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
    landlord: Landlord = Depends(dependencies.get_current_landlord),
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
    landlord: Landlord = Depends(dependencies.get_current_landlord),
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
    landlord: Landlord = Depends(dependencies.get_current_landlord),
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
    user: User = Depends(dependencies.get_current_user),
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
):
    query = session.query(Apartment)
    if min_price:
        query = query.filter(Apartment.monthly_price >= min_price)
    if max_price:
        query = query.filter(Apartment.monthly_price <= max_price)
    if min_size:
        query = query.filter(Apartment.size >= min_size)
    if max_size:
        query = query.filter(Apartment.size <= max_size)
    if min_bedrooms:
        query = query.filter(Apartment.bedrooms >= min_bedrooms)
    if max_bedrooms:
        query = query.filter(Apartment.bedrooms <= max_bedrooms)
    if min_bathrooms:
        query = query.filter(Apartment.bathrooms >= min_bathrooms)
    if max_bathrooms:
        query = query.filter(Apartment.bathrooms <= max_bathrooms)
    if latitude and longitude:
        center = "POINT({} {})".format(longitude, latitude)
        query = query.filter(Apartment.location.ST_Distance_Sphere(center) < 5000)
    return query.all()


@router.get("/{apartment_id}", response_model=ApartmentSchema)
def get_apartment(
    apartment_id: UUID,
    session: Session = Depends(dependencies.get_database_session),
    user: User = Depends(dependencies.get_current_user),
):
    apartment = session.query(Apartment).get(apartment_id)
    if not apartment:
        raise HTTPException(404, "Apartment not found")
    return apartment
