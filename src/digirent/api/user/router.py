from fastapi import APIRouter, Depends, HTTPException
from digirent.app.error import ApplicationError
from digirent.api.auth.schema import TokenSchema
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm.session import Session
from digirent.app import Application
import digirent.api.dependencies as dependencies
from digirent.database.models import User
from .schema import UserCreateSchema, UserSchema

router = APIRouter()


@router.post("/", response_model=UserSchema)
async def register(
    data: UserCreateSchema,
    application: Application = Depends(dependencies.get_application),
    session: Session = Depends(dependencies.get_database_session),
):
    try:
        return application.create_user(session, **data.dict())
    except ApplicationError as e:
        raise HTTPException(401, str(e))
