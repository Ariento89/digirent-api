from fastapi import Depends, HTTPException
from fastapi import status as status
from fastapi.security import OAuth2PasswordBearer
from jwt import PyJWTError
from digirent.app import Application
from digirent.app.container import ApplicationContainer
from sqlalchemy.orm.session import Session
from digirent.app.error import ApplicationError
from digirent.database.models import User, UserRole
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
    except ApplicationError:
        raise credentials_exception
    return user


async def get_current_active_user(current_user: User = Depends(get_current_user)):
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


async def get_current_admin_user(
    current_user: User = Depends(get_current_user),
) -> User:
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Forbidden")
    return current_user


async def get_current_active_admin_user(
    current_admin: User = Depends(get_current_admin_user),
):
    if not current_admin.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_admin


async def get_current_regular_user(
    current_user: User = Depends(get_current_user),
) -> User:
    if current_user.role != UserRole.REGULAR:
        raise HTTPException(status_code=403, detail="Forbidden")
    return current_user


async def get_current_active_regular_user(
    current_user: User = Depends(get_current_regular_user),
):
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user
