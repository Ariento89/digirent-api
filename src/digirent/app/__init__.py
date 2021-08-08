from pathlib import Path
from typing import IO, List, Optional, Union
from uuid import UUID, uuid4
from datetime import date, datetime
from jwt import PyJWTError
from digirent.core import config
import digirent.util as util
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.session import Session
from sqlalchemy import or_

from digirent.database.enums import (
    ApartmentApplicationStatus,
    BookingRequestStatus,
    ContractStatus,
    Gender,
    HouseType,
    InvoiceStatus,
    InvoiceType,
    SocialAccountType,
)
from .base import ApplicationBase
from .error import ApplicationError
from digirent.database.models import (
    Amenity,
    Apartment,
    ApartmentApplication,
    BankDetail,
    BookingRequest,
    Contract,
    Invoice,
    Landlord,
    LookingFor,
    SocialAccount,
    Tenant,
    User,
    UserRole,
)
from digirent.core.services.sign_request import send_contract_sign_request
from mollie.api.client import Client


mollie_client = Client()
mollie_client.set_api_key(config.MOLLIE_API_KEY)


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

    def authenticate_user(self, session: Session, email: str, password: str) -> bytes:
        existing_user: Optional[User] = (
            session.query(User)
            .filter(User.role != UserRole.ADMIN)
            .filter(User.email == email)
            .one_or_none()
        )
        if not existing_user:
            raise ApplicationError("Invalid login credentials")
        if not util.password_is_match(password, existing_user.hashed_password):
            raise ApplicationError("Invalid login credentials")
        return util.create_access_token(data={"sub": str(existing_user.id)})

    def authenticate_admin(self, session: Session, email: str, password: str) -> bytes:
        existing_user: Optional[User] = (
            session.query(User)
            .filter(User.role == UserRole.ADMIN)
            .filter(User.email == email)
            .one_or_none()
        )
        if not existing_user:
            raise ApplicationError("Invalid login credentials")
        if not util.password_is_match(password, existing_user.hashed_password):
            raise ApplicationError("Invalid login credentials")
        return util.create_access_token(data={"sub": str(existing_user.id)})

    def authenticate_token(self, session: Session, token: bytes) -> User:
        user_id: str = util.decode_access_token(token)
        return self.user_service.get(session, UUID(user_id))

    def authenticate_google(
        self,
        session: Session,
        access_token: str,
        id_token: str,
        email: str,
        first_name: str,
        last_name: str,
        role: UserRole,
        authenticated_user: User = None,
    ):
        user: User = None

        # TODO refactor social account methods into service?
        existing_google_social_account: Optional[SocialAccount] = (
            session.query(SocialAccount)
            .filter(SocialAccount.account_type == SocialAccountType.GOOGLE)
            .filter(SocialAccount.account_email == email)
            .one_or_none()
        )

        if not authenticated_user and existing_google_social_account:
            # social account exists therefore user exists
            # sign in with google
            user: User = existing_google_social_account.user
            existing_google_social_account.access_token = access_token
            existing_google_social_account.id_token = id_token

        elif not authenticated_user:
            # sign up with google
            user_with_email = self.user_service.get_by_email(session, email)
            if user_with_email:
                raise ApplicationError("User exists with this email address")
            user = self.user_service.create(
                session,
                first_name=first_name,
                last_name=last_name,
                email=email,
                email_verified=True,
                role=role,
                commit=False,
            )
            session.flush()
            existing_google_social_account = SocialAccount(
                user_id=user.id,
                access_token=access_token,
                id_token=id_token,
                account_email=email,
                account_type=SocialAccountType.GOOGLE,
            )
            session.add(existing_google_social_account)

        elif not existing_google_social_account:
            # link google account
            # does user already havea an existing google account
            authenticated_users_existing_google_account = (
                session.query(SocialAccount)
                .filter(SocialAccount.user_id == authenticated_user.id)
                .filter(SocialAccount.account_type == SocialAccountType.GOOGLE)
                .one_or_none()
            )
            if authenticated_users_existing_google_account:
                # update the account if yes
                authenticated_users_existing_google_account.access_token = access_token
                authenticated_users_existing_google_account.account_email = email
                authenticated_users_existing_google_account.id_token = id_token
            else:
                # create a new one if not.
                existing_google_social_account = SocialAccount(
                    user_id=authenticated_user.id,
                    access_token=access_token,
                    id_token=id_token,
                    account_email=email,
                    account_type=SocialAccountType.GOOGLE,
                )
                session.add(existing_google_social_account)
            user = authenticated_user

        else:
            # update google account
            user: User = existing_google_social_account.user
            if authenticated_user != user:
                raise ApplicationError("Google Account is linked to another user")
            existing_google_social_account.access_token = access_token
            existing_google_social_account.id_token = id_token

        session.commit()
        return util.create_access_token(data={"sub": str(user.id)})

    def authenticate_facebook(
        self,
        session: Session,
        facebook_user_id: str,
        access_token: str,
        email: str,
        first_name: str,
        last_name: str,
        role: UserRole,
        authenticated_user: User = None,
    ):
        user: User = None

        # TODO refactor social account methods into service?
        existing_facebook_social_account: Optional[SocialAccount] = (
            session.query(SocialAccount)
            .filter(SocialAccount.account_type == SocialAccountType.FACEBOOK)
            .filter(SocialAccount.account_id == facebook_user_id)
            .one_or_none()
        )

        if not authenticated_user and existing_facebook_social_account:
            # social account exists therefore user exists
            # sing in with facebook
            user: User = existing_facebook_social_account.user
            existing_facebook_social_account.access_token = access_token
            existing_facebook_social_account.account_email = email

        elif not authenticated_user:
            # sign up with facebook
            user_with_email = self.user_service.get_by_email(session, email)
            if user_with_email:
                raise ApplicationError("User exists with this email address")
            user = self.user_service.create(
                session,
                first_name=first_name,
                last_name=last_name,
                email=email,
                email_verified=True,
                role=role,
                commit=False,
            )
            session.flush()
            existing_facebook_social_account = SocialAccount(
                user_id=user.id,
                access_token=access_token,
                account_id=facebook_user_id,
                account_email=email,
                account_type=SocialAccountType.FACEBOOK,
            )
            session.add(existing_facebook_social_account)

        elif not existing_facebook_social_account:
            # link facebook account
            # does user already havea an existing facebook account
            authenticated_users_existing_facebook_account = (
                session.query(SocialAccount)
                .filter(SocialAccount.user_id == authenticated_user.id)
                .filter(SocialAccount.account_type == SocialAccountType.FACEBOOK)
                .one_or_none()
            )
            if authenticated_users_existing_facebook_account:
                # update the account if yes
                authenticated_users_existing_facebook_account.access_token = (
                    access_token
                )
                authenticated_users_existing_facebook_account.account_email = email
                authenticated_users_existing_facebook_account.account_id = (
                    facebook_user_id
                )
            else:
                # create a new one if not.
                existing_facebook_social_account = SocialAccount(
                    user_id=authenticated_user.id,
                    access_token=access_token,
                    account_id=facebook_user_id,
                    account_email=email,
                    account_type=SocialAccountType.FACEBOOK,
                )
                session.add(existing_facebook_social_account)
            user = authenticated_user

        else:
            # update facebook account
            user: User = existing_facebook_social_account.user
            if authenticated_user != user:
                raise ApplicationError("Facebook Account is linked to another user")
            existing_facebook_social_account.access_token = access_token
            existing_facebook_social_account.account_email = email

        session.commit()
        return util.create_access_token(data={"sub": str(user.id)})

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
        longitude: float,
        latitude: float,
        furnish_type: str,
        available_from: date,
        available_to: date,
        amenities: List[Amenity],
    ) -> Apartment:
        location = "POINT({} {})".format(longitude, latitude)
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
            location=location,
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
        if all(x in kwargs for x in ["longitude", "latitude"]):
            # TODO allow updating either longitude or latitude
            location = "POINT({} {})".format(kwargs["longitude"], kwargs["latitude"])
            kwargs["location"] = location
        try:
            del kwargs["longitude"]
            del kwargs["latitude"]
        except KeyError:
            pass
        return self.apartment_service.update(session, apartment, **kwargs)

    def __upload_file(
        self,
        user: User,
        file: IO,
        extension: str,
        folder_path: Path,
        supported_file_extensions: List[str] = config.SUPPORTED_FILE_EXTENSIONS,
    ) -> User:
        if extension.lower() not in supported_file_extensions:
            raise ApplicationError("Invalid file format")
        possible_filenames = [
            f"{user.id}.{ext}" for ext in config.SUPPORTED_FILE_EXTENSIONS
        ]
        for filename in possible_filenames:
            if self.file_service.get(filename, folder_path):
                self.file_service.delete(filename, folder_path)
        filename = f"{user.id}.{extension.lower()}"
        self.file_service.store_file(folder_path, filename, file)
        return user

    def upload_profile_image(self, user: User, file: IO, filename: str):
        file_extension = filename.split(".")[-1]
        if file_extension.lower() not in config.SUPPORTED_IMAGE_EXTENSIONS:
            raise ApplicationError("Unsupported image format")
        folder_path = util.get_profile_path()
        possible_filenames = [
            f"{user.id}.{ext}" for ext in config.SUPPORTED_IMAGE_EXTENSIONS
        ]
        for filename in possible_filenames:
            if self.file_service.get(filename, folder_path):
                self.file_service.delete(filename, folder_path)
        filename = f"{user.id}.{file_extension.lower()}"
        self.file_service.store_file(folder_path, filename, file)
        return user

    def upload_copy_id(self, user: User, file: IO, extension: str) -> User:
        supported_file_extensions = [
            *config.SUPPORTED_FILE_EXTENSIONS,
            *config.SUPPORTED_IMAGE_EXTENSIONS,
        ]
        return self.__upload_file(
            user, file, extension, util.get_copy_ids_path(), supported_file_extensions
        )

    def upload_proof_of_income(self, user: User, file: IO, extension: str) -> Tenant:
        supported_file_extensions = [
            *config.SUPPORTED_FILE_EXTENSIONS,
            *config.SUPPORTED_IMAGE_EXTENSIONS,
        ]
        return self.__upload_file(
            user,
            file,
            extension,
            util.get_proof_of_income_path(),
            supported_file_extensions,
        )

    def upload_proof_of_enrollment(
        self, user: User, file: IO, extension: str
    ) -> Tenant:
        supported_file_extensions = [
            *config.SUPPORTED_FILE_EXTENSIONS,
            *config.SUPPORTED_IMAGE_EXTENSIONS,
        ]
        return self.__upload_file(
            user,
            file,
            extension,
            util.get_proof_of_enrollment_path(),
            supported_file_extensions,
        )

    def upload_apartment_image(
        self, landlord: Landlord, apartment: Apartment, file: IO, filename: str
    ) -> Apartment:
        assert isinstance(landlord, Landlord)
        file_extension = filename.split(".")[-1]
        if file_extension.lower() not in config.SUPPORTED_IMAGE_EXTENSIONS:
            raise ApplicationError("Unsupported image format")
        folder_path = util.get_apartment_images_folder_path(apartment)
        files = self.file_service.list_files(folder_path)
        if len(files) == config.NUMBER_OF_APARTMENT_IMAGES:
            raise ApplicationError("Maximum number of apartment images reached")
        number_of_images_in_folder = len(files)
        new_filename = f"image{number_of_images_in_folder+1}.{file_extension}"
        self.file_service.store_file(folder_path, new_filename, file)
        return apartment

    def upload_apartment_video(
        self, landlord: Landlord, apartment: Apartment, file: IO, filename: str
    ) -> Apartment:
        assert isinstance(landlord, Landlord)
        file_extension = filename.split(".")[-1]
        if file_extension.lower() not in config.SUPPORTED_VIDEO_EXTENSIONS:
            raise ApplicationError("Unsupported video format")
        folder_path = util.get_apartment_videos_folder_path(apartment)
        files = self.file_service.list_files(folder_path)
        if len(files) == config.NUMBER_OF_APARTMENT_VIDEOS:
            raise ApplicationError("Maximum number of apartment vidoes reached")
        number_of_videos_in_folder = len(files)
        new_filename = f"video{number_of_videos_in_folder+1}.{file_extension}"
        self.file_service.store_file(folder_path, new_filename, file)
        return apartment

    def delete_apartment_image(
        self, apartment: Apartment, image_name: str
    ) -> Apartment:
        folder_path = util.get_apartment_images_folder_path(apartment)
        self.file_service.delete(image_name, folder_path)
        return apartment

    def delete_apartment_video(
        self, apartment: Apartment, video_name: str
    ) -> Apartment:
        folder_path = util.get_apartment_videos_folder_path(apartment)
        self.file_service.delete(video_name, folder_path)
        return apartment

    def apply_for_apartment(
        self, session: Session, tenant: Tenant, apartment: Apartment
    ) -> ApartmentApplication:

        awarded_or_completed_application = (
            session.query(ApartmentApplication)
            .join(Contract)
            .filter(ApartmentApplication.apartment_id == apartment.id)
            .filter(
                or_(
                    ApartmentApplication.status == ApartmentApplicationStatus.AWARDED,
                    ApartmentApplication.status == ApartmentApplicationStatus.COMPLETED,
                )
            )
            .one_or_none()
        )
        if awarded_or_completed_application:
            raise ApplicationError("Apartment has already been awarded or completed")
        existing_application = (
            session.query(ApartmentApplication)
            .filter(ApartmentApplication.apartment_id == apartment.id)
            .filter(ApartmentApplication.tenant_id == tenant.id)
            .one_or_none()
        )

        if (
            existing_application
            and existing_application.status != ApartmentApplicationStatus.FAILED
        ):
            raise ApplicationError("User already applied for this apartment")
        return self.apartment_application_service.create(
            session, tenant=tenant, apartment=apartment
        )

    def reject_apartment_application(
        self,
        session: Session,
        apartment_application: ApartmentApplication,
    ) -> ApartmentApplication:
        if apartment_application.status != ApartmentApplicationStatus.NEW:
            raise ApplicationError(
                "Apartment application can not be reject at this stage"
            )
        return self.apartment_application_service.update(
            session, apartment_application, is_rejected=True
        )

    def consider_apartment_application(
        self,
        session: Session,
        apartment_application: ApartmentApplication,
    ) -> ApartmentApplication:
        if apartment_application.status != ApartmentApplicationStatus.NEW:
            raise ApplicationError(
                "Apartment application can not be considered at this stage"
            )
        return self.apartment_application_service.update(
            session, apartment_application, is_considered=True
        )

    def process_apartment_application(
        self,
        session: Session,
        apartment_application: ApartmentApplication,
        has_document: bool = True,
    ) -> ApartmentApplication:
        if apartment_application.status != ApartmentApplicationStatus.CONSIDERED:
            raise ApplicationError("Apartment has not been considered")
        currently_processed_application = (
            session.query(ApartmentApplication)
            .join(Contract)
            .filter(
                ApartmentApplication.apartment_id == apartment_application.apartment_id
            )
            .filter(
                or_(
                    ApartmentApplication.status
                    == ApartmentApplicationStatus.PROCESSING,
                    ApartmentApplication.status == ApartmentApplicationStatus.AWARDED,
                )
            )
            .one_or_none()
        )
        if currently_processed_application:
            raise ApplicationError("Another application is currently being processed")
        contract = Contract(
            apartment_application_id=apartment_application.id, has_document=has_document
        )
        session.add(contract)
        session.commit()
        if config.APP_ENV != "test" and has_document:
            send_contract_sign_request(
                apartment_application.id,
                apartment_application.apartment.landlord.email,
                apartment_application.tenant.email,
            )
        return apartment_application

    def __confirm_and_create_invoice(self, session: Session, apartment_application):
        has_invoice = bool(
            session.query(Invoice)
            .filter(Invoice.type == InvoiceType.RENT)
            .filter(Invoice.apartment_application_id == apartment_application.id)
            .count()
        )
        if (
            not has_invoice
            and apartment_application.status == ApartmentApplicationStatus.AWARDED
        ):
            redirect_url: str = config.MOLLIE_REDIRECT_URL
            webhook_url: str = config.MOLLIE_WEBHOOK_URL
            start_date = util.get_current_date()
            start_date_text = util.get_human_readable_date(start_date)
            next_date = util.get_date_x_days_from(
                start_date, config.RENT_PAYMENT_DURATION_DAYS
            )
            next_date_text = util.get_human_readable_date(next_date)
            description = (
                f"Invoice for payment from {start_date_text} to {next_date_text}"
            )
            amount = round(apartment_application.apartment.total_price, 2)
            invoice = Invoice(
                apartment_application_id=apartment_application.id,
                type=InvoiceType.RENT,
                status=InvoiceStatus.PENDING,
                amount=amount,
                description=description,
                next_date=next_date,
            )
            session.add(invoice)
            session.flush()
            mollie_amount = util.float_to_mollie_amount(invoice.amount)
            print("\n\n\n\n")
            print(f"Amount to charge is {mollie_amount}")
            print("\n\n\n\n")
            payment = mollie_client.payments.create(
                {
                    "amount": {"currency": "EUR", "value": mollie_amount},
                    "description": invoice.description,
                    "redirectUrl": redirect_url,
                    "webhookUrl": webhook_url,
                    "metadata": {
                        "type": invoice.type,
                        "invoice_id": str(invoice.id),
                        "created_date": str(start_date),
                        "next_date": str(next_date),
                    },
                }
            )
            invoice.payment_id = payment.id

    def tenant_signed_contract(
        self,
        session: Session,
        apartment_application: ApartmentApplication,
        signed_on: datetime,
    ) -> ApartmentApplication:
        if apartment_application.status != ApartmentApplicationStatus.PROCESSING:
            raise ApplicationError("Cannot sign contract at this stage")
        apartment_application.contract.tenant_has_signed = True
        apartment_application.contract.tenant_signed_on = signed_on
        self.__confirm_and_create_invoice(session, apartment_application)
        session.commit()
        return apartment_application

    def landlord_signed_contract(
        self,
        session: Session,
        apartment_application: ApartmentApplication,
        signed_on: datetime,
    ) -> Contract:
        if apartment_application.status != ApartmentApplicationStatus.PROCESSING:
            raise ApplicationError("Cannot sign contract at this stage")
        apartment_application.contract.landlord_has_signed = True
        apartment_application.contract.landlord_signed_on = signed_on
        self.__confirm_and_create_invoice(session, apartment_application)
        session.commit()
        return apartment_application

    def decline_contract(
        self,
        session: Session,
        apartment_application: ApartmentApplication,
        declined_on: datetime,
        by: User,
    ):
        assert by.role in [UserRole.TENANT, UserRole.LANDLORD]
        if apartment_application.contract.status != ContractStatus.NEW:
            raise ApplicationError("Contract can not be declined at this stage")
        contract: Contract = apartment_application.contract
        if by.role == UserRole.TENANT:
            contract.tenant_declined_on = declined_on
            contract.tenant_declined = True
        else:
            contract.landlord_declined = True
            contract.landlord_declined_on = declined_on
        session.commit()
        return apartment_application

    def expire_contract(
        self,
        session: Session,
        apartment_application: ApartmentApplication,
        expired_on: datetime,
    ):
        if apartment_application.contract.status != ContractStatus.NEW:
            raise ApplicationError("Contract can not be declined at this stage")
        contract: Contract = apartment_application.contract
        contract.expired_on = expired_on
        contract.expired = True
        session.commit()
        return apartment_application

    def cancel_contract(
        self,
        session: Session,
        apartment_application: ApartmentApplication,
        canceled_on: datetime,
    ):
        if apartment_application.contract.status != ContractStatus.NEW:
            raise ApplicationError("Contract can not be declined at this stage")
        contract: Contract = apartment_application.contract
        contract.canceled = True
        contract.canceled_on = canceled_on
        session.commit()
        return apartment_application

    def provide_keys_to_tenant(
        self, session: Session, apartment_application: ApartmentApplication
    ):
        if apartment_application.contract.status != ContractStatus.SIGNED:
            raise ApplicationError("Contract is not signed")
        rent_invoice: Invoice = (
            session.query(Invoice)
            .filter(Invoice.type == InvoiceType.RENT)
            .filter(Invoice.apartment_application_id == apartment_application.id)
            .order_by(Invoice.created_at.desc())
            .first()
        )
        if not rent_invoice or rent_invoice.status != InvoiceStatus.PAID:
            raise ApplicationError("Payment has not been made")
        contract: Contract = apartment_application.contract
        contract.landlord_has_provided_keys = True
        session.commit()
        return apartment_application

    def tenant_receive_keys(
        self, session: Session, apartment_application: ApartmentApplication
    ):
        if apartment_application.contract.status != ContractStatus.SIGNED:
            raise ApplicationError("Contract is not signed")
        if not apartment_application.contract.landlord_has_provided_keys:
            raise ApplicationError("Landlord has not provided keys")
        other_applications = (
            session.query(ApartmentApplication)
            .filter(
                ApartmentApplication.apartment_id == apartment_application.apartment_id
            )
            .filter(ApartmentApplication.id != apartment_application.id)
            .all()
        )
        for apartment_app in other_applications:
            apartment_app.is_rejected = True
        contract: Contract = apartment_application.contract
        contract.tenant_has_received_keys = True
        session.commit()
        return apartment_application

    def invite_tenant_to_apply(
        self,
        session: Session,
        landlord: Landlord,
        tenant: Tenant,
        apartment: Apartment,
    ) -> BookingRequest:
        if apartment.landlord_id != landlord.id:
            raise ApplicationError("Landlord does not own apartment")
        awarded_application = (
            session.query(ApartmentApplication)
            .filter(ApartmentApplication.apartment_id == apartment.id)
            .filter(ApartmentApplication.status == ApartmentApplicationStatus.AWARDED)
            .first()
        )
        if awarded_application:
            raise ApplicationError("Apartment has already been awarded")
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
