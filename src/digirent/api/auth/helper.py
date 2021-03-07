import jwt
import httpx
from fastapi.requests import Request
from sqlalchemy.orm.session import Session
from digirent.database.enums import UserRole
from digirent.app.social import oauth
from digirent.app import Application
from digirent.database.models import User
from digirent.core import config
from itsdangerous.url_safe import URLSafeSerializer

from digirent.util import generate_apple_client_secret

serializer = URLSafeSerializer(secret_key=config.SECRET_KEY, salt=config.SALT)


def generate_state(access_token: str, who: str, social: str) -> str:
    assert who in ["tenant", "landlord"]
    assert social in ["google", "facebook", "apple"]
    state = serializer.dumps(
        {"access_token": access_token, "who": who, "social": social}
    )
    return f"{social}.{state}"


def get_payload_from_state(state: str) -> dict:
    _, serialized_state = state.split(".", maxsplit=1)
    return serializer.loads(serialized_state)


async def get_token_from_google_auth(
    request: Request,
    session: Session,
    app: Application,
    role: UserRole,
    authenticated_user: User,
) -> bytes:
    token = await oauth.google.authorize_access_token(request)
    access_token = token["access_token"]
    id_token = token["id_token"]
    user = await oauth.google.parse_id_token(request, token)
    name: str = user["name"]
    first_name, last_name = name.split(" ", maxsplit=1)
    email = user["email"]
    # email_verified = user["email_verified"]  TODO should unverified emails be allowed?
    access_token = app.authenticate_google(
        session,
        access_token,
        id_token,
        email,
        first_name,
        last_name,
        role,
        authenticated_user,
    )
    return access_token


async def get_token_from_facebook_auth(
    request: Request,
    session: Session,
    app: Application,
    role: UserRole,
    authenticated_user: User,
) -> bytes:
    token = await oauth.facebook.authorize_access_token(request)
    access_token = token["access_token"]
    facebook_user = None
    async with httpx.AsyncClient() as client:
        result = await client.get(
            "https://graph.facebook.com/me",
            params={
                "fields": "id,email,gender,name",
                "access_token": access_token,
            },
        )
        facebook_user = result.json()
    facebook_user_id = facebook_user["id"]
    firstname, lastname = facebook_user["name"].split(" ", maxsplit=1)
    email = facebook_user["email"]
    access_token = app.authenticate_facebook(
        session,
        facebook_user_id,
        access_token,
        email,
        firstname,
        lastname,
        role,
        authenticated_user,
    )
    return access_token


async def get_token_from_apple_auth(
    request: Request,
    session: Session,
    app: Application,
    role: UserRole,
    authenticated_user: User,
) -> bytes:
    print("about to get access token from apple auth")
    async with httpx.AsyncClient() as client:
        data = {
            "grant_type": "authorization_code",
            "code": request.query_params["code"].encode("ascii"),
            "redirect_uri": config.CLIENT_APPLE_AUTH_URL,
            "client_id": config.APPLE_CLIENT_ID,
            "client_secret": generate_apple_client_secret(),
        }
        resp = await client.post("https://appleid.apple.com/auth/token", data=data)
        resp_data = resp.json()
        access_token = resp_data["access_token"]
        id_token = resp_data["id_token"]
        headers = jwt.get_unverified_header(id_token)
        claims = jwt.decode(id_token, "", verify=False)
        print("\n\n\n\n\n\n")
        print(resp.json())
        print(headers)
        print(claims)
        print("\n\n\n\n\n\n")
    # name: str = user["name"]
    # first_name, last_name = name.split(" ", maxsplit=1)
    # email = user["email"]
    # # email_verified = user["email_verified"]  TODO should unverified emails be allowed?
    # access_token = app.authenticate_google(
    #     session,
    #     access_token,
    #     id_token,
    #     email,
    #     first_name,
    #     last_name,
    #     role,
    #     authenticated_user,
    # )
    return access_token
