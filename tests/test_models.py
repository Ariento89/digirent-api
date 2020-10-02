from datetime import datetime
from tests.conftest import landlord
import pytest
from requests import status_codes
from sqlalchemy.orm.session import Session
from digirent.database.enums import HouseType, UserRole
from digirent.database.models import (
    Admin,
    Amenity,
    Apartment,
    Landlord,
    Tenant,
    User,
    LookingFor,
    BankDetail,
)


def test_user_looking_for_relationship(session: Session):
    user = Tenant(
        "fname",
        "lname",
        "email",
        "00000",
        "hashed",
        datetime.now().date(),
    )
    session.add(user)
    assert user.role == UserRole.TENANT
    session.flush()
    lfor = LookingFor(
        house_type=HouseType.BUNGALOW,
        city="test city",
        max_budget=70.5,
        tenant_id=user.id,
    )
    session.add(lfor)
    session.commit()
    assert user.looking_for == lfor
    assert lfor.tenant == user


def test_user_bank_detail_relationship(session: Session):
    user = Tenant(
        "fname",
        "lname",
        "email",
        "00000",
        "hashed",
        datetime.now().date(),
    )
    assert user.role == UserRole.TENANT
    session.add(user)
    session.flush()
    bank = BankDetail(
        account_name="acc name", account_number="0012345678910", user_id=user.id
    )
    session.add(bank)
    session.commit()
    assert user.bank_detail == bank
    assert bank.user == user


def test_landlord_apartment_relationship(session: Session, landlord: Landlord):
    apartment = Apartment(
        landlord_id=landlord.id,
        name="apartment name",
        monthly_price=350.55,
        utilities_price=20.55,
        address="somewhere",
        country="Netherlands",
        state="somestate",
        city="somecity",
        description="some description",
        house_type=HouseType.BUNGALOW,
        bedrooms=3,
        bathrooms=3,
        size=1400,
        furnish_type="some furnish type",
        available_from=datetime.now().date(),
        available_to=datetime.now().date(),
    )
    session.add(apartment)
    session.commit()
    assert session.query(Apartment).count()
    assert landlord.apartments == [apartment]
    assert not apartment.amenities
    assert not apartment.tenant


def test_tenant_apartment_relationship(
    session: Session, landlord: Landlord, tenant: Tenant
):
    apartment = Apartment(
        landlord_id=landlord.id,
        name="apartment name",
        monthly_price=350.55,
        utilities_price=20.55,
        address="somewhere",
        country="Netherlands",
        state="somestate",
        city="somecity",
        description="some description",
        house_type=HouseType.BUNGALOW,
        bedrooms=3,
        bathrooms=3,
        size=1400,
        furnish_type="some furnish type",
        available_from=datetime.now().date(),
        available_to=datetime.now().date(),
    )
    apartment.tenant_id = tenant.id
    session.add(apartment)
    session.commit()
    assert session.query(Apartment).count()
    assert landlord.apartments == [apartment]
    assert not apartment.amenities
    assert apartment.tenant == tenant
    assert tenant.apartment == apartment


def test_apartment_amenity_relationship(session: Session, landlord: Landlord):
    apartment = Apartment(
        landlord_id=landlord.id,
        name="apartment name",
        monthly_price=350.55,
        utilities_price=20.55,
        address="somewhere",
        country="Netherlands",
        state="somestate",
        city="somecity",
        description="some description",
        house_type=HouseType.BUNGALOW,
        bedrooms=3,
        bathrooms=3,
        size=1400,
        furnish_type="some furnish type",
        available_from=datetime.now().date(),
        available_to=datetime.now().date(),
    )
    amenity1 = Amenity(title="pool")
    amenity2 = Amenity(title="barn")
    apartment.amenities.append(amenity1)
    apartment.amenities.append(amenity2)
    session.add(apartment)
    session.commit()
    assert session.query(Apartment).count()
    assert session.query(Amenity).count() == 2
    assert landlord.apartments == [apartment]
    assert apartment.amenities == [amenity1, amenity2]
    assert not apartment.tenant