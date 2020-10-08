from typing import List
from fastapi import APIRouter, Depends, HTTPException
from digirent.app.error import ApplicationError
from sqlalchemy.orm.session import Session
from digirent.app import Application
import digirent.api.dependencies as dependencies
from digirent.database.models import Admin, User
from .schema import AmenityCreateSchema, AmenitySchema

router = APIRouter()


@router.post("/", status_code=201, response_model=AmenitySchema)
async def create_amenity(
    data: AmenityCreateSchema,
    admin: Admin = Depends(dependencies.get_current_admin_user),
    application: Application = Depends(dependencies.get_application),
    session: Session = Depends(dependencies.get_database_session),
):
    try:
        return application.create_amenity(session, **data.dict())
    except ApplicationError as e:
        raise HTTPException(401, str(e))


@router.get("/", response_model=List[AmenitySchema])
async def fetch_amenities(
    user: User = Depends(dependencies.get_current_user),
    application: Application = Depends(dependencies.get_application),
    session: Session = Depends(dependencies.get_database_session),
):
    try:
        return application.amenity_service.all(session)
    except ApplicationError as e:
        raise HTTPException(401, str(e))
