from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, File, UploadFile
from digirent.app.error import ApplicationError
from sqlalchemy.orm.session import Session
from digirent.app import Application
import digirent.api.dependencies as dependencies
from digirent.database.models import Amenity, Apartment, Landlord
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
        amenities = payload["amenities"]
        if amenities:
            amenities = [
                session.query(Amenity).filter(Amenity.title == x).first()
                for x in amenities
            ]
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
