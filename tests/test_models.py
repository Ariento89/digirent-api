from datetime import datetime
import pytest
from sqlalchemy.orm.session import Session
from sqlalchemy.exc import IntegrityError
from digirent.app import Application
from digirent.database.enums import (
    BookingRequestStatus,
    FurnishType,
    HouseType,
    SocialAccountType,
    UserRole,
)
from digirent import util
from digirent.database.models import (
    Amenity,
    Apartment,
    ApartmentApplication,
    BookingRequest,
    Landlord,
    SocialAccount,
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
        furnish_type=FurnishType.FURNISHED,
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
        furnish_type=FurnishType.UNFURNISHED,
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
        furnish_type=FurnishType.FURNISHED,
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


def test_apartment_applications(tenant: Tenant, apartment: Apartment, session: Session):
    apartment_application = ApartmentApplication(
        tenant_id=tenant.id, apartment_id=apartment.id
    )
    session.add(apartment_application)
    session.commit()
    assert tenant.applications == [apartment_application]
    assert apartment.applications == [apartment_application]
    assert apartment_application.stage is None


def test_booking_request_relationships(
    apartment: Apartment,
    session: Session,
    tenant: Tenant,
):
    booking_request = BookingRequest(tenant_id=tenant.id, apartment_id=apartment.id)
    session.add(booking_request)
    session.commit()
    assert booking_request.status == BookingRequestStatus.PENDING


def test_accept_booking_request(
    apartment: Apartment,
    session: Session,
    tenant: Tenant,
    apartment_application: ApartmentApplication,
):
    booking_request = BookingRequest(tenant_id=tenant.id, apartment_id=apartment.id)
    session.add(booking_request)
    session.commit()
    assert booking_request.status == BookingRequestStatus.PENDING
    booking_request.accept(apartment_application)
    session.commit()
    assert booking_request.status == BookingRequestStatus.ACCEPTED
    assert booking_request.apartment_application == apartment_application


def test_reject_booking_request(
    apartment: Apartment,
    session: Session,
    tenant: Tenant,
):
    booking_request = BookingRequest(tenant_id=tenant.id, apartment_id=apartment.id)
    booking_request.reject()
    session.add(booking_request)
    session.commit()
    assert booking_request.status == BookingRequestStatus.REJECTED
    assert not booking_request.apartment_application


def test_social_account_with_multiple_rows_of_same_account_email_and_diff_account_type_ok(
    tenant: Tenant, session: Session
):
    assert not session.query(SocialAccount).count()
    email = "some@email.com"
    sa1 = SocialAccount(
        user=tenant, account_type=SocialAccountType.GOOGLE, account_email=email
    )
    session.add(sa1)
    session.commit()
    sa2 = SocialAccount(
        user=tenant, account_type=SocialAccountType.FACEBOOK, account_email=email
    )
    session.add(sa2)
    session.commit()


def test_social_account_with_multiple_rows_of_diff_account_email_and_same_account_type_ok(
    tenant: Tenant, session: Session
):
    assert not session.query(SocialAccount).count()
    account_type = SocialAccountType.GOOGLE
    sa1 = SocialAccount(
        user=tenant, account_type=account_type, account_email="one@email.com"
    )
    session.add(sa1)
    session.commit()
    sa2 = SocialAccount(
        user=tenant, account_type=account_type, account_email="two@email.com"
    )
    session.add(sa2)
    session.commit()


def test_social_account_with_multiple_rows_of_same_account_email_and_account_type_fail(
    tenant: Tenant, session: Session
):
    assert not session.query(SocialAccount).count()
    email = "some@email.com"
    account_type = SocialAccountType.GOOGLE
    sa1 = SocialAccount(user=tenant, account_type=account_type, account_email=email)
    session.add(sa1)
    session.commit()
    sa2 = SocialAccount(user=tenant, account_type=account_type, account_email=email)
    session.add(sa2)
    with pytest.raises(IntegrityError):
        session.commit()


def test_social_account_with_multiple_rows_of_same_account_id_and_diff_account_type_ok(
    tenant: Tenant, session: Session
):
    assert not session.query(SocialAccount).count()
    acc_id = "someid"
    sa1 = SocialAccount(
        user=tenant, account_type=SocialAccountType.GOOGLE, account_id=acc_id
    )
    session.add(sa1)
    session.commit()
    sa2 = SocialAccount(
        user=tenant, account_type=SocialAccountType.FACEBOOK, account_id=acc_id
    )
    session.add(sa2)
    session.commit()


def test_social_account_with_multiple_rows_of_diff_account_id_and_same_account_type_ok(
    tenant: Tenant, session: Session
):
    assert not session.query(SocialAccount).count()
    account_type = SocialAccountType.GOOGLE
    sa1 = SocialAccount(user=tenant, account_type=account_type, account_id="oneid")
    session.add(sa1)
    session.commit()
    sa2 = SocialAccount(user=tenant, account_type=account_type, account_id="twoid")
    session.add(sa2)
    session.commit()


def test_social_account_with_multiple_rows_of_same_account_id_and_account_type_fail(
    tenant: Tenant, session: Session
):
    assert not session.query(SocialAccount).count()
    acc_id = "someid"
    account_type = SocialAccountType.GOOGLE
    sa1 = SocialAccount(user=tenant, account_type=account_type, account_id=acc_id)
    session.add(sa1)
    session.commit()
    sa2 = SocialAccount(user=tenant, account_type=account_type, account_id=acc_id)
    session.add(sa2)
    with pytest.raises(IntegrityError):
        session.commit()
