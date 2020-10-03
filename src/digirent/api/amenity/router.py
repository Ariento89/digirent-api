from fastapi import APIRouter, Depends, HTTPException
from digirent.app.error import ApplicationError
from sqlalchemy.orm.session import Session
from digirent.app import Application
import digirent.api.dependencies as dependencies
from digirent.database.models import User
from .schema import AmenityCreateSchema

router = APIRouter()


@router.post("/")
async def register_tenant(
    data: AmenityCreateSchema,
    application: Application = Depends(dependencies.get_application),
    session: Session = Depends(dependencies.get_database_session),
):
    try:
        return application.create_amenity(session, **data.dict())
    except ApplicationError as e:
        raise HTTPException(401, str(e))


@router.post("/landlord", response_model=UserSchema)
async def register_landlord(
    data: UserCreateSchema,
    application: Application = Depends(dependencies.get_application),
    session: Session = Depends(dependencies.get_database_session),
):
    try:
        return application.create_landlord(session, **data.dict())
    except ApplicationError as e:
        raise HTTPException(401, str(e))