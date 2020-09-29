from fastapi import APIRouter, Depends, HTTPException
from digirent.app.error import ApplicationError
from digirent.api.auth.schema import TokenSchema
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm.session import Session
from digirent.app import Application
import digirent.api.dependencies as dependencies
from digirent.database.models import User
from .schema import TenantCreateSchema, LandlordCreateSchema, UserSchema

router = APIRouter()


@router.post("/tenant", response_model=UserSchema)
async def register_tenant(
    data: TenantCreateSchema,
    application: Application = Depends(dependencies.get_application),
    session: Session = Depends(dependencies.get_database_session),
):
    try:
        return application.create_tenant(session, **data.dict())
    except ApplicationError as e:
        raise HTTPException(401, str(e))


@router.post("/landlord", response_model=UserSchema)
async def register_landlord(
    data: LandlordCreateSchema,
    application: Application = Depends(dependencies.get_application),
    session: Session = Depends(dependencies.get_database_session),
):
    try:
        return application.create_landlord(session, **data.dict())
    except ApplicationError as e:
        raise HTTPException(401, str(e))