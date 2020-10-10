from pathlib import Path
from typing import IO, List, Optional
from uuid import UUID, uuid4
from datetime import date
from jwt import PyJWTError
from digirent.core.config import (
    NUMBER_OF_APARTMENT_VIDEOS,
    SUPPORTED_FILE_EXTENSIONS,
    UPLOAD_PATH,
    SUPPORTED_IMAGE_EXTENSIONS,
    NUMBER_OF_APARTMENT_IMAGES,
    SUPPORTED_VIDEO_EXTENSIONS,
)
import digirent.util as util
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.session import Session

from digirent.database.enums import (
    ApartmentApplicationStage,
    BookingRequestStatus,
    Gender,
    HouseType,
)
from .base import ApplicationBase
from .error import ApplicationError
from digirent.database.models import (
    Amenity,
    Apartment,
    ApartmentApplication,
    BankDetail,
    BookingRequest,
    Landlord,
    LookingFor,
    Tenant,
    User,
    UserRole,
)


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
    ) -> User:
        try:
            return self.user_service.update(
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
    ) -> User:
        bank_detail = BankDetail(uuid4(), account_name, account_number)
        return self.user_service.update(session, user, bank_detail=bank_detail)

    def update_password(
        self, session: Session, user: User, old_password: str, new_password: str
    ) -> User:
        if not util.password_is_match(old_password, user.hashed_password):
            raise ApplicationError("Wrong password")
        new_hashed_password = util.hash_password(new_password)
        return self.user_service.update(
            session, user, hashed_password=new_hashed_password
        )

    def set_looking_for(
        self,
        session: Session,
        tenant: Tenant,
        house_type: HouseType,
        city: str,
        max_budget: float,
    ) -> Tenant:
        looking_for = LookingFor(tenant.id, house_type, city, max_budget)
        return self.tenant_service.update(session, tenant, looking_for=looking_for)

    def create_amenity(self, session: Session, title: str) -> Amenity:
        existing_amenity = session.query(Amenity).filter(Amenity.title == title).first()
        if existing_amenity:
            raise ApplicationError("Amenity already exists")
        return self.amenity_service.create(session, title=title)

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
    ) -> Apartment:
        return self.apartment_service.create(
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
    ) -> Apartment:
        apartment = self.apartment_service.get(session, apartment_id)
        if not apartment:
            raise ApplicationError("Apartment not found")
        if apartment.landlord_id != landlord.id:
            raise ApplicationError("Apartment not owned by user")
        if apartment.tenant_id:
            raise ApplicationError("Apartment has been subletted")
        return self.apartment_service.update(session, apartment, **kwargs)

    def __upload_file(
        self, user: User, file: IO, extension: str, folder_path: Path
    ) -> User:
        if extension not in SUPPORTED_FILE_EXTENSIONS:
            raise ApplicationError("Invalid file format")
        possible_filenames = [f"{user.id}.{ext}" for ext in SUPPORTED_FILE_EXTENSIONS]
        for filename in possible_filenames:
            if self.file_service.get(filename, folder_path):
                self.file_service.delete(filename, folder_path)
        filename = f"{user.id}.{extension}"
        self.file_service.store_file(folder_path, filename, file)
        return user

    def upload_copy_id(self, user: User, file: IO, extension: str) -> User:
        return self.__upload_file(user, file, extension, util.get_copy_ids_path())

    def upload_proof_of_income(self, user: User, file: IO, extension: str) -> Tenant:
        return self.__upload_file(
            user, file, extension, util.get_proof_of_income_path()
        )

    def upload_proof_of_enrollment(
        self, user: User, file: IO, extension: str
    ) -> Tenant:
        return self.__upload_file(
            user, file, extension, util.get_proof_of_enrollment_path()
        )

    def upload_apartment_image(
        self, landlord: Landlord, apartment: Apartment, file: IO, filename: str
    ) -> Apartment:
        assert isinstance(landlord, Landlord)
        file_extension = filename.split(".")[-1]
        if file_extension not in SUPPORTED_IMAGE_EXTENSIONS:
            raise ApplicationError("Unsupported image format")
        folder_path = (
            Path(UPLOAD_PATH) / f"apartments/{landlord.id}/{apartment.id}/images"
        )
        files = self.file_service.list_files(folder_path)
        if len(files) == NUMBER_OF_APARTMENT_IMAGES:
            raise ApplicationError("Maximum number of apartment images reached")
        self.file_service.store_file(folder_path, filename, file)
        return apartment

    def upload_apartment_video(
        self, landlord: Landlord, apartment: Apartment, file: IO, filename: str
    ) -> Apartment:
        assert isinstance(landlord, Landlord)
        file_extension = filename.split(".")[-1]
        if file_extension not in SUPPORTED_VIDEO_EXTENSIONS:
            raise ApplicationError("Unsupported video format")
        folder_path = (
            Path(UPLOAD_PATH) / f"apartments/{landlord.id}/{apartment.id}/videos"
        )
        files = self.file_service.list_files(folder_path)
        if len(files) == NUMBER_OF_APARTMENT_VIDEOS:
            raise ApplicationError("Maximum number of apartment vidoes reached")
        self.file_service.store_file(folder_path, filename, file)
        return apartment

    def apply_for_apartment(
        self, session: Session, tenant: Tenant, apartment: Apartment
    ) -> ApartmentApplication:
        awarded_application = (
            session.query(ApartmentApplication)
            .filter(ApartmentApplication.apartment_id == apartment.id)
            .filter(ApartmentApplication.stage == ApartmentApplicationStage.AWARDED)
            .first()
        )
        if awarded_application:
            raise ApplicationError("Apartment has already been awarded")
        existing_application = (
            session.query(ApartmentApplication)
            .filter(ApartmentApplication.apartment_id == apartment.id)
            .filter(ApartmentApplication.tenant_id == tenant.id)
            .one_or_none()
        )

        if existing_application:
            raise ApplicationError("User already applied for this apartment")
        return self.apartment_application_service.create(
            session, tenant=tenant, apartment=apartment
        )

    def reject_tenant_application(
        self,
        session: Session,
        landlord: Landlord,
        tenant_application: ApartmentApplication,
    ) -> ApartmentApplication:
        apartment: Apartment = tenant_application.apartment
        if apartment.landlord_id != landlord.id:
            raise ApplicationError("Apartment not owned by landlord")
        return self.apartment_application_service.update(
            session, tenant_application, stage=ApartmentApplicationStage.REJECTED
        )

    def consider_tenant_application(
        self,
        session: Session,
        landlord: Landlord,
        tenant_application: ApartmentApplication,
    ) -> ApartmentApplication:
        apartment: Apartment = tenant_application.apartment
        if apartment.landlord_id != landlord.id:
            raise ApplicationError("Apartment not owned by landlord")
        return self.apartment_application_service.update(
            session, tenant_application, stage=ApartmentApplicationStage.CONSIDERED
        )

    def accept_tenant_application(
        self,
        session: Session,
        landlord: Landlord,
        tenant_application: ApartmentApplication,
    ) -> ApartmentApplication:
        apartment: Apartment = tenant_application.apartment
        if tenant_application.stage != ApartmentApplicationStage.CONSIDERED:
            raise ApplicationError("Application has not yet been considered")
        if apartment.landlord_id != landlord.id:
            raise ApplicationError("Apartment not owned by landlord")
        for tenant_app in tenant_application.apartment.applications:
            if tenant_app.id != tenant_application.id:
                self.apartment_application_service.update(
                    session, tenant_app, False, stage=ApartmentApplicationStage.REJECTED
                )
        return self.apartment_application_service.update(
            session, tenant_application, stage=ApartmentApplicationStage.AWARDED
        )

    def invite_tenant_to_apply(
        self,
        session: Session,
        landlord: Landlord,
        tenant: Tenant,
        apartment: Apartment,
    ) -> BookingRequest:
        if apartment.landlord_id != landlord.id:
            raise ApplicationError("Landlord does not own apartment")
        return self.booking_request_service.create(
            session, apartment_id=apartment.id, tenant_id=tenant.id
        )

    def accept_application_invitation(
        self, session: Session, tenant: Tenant, booking_request: BookingRequest
    ):
        if booking_request.tenant_id != tenant.id:
            raise ApplicationError("Request not for tenant")
        if booking_request.status == BookingRequestStatus.REJECTED:
            raise ApplicationError("Invitation has been rejected")
        apartment_application = self.apartment_application_service.create(
            session,
            apartment=booking_request.apartment,
            tenant=booking_request.tenant,
            commit=False,
        )
        booking_request.accept(apartment_application)
        session.commit()
        return booking_request

    def reject_application_invitation(
        self,
        session: Session,
        tenant: Tenant,
        booking_request: BookingRequest,
    ):
        if booking_request.tenant_id != tenant.id:
            raise ApplicationError("Request not for tenant")
        if booking_request.status == BookingRequestStatus.ACCEPTED:
            raise ApplicationError("Invitation has been accepted")
        booking_request.reject()
        session.commit()
        return booking_request
