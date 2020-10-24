from typing import Optional
from enum import Enum
from fastapi import APIRouter, Depends, HTTPException
from fastapi.requests import Request
from digirent.app.error import ApplicationError
from digirent.database.enums import UserRole
from digirent.database.models import User
from .schema import TokenSchema
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm.session import Session
from digirent.app import Application
from digirent.app.social import oauth
from .helper import get_token_from_facebook_auth, get_token_from_google_auth
import digirent.api.dependencies as dependencies


class SocialAccountLoginWho(str, Enum):
    TENANT = "tenant"
    LANDLORD = "landlord"


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


@router.get("/tenant/authorization/google", response_model=TokenSchema)
async def tenant_google_authorization(
    request: Request,
    app: Application = Depends(dependencies.get_application),
    session: Session = Depends(dependencies.get_database_session),
    user: Optional[User] = Depends(dependencies.get_optional_current_user_from_state),
):
    try:
        access_token = await get_token_from_google_auth(
            request, session, app, UserRole.TENANT, user
        )
        return {"access_token": access_token}
    except ApplicationError as e:
        raise HTTPException(400, str(e))


@router.get("/landlord/authorization/google", response_model=TokenSchema)
async def landlord_google_authorization(
    request: Request,
    app: Application = Depends(dependencies.get_application),
    session: Session = Depends(dependencies.get_database_session),
    user: Optional[User] = Depends(dependencies.get_optional_current_user_from_state),
):
    try:
        access_token = await get_token_from_google_auth(
            request, session, app, UserRole.LANDLORD, user
        )
        return {"access_token": access_token}
    except ApplicationError as e:
        raise HTTPException(400, str(e))


@router.get("/google")
async def login_with_google(
    who: SocialAccountLoginWho,
    request: Request,
    token: Optional[str] = Depends(dependencies.get_optional_current_user_token),
):
    endpoint_name = f"{who.value}_google_authorization"
    redirect_uri = request.url_for(endpoint_name)
    state = token or " "
    return await oauth.google.authorize_redirect(request, redirect_uri, state=state)


@router.get("/facebook")
async def login_with_facebook(
    who: SocialAccountLoginWho,
    request: Request,
    token: Optional[str] = Depends(dependencies.get_optional_current_user_token),
):
    endpoint_name = f"{who.value}_facebook_authorization"
    redirect_uri = request.url_for(endpoint_name)
    state = token or " "
    return await oauth.facebook.authorize_redirect(request, redirect_uri, state=state)


@router.get("/landlord/authorization/facebook")
async def landlord_facebook_authorization(
    request: Request,
    app: Application = Depends(dependencies.get_application),
    session: Session = Depends(dependencies.get_database_session),
    user: Optional[User] = Depends(dependencies.get_optional_current_user_from_state),
):
    try:
        access_token = await get_token_from_facebook_auth(
            request, session, app, UserRole.LANDLORD, user
        )
        return {"access_token": access_token}
    except ApplicationError as e:
        raise HTTPException(400, str(e))


@router.get("/tenant/authorization/facebook")
async def tenant_facebook_authorization(
    request: Request,
    app: Application = Depends(dependencies.get_application),
    session: Session = Depends(dependencies.get_database_session),
    user: Optional[User] = Depends(dependencies.get_optional_current_user_from_state),
):
    try:
        access_token = await get_token_from_facebook_auth(
            request, session, app, UserRole.TENANT, user
        )
        return {"access_token": access_token}
    except ApplicationError as e:
        raise HTTPException(400, str(e))
