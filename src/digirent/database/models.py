from typing import List
from sqlalchemy import (
    Table,
    Column,
    String,
    Text,
    Float,
    DateTime,
    Integer,
    ForeignKey,
    Boolean,
    Date,
    UniqueConstraint,
    case,
    and_,
    or_,
)
from geoalchemy2 import Geometry
from sqlalchemy.orm import backref, relationship
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy_utils import ChoiceType, EmailType, UUIDType

from digirent import util
from digirent.core.config import SUPPORTED_FILE_EXTENSIONS, SUPPORTED_IMAGE_EXTENSIONS
from .base import Base
from .mixins import EntityMixin, TimestampMixin
from .enums import (
    ApartmentApplicationStatus,
    BookingRequestStatus,
    ContractStatus,
    FurnishType,
    InvoiceStatus,
    InvoiceType,
    SocialAccountType,
    UserRole,
    Gender,
    HouseType,
)
from .association_tables import apartments_amenities_association_table


class User(Base, EntityMixin, TimestampMixin):
    __tablename__ = "users"
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    dob = Column(Date, nullable=True)
    phone_number = Column(String, nullable=True, unique=True)
    email = Column(EmailType, nullable=False, unique=True)
    hashed_password = Column(Text, nullable=True)
    email_verified = Column(Boolean, nullable=False, default=False)
    phone_verified = Column(Boolean, nullable=False, default=False)
    is_suspended = Column(Boolean, nullable=False, default=False)
    suspended_reason = Column(String, nullable=True)
    role = Column(ChoiceType(UserRole, impl=String()), nullable=False)
    gender = Column(ChoiceType(Gender, impl=String()), nullable=True)
    city = Column(String, nullable=True)
    description = Column(String, nullable=True)
    bank_detail = relationship("BankDetail", uselist=False, backref="user")

    __mapper_args__ = {"polymorphic_identity": None, "polymorphic_on": role}

    @property
    def is_active(self):
        if self.is_suspended:
            return False
        return all([self.email_verified])

    @property
    def copy_id_uploaded(self) -> bool:
        possible_filenames = [
            f"{self.id}.{ext}"
            for ext in [*SUPPORTED_FILE_EXTENSIONS, *SUPPORTED_IMAGE_EXTENSIONS]
        ]
        copy_id_path = util.get_copy_ids_path()
        possible_copy_id_file_paths = [
            (copy_id_path / filename) for filename in possible_filenames
        ]
        return any(path.exists() for path in possible_copy_id_file_paths)

    @property
    def proof_of_income_uploaded(self) -> bool:
        possible_filenames = [
            f"{self.id}.{ext}"
            for ext in [*SUPPORTED_FILE_EXTENSIONS, *SUPPORTED_IMAGE_EXTENSIONS]
        ]
        proof_of_income_path = util.get_proof_of_income_path()
        possible_proof_of_income_file_paths = [
            (proof_of_income_path / filename) for filename in possible_filenames
        ]
        return any(path.exists() for path in possible_proof_of_income_file_paths)

    @property
    def proof_of_enrollment_uploaded(self) -> bool:
        possible_filenames = [
            f"{self.id}.{ext}"
            for ext in [*SUPPORTED_FILE_EXTENSIONS, *SUPPORTED_IMAGE_EXTENSIONS]
        ]
        proof_of_enrollment_path = util.get_proof_of_enrollment_path()
        possible_proof_of_enrollment_file_paths = [
            (proof_of_enrollment_path / filename) for filename in possible_filenames
        ]
        return any(path.exists() for path in possible_proof_of_enrollment_file_paths)

    @property
    def profile_image_url(self) -> str:
        url = "/static/profile_images/"
        possible_filenames = [f"{self.id}.{ext}" for ext in SUPPORTED_IMAGE_EXTENSIONS]
        profile_image_path = util.get_profile_path()
        possible_profile_image_file_paths = [
            (profile_image_path / filename) for filename in possible_filenames
        ]
        for image_path in possible_profile_image_file_paths:
            if image_path.exists():
                url += image_path.name
                return url


class Admin(User):
    __mapper_args__ = {"polymorphic_identity": UserRole.ADMIN}


