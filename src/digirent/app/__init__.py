from datetime import date, datetime
from typing import Optional, Union
from jwt import PyJWTError
from sqlalchemy.orm.session import Session
from .base import ApplicationBase
from .error import ApplicationError
from digirent.database.models import User, UserRole


class Application(ApplicationBase):
    def create_tenant(
        self,
        session: Session,
        first_name: str,
        last_name: str,
        dob: date,
        email: str,
        phone_number: str,
        password: str,
    ):
        user: User = self.user_service.create_user(
            session,
            first_name,
            last_name,
            dob,
            email,
            phone_number,
            password,
            UserRole.TENANT,
        )
        if isinstance(user, str):
            raise ApplicationError(user)
        return user

    def create_landlord(
        self,
        session: Session,
        first_name: str,
        last_name: str,
        email: str,
        phone_number: str,
        password: str,
    ):
        user: User = self.user_service.create_user(
            session,
            first_name,
            last_name,
            None,
            email,
            phone_number,
            password,
            UserRole.LANDLORD,
        )
        if isinstance(user, str):
            raise ApplicationError(user)
        return user

    def create_admin(
        self,
        session: Session,
        first_name: str,
        last_name: str,
        email: str,
        phone_number: str,
        password: str,
    ):
        user: User = self.user_service.create_user(
            session,
            first_name,
            last_name,
            None,
            email,
            phone_number,
            password,
            UserRole.ADMIN,
        )
        if isinstance(user, str):
            raise ApplicationError(user)
        return user

    def authenticate_user(self, session: Session, login: str, password: str) -> bytes:
        token = self.auth_service.authenticate(session, login, password)
        if not token:
            raise ApplicationError("Invalid login credentials")
        return token

    def authenticate_token(self, session: Session, token: bytes) -> User:
        try:
            user = self.auth_service.authenticate_token(session, token)
            if not user:
                raise ApplicationError("Invalid token")
            return user
        except PyJWTError:
            raise ApplicationError("Invalid token")
