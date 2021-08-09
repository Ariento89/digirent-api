import jwt
from typing import Optional, Union
from fastapi import Depends, HTTPException, Request, WebSocket
from fastapi import status
from fastapi.param_functions import Header, Query
from fastapi.security import OAuth2PasswordBearer
from digirent.api.chat.chat import ChatManager
from digirent.app import Application
from digirent.app.container import ApplicationContainer
from sqlalchemy.orm.session import Session
from digirent.app.error import ApplicationError
from digirent.core import config
from digirent.database.models import Admin, Landlord, Tenant, User, UserRole
from digirent.database.base import SessionLocal
from itsdangerous.url_safe import URLSafeSerializer
from itsdangerous.exc import BadSignature

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/")
admin_oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/admin/auth/")
serializer = URLSafeSerializer(secret_key=config.SECRET_KEY, salt=config.SALT)


def get_database_session() -> Session:
    session: Session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def get_application() -> Application:
    return ApplicationContainer.app()


def get_current_user(
    token: bytes = Depends(oauth2_scheme),
    session: Session = Depends(get_database_session),
    application: Application = Depends(get_application),
) -> User:
    # todo? change to application method instead of service method?
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        user: User = application.authenticate_user_token(session, token)
        if user is None:
            raise credentials_exception
    except jwt.PyJWTError:
        raise credentials_exception
    except jwt.ExpiredSignatureError:
        raise credentials_exception
    return user


def get_current_active_user(current_user: User = Depends(get_current_user)):
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


def get_current_admin_user(
    token: bytes = Depends(admin_oauth2_scheme),
    session: Session = Depends(get_database_session),
    application: Application = Depends(get_application),
) -> Admin:
    # todo? change to application method instead of service method?
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        admin: Admin = application.authenticate_admin_token(session, token)
        if admin is None:
            raise credentials_exception
    except jwt.PyJWTError:
        raise credentials_exception
    except jwt.ExpiredSignatureError:
        raise credentials_exception
    return admin


def get_current_active_admin_user(
    current_admin: User = Depends(get_current_admin_user),
) -> Admin:
    if not current_admin.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_admin


def get_current_tenant(
    current_user: User = Depends(get_current_user),
) -> Tenant:
    if current_user.role != UserRole.TENANT:
        raise HTTPException(status_code=403, detail="Forbidden")
    return current_user


def get_current_active_tenant(
    current_tenant: Tenant = Depends(get_current_tenant),
) -> Tenant:
    if not current_tenant.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_tenant


def get_current_landlord(
    current_user: User = Depends(get_current_user),
) -> Landlord:
    if current_user.role != UserRole.LANDLORD:
        raise HTTPException(status_code=403, detail="Forbidden")
    return current_user


def get_current_active_landlord(
    current_landlord: Landlord = Depends(get_current_landlord),
) -> Landlord:
    if not current_landlord.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_landlord


def get_current_non_admin_user(
    current_user: User = Depends(get_current_user),
) -> Union[Landlord, Tenant]:
    if current_user.role == UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Forbidden")
    return current_user


def get_current_active_non_admin_user(
    current_non_admin_user: Union[Landlord, Tenant] = Depends(
        get_current_non_admin_user
    ),
) -> Union[Landlord, Tenant]:
    if not current_non_admin_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_non_admin_user


def get_current_admin_or_tenant(
    current_user: User = Depends(get_current_user),
) -> Union[Admin, Tenant]:
    if current_user.role not in [UserRole.TENANT, UserRole.ADMIN]:
        raise HTTPException(status_code=403, detail="Forbidden")
    return current_user


def get_current_active_admin_or_tenant(
    current_admin_or_tenant: Union[Admin, Tenant] = Depends(get_current_admin_or_tenant)
):
    if not current_admin_or_tenant.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_admin_or_tenant


def get_current_admin_or_landlord(
    current_user: User = Depends(get_current_user),
) -> Union[Admin, Tenant]:
    if current_user.role not in [UserRole.LANDLORD, UserRole.ADMIN]:
        raise HTTPException(status_code=403, detail="Forbidden")
    return current_user


