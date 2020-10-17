from fastapi import APIRouter, Depends, HTTPException
from fastapi.requests import Request
from digirent.app.error import ApplicationError
from .schema import TokenSchema
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm.session import Session
from digirent.app import Application
from digirent.app.social import oauth
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


@router.get("/authorization/google", response_model=TokenSchema)
async def google_authorization(request: Request):
    token = await oauth.google.authorize_access_token(request)
    access_token = token["access_token"]
    id_token = token["id_token"]
    user = await oauth.google.parse_id_token(request, token)
    email = user["email"]
    # email_verified = user["email_verified"]  TODO should unverified emails be allowed?

    return user


@router.get("/google")
async def login_with_google(request: Request):
    redirect_uri = request.url_for("google_authorization")
    return await oauth.google.authorize_redirect(request, redirect_uri)
