from pathlib import Path
from typing import IO, List, Optional
from uuid import UUID, uuid4
from datetime import date
from jwt import PyJWTError
from digirent.core.config import UPLOAD_PATH
import digirent.util as util
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.session import Session

from digirent.database.enums import Gender, HouseType
from .base import ApplicationBase
from .error import ApplicationError
from digirent.database.models import (
    Amenity,
    Apartment,
    BankDetail,
    Landlord,
    LookingFor,
    Tenant,
    User,
    UserRole,
)


SUPPORTED_FILE_EXTENSIONS = ["pdf", "doc", "docx"]


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
    ) -> Tenant:
        hashed_password = util.hash_password(password)
        return self.tenant_service.create(
            session,
            first_name=first_name,
            last_name=last_name,
            dob=dob,
            email=email,
            phone_number=phone_number,
            hashed_password=hashed_password,
        )

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
        hashed_password = util.hash_password(password)
        return self.landlord_service.create(
            session,
            first_name=first_name,
            last_name=last_name,
            dob=dob,
            email=email,
            phone_number=phone_number,
            hashed_password=hashed_password,
        )

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
        hashed_password = util.hash_password(password)
        return self.admin_service.create(
            session,
            first_name=first_name,
            last_name=last_name,
            dob=dob,
            email=email,
            phone_number=phone_number,
            hashed_password=hashed_password,
        )

    def authenticate_user(self, session: Session, login: str, password: str) -> bytes:
        existing_user: Optional[User] = self.user_service.get_by_email(
            session, login
        ) or self.user_service.get_by_phone_number(session, login)
        if not existing_user:
            raise ApplicationError("Invalid login credentials")
        if not util.password_is_match(password, existing_user.hashed_password):
            raise ApplicationError("Invalid login credentials")
        return util.create_access_token(data={"sub": str(existing_user.id)})

    def authenticate_token(self, session: Session, token: bytes) -> User:
        try:
            user_id: str = util.decode_access_token(token)
            return self.user_service.get(session, UUID(user_id))
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
            self.user_service.update(
                session,
                user,
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
        self.user_service.update(session, user, bank_detail=bank_detail)

    def update_password(
        self, session: Session, user: User, old_password: str, new_password: str
    ):
        if not util.password_is_match(old_password, user.hashed_password):
            raise ApplicationError("Wrong password")
        new_hashed_password = util.hash_password(new_password)
        self.user_service.update(session, user, hashed_password=new_hashed_password)

    def set_looking_for(
        self,
        session: Session,
        tenant: Tenant,
        house_type: HouseType,
        city: str,
        max_budget: float,
    ):
        looking_for = LookingFor(tenant.id, house_type, city, max_budget)
        self.tenant_service.update(session, tenant, looking_for=looking_for)

    def create_amenity(self, session: Session, title: str):
        existing_amenity = session.query(Amenity).filter(Amenity.title == title).first()
        if existing_amenity:
            raise ApplicationError("Amenity already exists")
        self.amenity_service.create(session, title=title)

    def create_apartment(
        self,
        session: Session,
        landlord: Landlord,
        name: str,
        monthly_price: float,
        utilities_price: float,
        address: str,
        country: str,
        state: str,
        city: str,
        description: str,
        house_type: HouseType,
        bedrooms: int,
        bathrooms: int,
        size: float,
        furnish_type: str,
        available_from: date,
        available_to: date,
        amenities: List[Amenity],
    ):
        self.apartment_service.create(
            session,
            amenities=amenities,
            landlord=landlord,
            name=name,
            monthly_price=monthly_price,
            utilities_price=utilities_price,
            address=address,
            country=country,
            state=state,
            city=city,
            description=description,
            house_type=house_type,
            bedrooms=bedrooms,
            bathrooms=bathrooms,
            size=size,
            furnish_type=furnish_type,
            available_from=available_from,
            available_to=available_to,
        )

    def update_apartment(
        self, session: Session, landlord: Landlord, apartment_id: UUID, **kwargs
    ):
        apartment = self.apartment_service.get(session, apartment_id)
        if not apartment:
            raise ApplicationError("Apartment not found")
        if apartment.landlord_id != landlord.id:
            raise ApplicationError("Apartment not owned by user")
        if apartment.tenant_id:
            raise ApplicationError("Apartment has been subletted")
        self.apartment_service.update(session, apartment, **kwargs)

    def __upload_file(self, user: User, file: IO, extension: str, foldername: str):
        if extension not in SUPPORTED_FILE_EXTENSIONS:
            raise ApplicationError("Invalid file format")
        folder_path = Path(UPLOAD_PATH) / foldername
        possible_filenames = [f"{user.id}.{ext}" for ext in SUPPORTED_FILE_EXTENSIONS]
        for filename in possible_filenames:
            if self.file_service.get(filename, folder_path):
                self.file_service.delete(filename, folder_path)
        filename = f"{user.id}.{extension}"
        self.file_service.store_file(folder_path, filename, file)

    def upload_copy_id(self, user: User, file: IO, extension: str):
        return self.__upload_file(user, file, extension, "copy_ids")

    def upload_proof_of_income(self, user: User, file: IO, extension: str):
        return self.__upload_file(user, file, extension, "proof_of_income")

    def upload_proof_of_enrollment(self, user: User, file: IO, extension: str):
        return self.__upload_file(user, file, extension, "proof_of_enrollment")