def get_current_active_admin_or_landlord(
    current_admin_or_landlord: Union[Admin, Landlord] = Depends(
        get_current_admin_or_landlord
    )
):
    if not current_admin_or_landlord.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_admin_or_landlord


def get_optional_current_user_token(
    authorization: Optional[str] = Header(None),
):
    """
    Get and return authenticated user's access token if one is passed
    """
    if not authorization:
        return
    if "Bearer" not in authorization:
        raise HTTPException(401, "Not authenticated")
    return authorization.split("Bearer")[-1].strip()


def get_optional_current_user(
    token: Optional[str] = Depends(get_optional_current_user_token),
    session: Session = Depends(get_database_session),
    application: Application = Depends(get_application),
):
    """Get optional user from token if token in request"""
    if token is None:
        return
    try:
        user = application.authenticate_token(session, token)
        if user.role == UserRole.ADMIN:
            user = session.query(Admin).get(user.id)
        elif user.role == UserRole.TENANT:
            user = session.query(Tenant).get(user.id)
        elif user.role == UserRole.LANDLORD:
            user = session.query(Landlord).get(user.id)
        return user
    except jwt.PyJWTError:
        raise HTTPException(401, "invalid authorization token")


def get_optional_current_landlord(
    user: Optional[str] = Depends(get_optional_current_user),
):
    """Get optional active user from token if token in request"""
    if user is None:
        return
    if user.role != UserRole.LANDLORD:
        raise HTTPException(status_code=403, detail="Forbidden")
    return user


def get_optional_current_tenant(
    user: Optional[str] = Depends(get_optional_current_user),
):
    """Get optional active user from token if token in request"""
    if user is None:
        return
    if user.role != UserRole.TENANT:
        raise HTTPException(status_code=403, detail="Forbidden")
    return user


def get_optional_current_active_user(
    user: Optional[str] = Depends(get_optional_current_user),
):
    """Get optional active user from token if token in request"""
    if user is None:
        return
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return user


def get_optional_current_active_landlord(
    user: Optional[str] = Depends(get_optional_current_active_user),
):
    """Get optional active user from token if token in request"""
    if user is None:
        return
    if user.role != UserRole.LANDLORD:
        raise HTTPException(status_code=400, detail="Inactive user")
    return user


def get_optional_current_active_tenant(
    user: Optional[str] = Depends(get_optional_current_active_user),
):
    """Get optional active user from token if token in request"""
    if user is None:
        return
    if user.role != UserRole.TENANT:
        raise HTTPException(status_code=400, detail="Inactive user")
    return user


def get_optional_current_user_from_state(
    session: Session = Depends(get_database_session),
    application: Application = Depends(get_application),
    state: Optional[str] = Query(None),
):
    """
    Get and return user from state query parameter if any
    """
    if not state or state.strip() == "":
        return
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        splitted_state = state.split(".", 1)
        if len(splitted_state) < 2:
            raise credentials_exception
        print("\n\n\nabout to get payload from state")
        payload_from_state = serializer.loads(splitted_state[1])
        print("\n\n\n\n\n payload from state is")
        print(payload_from_state)
        print("\n\n\n\n\n")
        access_token = payload_from_state["access_token"]
        if not access_token:
            return
        user: User = application.authenticate_token(session, access_token)
        if user.role == UserRole.ADMIN:
            user = session.query(Admin).get(user.id)
        elif user.role == UserRole.TENANT:
            user = session.query(Tenant).get(user.id)
        elif user.role == UserRole.LANDLORD:
            user = session.query(Landlord).get(user.id)
    except ApplicationError:
        raise credentials_exception
    except BadSignature as be:
        print("\n\n\n\n\n bad signature error")
        print(be)
        print("\n\n\n\n")
        raise credentials_exception
    except KeyError:
        raise credentials_exception
    return user


def get_user_websocket_from_request(
    request: Request,
    user: User = Depends(get_current_user),
) -> Optional[WebSocket]:
    manager: ChatManager = request.get("room_manager")
    return manager.chat_users.get(user.id)
