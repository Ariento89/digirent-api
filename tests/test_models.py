from datetime import datetime
from sqlalchemy.orm.session import Session
from digirent.app import Application
from digirent.database.enums import HouseType, UserRole
from digirent import util
from digirent.database.models import (
    Amenity,
    Apartment,
    Landlord,
    Tenant,
    LookingFor,
    BankDetail,
)


def test_user_looking_for_relationship(session: Session):
    user = Tenant(
        first_name="fname",
        last_name="lname",
        email="email",
        phone_number="00000",
        hashed_password="hashed",
        dob=datetime.now().date(),
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
        first_name="fname",
        last_name="lname",
        email="email",
        phone_number="00000",
        hashed_password="hashed",
        dob=datetime.now().date(),
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
    assert all(x in apartment.amenities for x in [amenity1, amenity2])
    assert not apartment.tenant


def test_tenant_percentage_profile(
    tenant: Tenant, file, application: Application, clear_upload
):
    copy_id_path = util.get_copy_ids_path()
    proof_of_income_path = util.get_proof_of_income_path()
    proof_of_enrollment_path = util.get_proof_of_enrollment_path()
    paths = [copy_id_path, proof_of_income_path, proof_of_enrollment_path]
    assert all(not application.file_service.list_files(path) for path in paths)
    assert tenant.profile_percentage == 0
    application.upload_copy_id(tenant, file, "pdf")
    assert tenant.profile_percentage == 20
    application.upload_proof_of_enrollment(tenant, file, "pdf")
    assert tenant.profile_percentage == 30
    application.upload_proof_of_income(tenant, file, "pdf")
    assert tenant.profile_percentage == 40


def test_landlord_percentage_profile(
    landlord: Landlord, file, application: Application, clear_upload
):
    copy_id_path = util.get_copy_ids_path()
    proof_of_income_path = util.get_proof_of_income_path()
    proof_of_enrollment_path = util.get_proof_of_enrollment_path()
    paths = [copy_id_path, proof_of_income_path, proof_of_enrollment_path]
    assert all(not application.file_service.list_files(path) for path in paths)
    assert landlord.profile_percentage == 0
    application.upload_copy_id(landlord, file, "pdf")
    assert landlord.profile_percentage == 30
