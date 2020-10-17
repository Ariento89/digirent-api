from fastapi.requests import Request
from sqlalchemy.orm.session import Session
from digirent.database.enums import UserRole
from digirent.app.social import oauth
from digirent.app import Application


async def get_token_from_google_auth(
    request: Request, session: Session, app: Application, role: UserRole
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
        session, access_token, id_token, email, first_name, last_name, role
    )
    return access_token
