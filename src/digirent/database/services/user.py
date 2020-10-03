from typing import Optional
from sqlalchemy.orm.session import Session
from .base import DBService
from ..models import User


class UserService(DBService[User]):
    def __init__(self) -> None:
        super().__init__(User)

    def get_by_email(self, session: Session, email: str) -> Optional[User]:
        return session.query(User).filter(User.email == email).first()

    def get_by_phone_number(
        self, session: Session, phone_number: str
    ) -> Optional[User]:
        return session.query(User).filter(User.phone_number == phone_number).first()
