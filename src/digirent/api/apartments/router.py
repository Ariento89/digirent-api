from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from digirent.app.error import ApplicationError
from sqlalchemy.orm.session import Session
from digirent.app import Application
import digirent.api.dependencies as dependencies
from digirent.database.models import Amenity, Landlord
from .schema import ApartmentCreateSchema, ApartmentUpdateSchema

router = APIRouter()


@router.post("/", status_code=201)
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


@router.put("/{apartment_id}", status_code=200)
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
