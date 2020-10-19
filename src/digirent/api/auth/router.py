import httpx
from enum import Enum
from fastapi import APIRouter, Depends, HTTPException
from fastapi.requests import Request
from digirent.app.error import ApplicationError
from digirent.database.enums import UserRole
from .schema import TokenSchema
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm.session import Session
from digirent.app import Application
from digirent.app.social import oauth
from .helper import get_token_from_google_auth
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
):
    access_token = await get_token_from_google_auth(
        request, session, app, UserRole.TENANT
    )
    return {"access_token": access_token}


@router.get("/landlord/authorization/google", response_model=TokenSchema)
async def landlord_google_authorization(
    request: Request,
    app: Application = Depends(dependencies.get_application),
    session: Session = Depends(dependencies.get_database_session),
):
    access_token = await get_token_from_google_auth(
        request, session, app, UserRole.LANDLORD
    )
    return {"access_token": access_token}


@router.get("/google")
async def login_with_google(who: SocialAccountLoginWho, request: Request):
    endpoint_name = f"{who.value}_google_authorization"
    redirect_uri = request.url_for(endpoint_name)
    return await oauth.google.authorize_redirect(request, redirect_uri)


@router.get("/facebook")
async def login_with_facebook(who: SocialAccountLoginWho, request: Request):
    endpoint_name = f"{who.value}_facebook_authorization"
    redirect_uri = request.url_for(endpoint_name)
    return await oauth.facebook.authorize_redirect(request, redirect_uri)


@router.get("/landlord/authorization/facebook")
async def landlord_facebook_authorization(request: Request):
    token = await oauth.facebook.authorize_access_token(request)
    access_token = token["access_token"]
    result = None
    async with httpx.AsyncClient() as client:
        result = await client.get(
            "https://graph.facebook.com/me",
            params={
                "fields": ["id", "email", "gender", "name"],
                "access_token": access_token,
            },
        )
    # access_token = token["access_token"]
    # id_token = token["id_token"]
    # user = await oauth.google.parse_id_token(request, token)
    return result.json()


@router.get("/tenant/authorization/facebook")
async def tenant_facebook_authorization(request: Request):
    token = await oauth.facebook.authorize_access_token(request)
    access_token = token["access_token"]
    result = None
    async with httpx.AsyncClient() as client:
        result = await client.get(
            "https://graph.facebook.com/me",
            params={
                "fields": ["id", "email"],
                "access_token": access_token,
            },
        )
    # access_token = token["access_token"]
    # id_token = token["id_token"]
    # user = await oauth.google.parse_id_token(request, token)
    return result.json()
