from datetime import date, datetime
from typing import Optional, Union
from uuid import UUID
from digirent.database.models import Admin, Landlord, Tenant, User, UserRole
from sqlalchemy.orm.session import Session
from passlib.context import CryptContext


class UserService:
    def __init__(self) -> None:
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    def get_user_by_id(self, session: Session, id: UUID) -> Optional[User]:
        return session.query(User).get(id)

    def get_user_by_email(self, session: Session, email: str) -> Optional[User]:
        return session.query(User).filter(User.email == email).first()

    def get_user_by_phone_number(
        self, session: Session, phone_number: str
    ) -> Optional[User]:
        return session.query(User).filter(User.phone_number == phone_number).first()

    def create_user(
        self,
        session: Session,
        first_name: str,
        last_name: str,
        dob: date,
        email: str,
        phone_number: str,
        password: str,
        role: UserRole,
        commit: bool = True,
    ) -> Union[str, User]:
        if self.get_user_by_email(session, email):
            return f"Email taken"
        if self.get_user_by_phone_number(session, phone_number):
            return f"Phone number taken"
        hashed_password = self.hash_password(password)
        new_user: User = User(
            first_name=first_name,
            last_name=last_name,
            dob=dob,
            email=email,
            phone_number=phone_number,
            hashed_password=hashed_password,
        )
        new_user.role = role
        session.add(new_user)
        if commit:
            session.commit()
        return new_user

    def password_is_match(self, plain_password: str, hashed_password: str):
        return self.pwd_context.verify(plain_password, hashed_password)

    def hash_password(self, plain_password: str):
        return self.pwd_context.hash(plain_password)
