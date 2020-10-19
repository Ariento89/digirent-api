from typing import Optional, Union
from fastapi import Depends, HTTPException
from fastapi import status as status
from fastapi.param_functions import Header, Query
from fastapi.security import OAuth2PasswordBearer
from digirent.app import Application
from digirent.app.container import ApplicationContainer
from sqlalchemy.orm.session import Session
from digirent.app.error import ApplicationError
from digirent.database.models import Admin, Landlord, Tenant, User, UserRole
from digirent.database.base import SessionLocal

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/")


def get_database_session() -> Session:
    session: Session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def get_application() -> Application:
    return ApplicationContainer.app()


async def get_current_user(
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
        user: User = application.authenticate_token(session, token)
        if user.role == UserRole.ADMIN:
            user = session.query(Admin).get(user.id)
        elif user.role == UserRole.TENANT:
            user = session.query(Tenant).get(user.id)
        elif user.role == UserRole.LANDLORD:
            user = session.query(Landlord).get(user.id)
    except ApplicationError:
        raise credentials_exception
    return user


async def get_current_active_user(current_user: User = Depends(get_current_user)):
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


async def get_current_admin_user(
    current_user: User = Depends(get_current_user),
) -> Admin:
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Forbidden")
    return current_user


async def get_current_active_admin_user(
    current_admin: User = Depends(get_current_admin_user),
) -> Admin:
    if not current_admin.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_admin


async def get_current_tenant(
    current_user: User = Depends(get_current_user),
) -> Tenant:
    if current_user.role != UserRole.TENANT:
        raise HTTPException(status_code=403, detail="Forbidden")
    return current_user


async def get_current_active_tenant(
    current_tenant: Tenant = Depends(get_current_tenant),
) -> Tenant:
    if not current_tenant.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_tenant


async def get_current_landlord(
    current_user: User = Depends(get_current_user),
) -> Landlord:
    if current_user.role != UserRole.LANDLORD:
        raise HTTPException(status_code=403, detail="Forbidden")
    return current_user


async def get_current_active_landlord(
    current_landlord: Landlord = Depends(get_current_landlord),
) -> Landlord:
    if not current_landlord.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_landlord


async def get_current_non_admin_user(
    current_user: User = Depends(get_current_user),
) -> Union[Landlord, Tenant]:
    if current_user.role == UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Forbidden")
    return current_user


async def get_current_active_non_admin_user(
    current_non_admin_user: Union[Landlord, Tenant] = Depends(
        get_current_non_admin_user
    ),
) -> Union[Landlord, Tenant]:
    if not current_non_admin_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_non_admin_user


async def get_current_admin_or_tenant(
    current_user: User = Depends(get_current_user),
) -> Union[Admin, Tenant]:
    if current_user.role not in [UserRole.TENANT, UserRole.ADMIN]:
        raise HTTPException(status_code=403, detail="Forbidden")
    return current_user


async def get_current_active_admin_or_tenant(
    current_admin_or_tenant: Union[Admin, Tenant] = Depends(get_current_admin_or_tenant)
):
    if not current_admin_or_tenant.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_admin_or_tenant


async def get_current_admin_or_landlord(
    current_user: User = Depends(get_current_user),
) -> Union[Admin, Tenant]:
    if current_user.role not in [UserRole.LANDLORD, UserRole.ADMIN]:
        raise HTTPException(status_code=403, detail="Forbidden")
    return current_user


async def get_current_active_admin_or_landlord(
    current_admin_or_landlord: Union[Admin, Landlord] = Depends(
        get_current_admin_or_landlord
    )
):
    if not current_admin_or_landlord.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_admin_or_landlord


async def get_optional_current_user_token(
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
        user: User = application.authenticate_token(session, state)
        if user.role == UserRole.ADMIN:
            user = session.query(Admin).get(user.id)
        elif user.role == UserRole.TENANT:
            user = session.query(Tenant).get(user.id)
        elif user.role == UserRole.LANDLORD:
            user = session.query(Landlord).get(user.id)
    except ApplicationError:
        raise credentials_exception
    return user
