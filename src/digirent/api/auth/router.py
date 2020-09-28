from fastapi import APIRouter, Depends, HTTPException
from digirent.app.error import ApplicationError
from .schema import TokenSchema
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm.session import Session
from digirent.app import Application
import digirent.api.dependencies as dependencies


router = APIRouter()


@router.post("/", response_model=TokenSchema)
async def login(
    data: OAuth2PasswordRequestForm = Depends(),
    application: Application = Depends(dependencies.get_application),
    session: Session = Depends(dependencies.get_database_session),
):
    try:
        token = application.authenticate_user(session, data.username, data.password)
        return TokenSchema(access_token=token, token_type="bearer")
    except ApplicationError as e:
        raise HTTPException(401, str(e))
