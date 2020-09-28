from typing import Optional, Union
from uuid import UUID
from sqlalchemy.orm.session import Session
from digirent.database.models import User
import digirent.util as util
from .user import UserService


class AuthService:
    def __init__(self, user_service: UserService) -> None:
        self.user_service: UserService = user_service

    def authenticate_token(self, session: Session, token: bytes) -> Optional[User]:
        # scenario: user_id not UUID
        user_id: str = util.decode_access_token(token)
        return self.user_service.get_user_by_id(session, UUID(user_id))

    def authenticate(
        self, session: Session, login: str, password: str
    ) -> Optional[bytes]:
        existing_user: Optional[User] = (
            self.user_service.get_user_by_email(session, login)
            or self.user_service.get_user_by_username(session, login)
            or self.user_service.get_user_by_phone_number(session, login)
        )
        if not existing_user:
            return
        if not self.user_service.password_is_match(
            password, existing_user.hashed_password
        ):
            return
        return util.create_access_token(data={"sub": str(existing_user.id)})
