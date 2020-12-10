from typing import Optional
from enum import Enum
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.param_functions import Body
from fastapi.requests import Request
from jwt import PyJWTError
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
from digirent import util
from digirent.core import config


PASSWORD_RESET_TOKEN_VALUE = "password_reset"


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


@router.post("/forgot-password")
def forgot_password(
    background: BackgroundTasks,
    email: str = Body(...),
    session: Session = Depends(dependencies.get_database_session),
):
    user_with_email = session.query(User).filter(User.email == email).one_or_none()
    if user_with_email:
        password_reset_token = util.create_access_token(
            {"type": PASSWORD_RESET_TOKEN_VALUE, "email": email}
        )
        url = f"{config.CLIENT_HOST}/forgot-password?token={password_reset_token}"
        email_str = f"Follow this link to reset password {url}"
        background.add_task(
            util.send_email,
            to=email,
            subject="Reset Digirent Password",
            message=email_str,
        )


@router.post("/reset-password")
def reset_password(
    token: str = Body(...),
    email: str = Body(...),
    password: str = Body(...),
    session: Session = Depends(dependencies.get_database_session),
):
    error = HTTPException(400, "Invalid token")
    user_with_email: User = (
        session.query(User).filter(User.email == email).one_or_none()
    )
    if not user_with_email:
        raise HTTPException(404, "User not found")
    try:
        payload = util.get_payload_from_token(token)
        token_type = payload["type"]
        if token_type != PASSWORD_RESET_TOKEN_VALUE:
            raise error
        token_email = payload["email"]
        if token_email != user_with_email.email:
            raise error
        user_password = util.hash_password(password)
        user_with_email.hashed_password = user_password
        session.commit()
    except PyJWTError:
        raise error
    except KeyError:
        raise error


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
