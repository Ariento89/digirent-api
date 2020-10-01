from datetime import date, datetime
from typing import Optional, Union
from uuid import UUID, uuid4
from jwt import PyJWTError
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.session import Session

from digirent.database.enums import Gender, HouseType
from .base import ApplicationBase
from .error import ApplicationError
from digirent.database.models import BankDetail, LookingFor, Tenant, User, UserRole


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

    def update_profile(
        self,
        session: Session,
        user: User,
        first_name: str = None,
        last_name: str = None,
        city: str = None,
        phone_number: str = None,
        email: str = None,
        dob: date = None,
        gender: Gender = None,
        description: str = None,
    ):
        try:
            self.user_service.update_user(
                session,
                user.id,
                first_name=first_name,
                last_name=last_name,
                city=city,
                phone_number=phone_number,
                email=email,
                gender=gender,
                dob=dob,
                description=description,
            )
        except IntegrityError as e:
            marker = "unique constraint failed:"
            if marker in str(e).lower():
                raise ApplicationError("Email or Phone Number already exists")
            raise ApplicationError(
                "Invalid data, ensure firstname, lastname, phonenumber, and email are not empty"
            )

    def set_bank_detail(
        self, session: Session, user: User, account_name: str, account_number: str
    ):
        bank_detail = BankDetail(uuid4(), account_name, account_number)
        self.user_service.update_user(session, user.id, bank_detail=bank_detail)

    def update_password(
        self, session: Session, user: User, old_password: str, new_password: str
    ):
        if not self.user_service.password_is_match(old_password, user.hashed_password):
            raise ApplicationError("Wrong password")
        new_hashed_password = self.user_service.hash_password(new_password)
        self.user_service.update_user(
            session, user.id, hashed_password=new_hashed_password
        )

    def set_looking_for(
        self,
        session: Session,
        tenant: Tenant,
        house_type: HouseType,
        city: str,
        max_budget: float,
    ):
        looking_for = LookingFor(tenant.id, house_type, city, max_budget)
        self.user_service.update_user(session, tenant.id, looking_for=looking_for)