class Tenant(User):
    looking_for = relationship("LookingFor", uselist=False, backref="tenant")
    __mapper_args__ = {"polymorphic_identity": UserRole.TENANT}

    @hybrid_property
    def profile_percentage(self) -> float:
        result = 0
        if self.copy_id_uploaded:
            result += 20
        if self.proof_of_income_uploaded:
            result += 10
        if self.proof_of_enrollment_uploaded:
            result += 10
        if self.social_accounts:
            result += 10
        assert result <= 100
        return result


class Landlord(User):
    __mapper_args__ = {"polymorphic_identity": UserRole.LANDLORD}

    @hybrid_property
    def profile_percentage(self) -> float:
        result = 0
        if self.copy_id_uploaded:
            result += 30
        if self.social_accounts:
            result += 20
        assert result <= 100
        return result


class LookingFor(Base, EntityMixin, TimestampMixin):
    __tablename__ = "looking_for"
    tenant_id = Column(UUIDType(binary=False), ForeignKey("users.id"))
    house_type = Column(ChoiceType(HouseType, impl=String()), nullable=False)
    city = Column(String, nullable=False)
    max_budget = Column(Float, nullable=False)

    def __init__(self, tenant_id, house_type, city, max_budget):
        self.tenant_id = tenant_id
        self.house_type = house_type
        self.city = city
        self.max_budget = max_budget


class BankDetail(Base, EntityMixin, TimestampMixin):
    __tablename__ = "bank_details"
    user_id = Column(UUIDType(binary=False), ForeignKey("users.id"))
    account_name = Column(String, nullable=False)
    account_number = Column(String, nullable=False)

    def __init__(self, user_id, account_name, account_number) -> None:
        self.user_id = user_id
        self.account_name = account_name
        self.account_number = account_number


class Apartment(Base, EntityMixin, TimestampMixin):
    __tablename__ = "apartments"
    name = Column(String, nullable=False)
    monthly_price = Column(Float, nullable=False)
    utilities_price = Column(Float, nullable=False)
    address = Column(String, nullable=False)
    country = Column(String, nullable=False)
    state = Column(String, nullable=False)
    city = Column(String, nullable=False)
    description = Column(String, nullable=False)
    house_type = Column(ChoiceType(HouseType, impl=String()), nullable=False)
    furnish_type = Column(ChoiceType(FurnishType, impl=String()), nullable=False)
    bedrooms = Column(Integer, nullable=False)
    bathrooms = Column(Integer, nullable=False)
    size = Column(Float, nullable=False)
    available_from = Column(Date, nullable=False)
    available_to = Column(Date, nullable=False)
    location = Column(Geometry("POINT", management=True))

    amenities = relationship(
        "Amenity",
        secondary=apartments_amenities_association_table,
        backref="apartments",
    )
    landlord_id = Column(UUIDType(binary=False), ForeignKey("users.id"), nullable=False)
    tenant_id = Column(UUIDType(binary=False), ForeignKey("users.id"), nullable=True)

    landlord = relationship(
        "Landlord", foreign_keys=[landlord_id], backref="apartments"
    )
    tenant = relationship(
        "Tenant", foreign_keys=[tenant_id], backref=backref("apartment", uselist=False)
    )

    @hybrid_property
    def amenity_titles(self) -> List[str]:
        return [amenity.title for amenity in self.amenities]

    @hybrid_property
    def total_price(self) -> float:
        return self.monthly_price + self.utilities_price


class Amenity(Base, EntityMixin, TimestampMixin):
    __tablename__ = "amenities"
    title = Column(String, nullable=False, unique=True)


