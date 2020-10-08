from sqlalchemy import (
    Column,
    String,
    Text,
    Float,
    Integer,
    ForeignKey,
    Boolean,
    Date,
)
from sqlalchemy.orm import backref, relationship
from sqlalchemy.util.langhelpers import hybridproperty
from sqlalchemy_utils import ChoiceType, EmailType, UUIDType

from digirent import util
from digirent.core.config import SUPPORTED_FILE_EXTENSIONS
from .base import Base
from .mixins import EntityMixin, TimestampMixin
from .enums import ApartmentApplicationStage, UserRole, Gender, HouseType
from .association_tables import apartments_amenities_association_table


class User(Base, EntityMixin, TimestampMixin):
    __tablename__ = "users"
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    dob = Column(Date, nullable=True)
    phone_number = Column(String, nullable=False, unique=True)
    email = Column(EmailType, nullable=False, unique=True)
    hashed_password = Column(Text, nullable=False)
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
        return all([self.email_verified, self.phone_verified])


class Admin(User):
    __mapper_args__ = {"polymorphic_identity": UserRole.ADMIN}


class Tenant(User):
    looking_for = relationship("LookingFor", uselist=False, backref="tenant")
    __mapper_args__ = {"polymorphic_identity": UserRole.TENANT}

    @hybridproperty
    def profile_percentage(self) -> float:
        result = 0
        possible_filenames = [f"{self.id}.{ext}" for ext in SUPPORTED_FILE_EXTENSIONS]
        copy_id_path = util.get_copy_ids_path()
        possible_copy_id_file_paths = [
            (copy_id_path / filename) for filename in possible_filenames
        ]
        proof_of_income_path = util.get_proof_of_income_path()
        possible_proof_of_income_file_paths = [
            (proof_of_income_path / filename) for filename in possible_filenames
        ]
        proof_of_enrollment_path = util.get_proof_of_enrollment_path()
        possible_proof_of_enrollment_file_paths = [
            (proof_of_enrollment_path / filename) for filename in possible_filenames
        ]
        if any(path.exists() for path in possible_copy_id_file_paths):
            result += 20
        if any(path.exists() for path in possible_proof_of_income_file_paths):
            result += 10
        if any(path.exists() for path in possible_proof_of_enrollment_file_paths):
            result += 10
        assert result <= 100
        return result


class Landlord(User):
    __mapper_args__ = {"polymorphic_identity": UserRole.LANDLORD}

    @hybridproperty
    def profile_percentage(self) -> float:
        result = 0
        possible_filenames = [f"{self.id}.{ext}" for ext in SUPPORTED_FILE_EXTENSIONS]
        copy_id_path = util.get_copy_ids_path()
        possible_copy_id_file_paths = [
            (copy_id_path / filename) for filename in possible_filenames
        ]
        if any(path.exists() for path in possible_copy_id_file_paths):
            result += 30
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
    bedrooms = Column(Integer, nullable=False)
    bathrooms = Column(Integer, nullable=False)
    size = Column(Float, nullable=False)
    furnish_type = Column(String, nullable=False)
    available_from = Column(Date, nullable=False)
    available_to = Column(Date, nullable=False)
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

    @hybridproperty
    def amenity_titles(self):
        return [amenity.title for amenity in self.amenities]


class Amenity(Base, EntityMixin, TimestampMixin):
    __tablename__ = "amenities"
    title = Column(String, nullable=False, unique=True)


class ApartmentApplication(Base, EntityMixin, TimestampMixin):
    __tablename__ = "apartment_applications"
    apartment_id = Column(UUIDType(binary=False), ForeignKey("apartments.id"))
    tenant_id = Column(UUIDType(binary=False), ForeignKey("users.id"))
    stage = Column(ChoiceType(ApartmentApplicationStage, impl=String()), nullable=True)
    apartment = relationship("Apartment", backref="applications")
    tenant = relationship("Tenant", backref="applications")
