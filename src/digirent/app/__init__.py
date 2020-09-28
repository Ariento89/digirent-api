from typing import Optional, Union
from jwt import PyJWTError
from sqlalchemy.orm.session import Session
from .base import ApplicationBase
from .error import ApplicationError
from digirent.database.models import User, UserRole


class Application(ApplicationBase):
    def create_user(
        self,
        session: Session,
        first_name: str,
        last_name: str,
        username: str,
        email: str,
        phone_number: str,
        password: str,
        role: UserRole = UserRole.REGULAR,
    ) -> User:
        result: Union[str, User] = self.user_service.create_user(
            session,
            first_name,
            last_name,
            username,
            email,
            phone_number,
            password,
            role,
        )
        if isinstance(result, str):
            raise ApplicationError(result)
        return result

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
