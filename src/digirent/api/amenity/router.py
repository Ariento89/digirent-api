from typing import List
from fastapi import APIRouter, Depends, HTTPException
from digirent.app.error import ApplicationError
from sqlalchemy.orm.session import Session
from digirent.app import Application
import digirent.api.dependencies as dependencies
from .schema import AmenitySchema

router = APIRouter()


@router.get("/", response_model=List[AmenitySchema])
async def fetch_amenities(
    application: Application = Depends(dependencies.get_application),
    session: Session = Depends(dependencies.get_database_session),
):
    try:
        return application.amenity_service.all(session)
    except ApplicationError as e:
        raise HTTPException(401, str(e))