class ApartmentApplication(Base, EntityMixin, TimestampMixin):
    __tablename__ = "apartment_applications"
    apartment_id = Column(
        UUIDType(binary=False), ForeignKey("apartments.id"), nullable=False
    )
    tenant_id = Column(UUIDType(binary=False), ForeignKey("users.id"), nullable=False)
    is_rejected = Column(Boolean, nullable=False, default=False)
    is_considered = Column(Boolean, nullable=False, default=False)
    apartment = relationship("Apartment", backref="applications")
    tenant = relationship("Tenant", backref="applications")
    booking_request = relationship(
        "BookingRequest", uselist=False, backref="apartment_application"
    )

    contract = relationship("Contract", uselist=False, backref="apartment_application")

    @hybrid_property
    def status(self) -> ApartmentApplicationStatus:
        if not any([self.is_considered, self.is_rejected]):
            return ApartmentApplicationStatus.NEW
        if self.is_rejected:
            return ApartmentApplicationStatus.REJECTED
        if not self.contract:
            return ApartmentApplicationStatus.CONSIDERED
        if self.contract.status in [
            ContractStatus.DECLINED,
            ContractStatus.CANCELED,
            ContractStatus.EXPIRED,
        ]:
            return ApartmentApplicationStatus.FAILED
        if self.contract.status == ContractStatus.NEW:
            return ApartmentApplicationStatus.PROCESSING
        if self.contract.status == ContractStatus.SIGNED:
            return ApartmentApplicationStatus.AWARDED
            # TODO is it awarded when contract is signed
        if self.contract.status == ContractStatus.COMPLETED:
            return ApartmentApplicationStatus.COMPLETED

    @status.expression
    def status(self):
        return case(
            [
                (
                    and_(
                        self.is_considered == False, self.is_rejected == False  # noqa
                    ),
                    ApartmentApplicationStatus.NEW.value,
                ),
                (
                    self.is_rejected == True,
                    ApartmentApplicationStatus.REJECTED.value,
                ),
                (
                    self.contract == None,
                    ApartmentApplicationStatus.CONSIDERED.value,
                ),
                (
                    or_(
                        Contract.status == ContractStatus.DECLINED,
                        Contract.status == ContractStatus.CANCELED,
                        Contract.status == ContractStatus.EXPIRED,
                    ),
                    ApartmentApplicationStatus.FAILED.value,
                ),
                (
                    Contract.status == ContractStatus.NEW,
                    ApartmentApplicationStatus.PROCESSING.value,
                ),
                (
                    Contract.status == ContractStatus.SIGNED,
                    ApartmentApplicationStatus.AWARDED.value,
                ),
                (
                    Contract.status == ContractStatus.COMPLETED,
                    ApartmentApplicationStatus.COMPLETED.value,
                ),
            ]
        )


class Contract(Base, EntityMixin, TimestampMixin):
    __tablename__ = "contracts"
    apartment_application_id = Column(
        UUIDType(binary=False), ForeignKey("apartment_applications.id")
    )
    landlord_has_signed = Column(Boolean, nullable=False, default=False)
    landlord_signed_on = Column(DateTime, nullable=True)
    tenant_has_signed = Column(Boolean, nullable=False, default=False)
    tenant_signed_on = Column(DateTime, nullable=True)
    landlord_has_provided_keys = Column(Boolean, nullable=False, default=False)
    landlord_provided_keys_on = Column(DateTime, nullable=True)
    tenant_has_received_keys = Column(Boolean, nullable=False, default=False)
    tenant_received_keys_on = Column(DateTime, nullable=True)
    landlord_declined = Column(Boolean, nullable=False, default=False)
    landlord_declined_on = Column(DateTime, nullable=True)
    tenant_declined = Column(Boolean, nullable=False, default=False)
    tenant_declined_on = Column(DateTime, nullable=True)
    canceled = Column(Boolean, nullable=False, default=False)
    canceled_on = Column(DateTime, nullable=True)
    expired = Column(Boolean, nullable=False, default=False)
    expired_on = Column(DateTime, nullable=True)

    @hybrid_property
    def status(self) -> ContractStatus:
        if any([self.tenant_declined, self.landlord_declined]):
            return ContractStatus.DECLINED
        elif self.expired:
            return ContractStatus.EXPIRED
        elif self.canceled:
            return ContractStatus.CANCELED
        elif not all([self.landlord_has_signed, self.tenant_has_signed]):
            return ContractStatus.NEW
        elif not all([self.landlord_has_provided_keys, self.tenant_has_received_keys]):
            return ContractStatus.SIGNED
        else:
            return ContractStatus.COMPLETED

    @status.expression
    def status(self):
        return case(
            [
                (
                    or_(
                        self.tenant_declined == True,  # noqa
                        self.landlord_declined == True,
                    ),
                    ContractStatus.DECLINED.value,
                ),
                (self.expired == True, ContractStatus.EXPIRED.value),
                (self.canceled == True, ContractStatus.CANCELED.value),
                (
                    or_(
                        self.landlord_has_signed == False,  # noqa
                        self.tenant_has_signed == False,
                    ),
                    ContractStatus.NEW.value,
                ),
                (
                    or_(
                        self.landlord_has_provided_keys == False,
                        self.tenant_has_received_keys == False,
                    ),
                    ContractStatus.SIGNED.value,
                ),
            ],
            else_=ContractStatus.COMPLETED.value,
        )


class BookingRequest(Base, EntityMixin, TimestampMixin):
    __tablename__ = "booking_requests"
    tenant_id = Column(UUIDType(binary=False), ForeignKey("users.id"), nullable=False)
    apartment_id = Column(
        UUIDType(binary=False), ForeignKey("apartments.id"), nullable=False
    )
    apartment_application_id = Column(
        UUIDType(binary=False), ForeignKey("apartment_applications.id"), nullable=True
    )
    status = Column(
        ChoiceType(BookingRequestStatus, impl=String()),
        nullable=False,
        default=BookingRequestStatus.PENDING,
    )
    tenant = relationship("Tenant", backref="booking_requests")
    apartment = relationship("Apartment", backref="booking_requests")

    def accept(self, apartment_application: ApartmentApplication):
        self.status = BookingRequestStatus.ACCEPTED
        self.apartment_application = apartment_application

    def reject(self):
        self.status = BookingRequestStatus.REJECTED
        self.apartment_application_id = None


class SocialAccount(Base, EntityMixin, TimestampMixin):
    __tablename__ = "social_accounts"
    id_token = Column(String, nullable=True, unique=True)
    account_id = Column(String, nullable=True)
    account_email = Column(EmailType, nullable=True)
    access_token = Column(String, nullable=True, unique=True)
    account_type = Column(ChoiceType(SocialAccountType, impl=String()), nullable=False)

    user_id = Column(UUIDType(binary=False), ForeignKey("users.id"), nullable=False)

    user = relationship("User", foreign_keys=[user_id], backref="social_accounts")

    UniqueConstraint(account_id, account_type, name="uix_id_type")
    UniqueConstraint(account_email, account_type, name="uix_email_type")


class Invoice(Base, EntityMixin, TimestampMixin):
    __tablename__ = "invoices"
    status = Column(
        ChoiceType(InvoiceStatus, impl=String()),
        nullable=False,
        default=InvoiceStatus.PENDING,
    )
    type = Column(ChoiceType(InvoiceType, impl=String()), nullable=False)
    user_id = Column(UUIDType(binary=False), ForeignKey("users.id"), nullable=True)
    apartment_application_id = Column(
        UUIDType(binary=False),
        ForeignKey("apartment_applications.id"),
        nullable=True,
    )
    amount = Column(Float, nullable=False)
    description = Column(String, nullable=True)
    payment_id = Column(String, nullable=True)
    payment_action_date = Column(Date, nullable=True)
    next_date = Column(Date, nullable=False)

    apartment_application = relationship(ApartmentApplication, backref="invoices")
    user = relationship(User, backref="invoices")


class ChatMessage(Base, EntityMixin, TimestampMixin):
    __tablename__ = "chat_messages"
    from_user_id = Column(
        UUIDType(binary=False),
        ForeignKey("users.id"),
        nullable=False,
    )
    to_user_id = Column(
        UUIDType(binary=False),
        ForeignKey("users.id"),
        nullable=False,
    )
    message = Column(String, nullable=False)


blog_post_tag_association_table = Table(
    "blog_posts_tags_association",
    Base.metadata,
    Column("blog_post_id", UUIDType(binary=False), ForeignKey("blog_posts.id")),
    Column("blog_tag_name", String, ForeignKey("blog_tags.name")),
)


class BlogPost(Base, EntityMixin, TimestampMixin):
    __tablename__ = "blog_posts"

    title = Column(String, nullable=False, unique=True)
    content = Column(String, nullable=False)
    tags = relationship(
        "BlogTag",
        secondary=blog_post_tag_association_table,
        backref="posts",
    )


class BlogTag(Base, TimestampMixin):
    __tablename__ = "blog_tags"

    name = Column(String, primary_key=True)
