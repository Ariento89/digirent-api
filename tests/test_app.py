from datetime import datetime
import digirent.util as util
from digirent.database.enums import (
    BookingRequestStatus,
    FurnishType,
    HouseType,
    SocialAccountType,
)
from digirent.app.error import ApplicationError
import pytest
from digirent.app import Application
from sqlalchemy.orm.session import Session
from digirent.database.models import (
    Amenity,
    Apartment,
    BookingRequest,
    Landlord,
    SocialAccount,
    Tenant,
    User,
    UserRole,
)


def test_create_tenant(
    application: Application, session: Session, tenant_create_data: dict
):
    del tenant_create_data["role"]
    assert not session.query(User).count()
    tenant: User = application.create_tenant(session, **tenant_create_data)
    assert tenant
    assert tenant.dob
    assert tenant.role == UserRole.TENANT
    assert session.query(User).count() == 1


def test_create_landlord(
    application: Application, session: Session, landlord_create_data: dict
):
    del landlord_create_data["role"]
    assert not session.query(User).count()
    landlord: User = application.create_landlord(session, **landlord_create_data)
    assert landlord
    assert not landlord.dob
    assert landlord.role == UserRole.LANDLORD
    assert session.query(User).count() == 1


def test_create_admin(
    application: Application, session: Session, admin_create_data: dict
):
    del admin_create_data["role"]
    assert not session.query(User).count()
    admin: User = application.create_admin(session, **admin_create_data)
    assert admin
    assert not admin.dob
    assert admin.role == UserRole.ADMIN
    assert session.query(User).count() == 1


@pytest.mark.parametrize(
    "user",
    [
        "tenant",
        "landlord",
        "admin",
    ],
    indirect=True,
)
def test_update_user_profile(user: User, session: Session, application: Application):
    prev_firstname = user.first_name
    prev_lastname = user.last_name
    prev_city = user.city
    new_fname = "new updated fname"
    new_lname = "new updated lname"
    new_city = "new updated city"
    assert prev_firstname != new_fname
    assert prev_lastname != new_lname
    assert prev_city != new_city
    application.update_profile(
        session,
        user,
        first_name=new_fname,
        last_name=new_lname,
        city=new_city,
        email=user.email,
        phone_number=user.phone_number,
        gender=user.gender,
        dob=user.dob,
    )
    xuser = session.query(User).get(user.id)
    assert xuser.first_name == new_fname
    assert xuser.last_name == new_lname
    assert xuser.city == new_city
    assert xuser.email == user.email
    assert xuser.phone_number == user.phone_number
    assert xuser.gender == user.gender
    assert xuser.dob == user.dob


def test_update_user_email_to_existing_email_fail(
    tenant: Tenant, landlord: Landlord, session: Session, application: Application
):
    prev_email = tenant.email
    assert prev_email != landlord.email
    with pytest.raises(ApplicationError):
        application.update_profile(
            session,
            tenant,
            email=landlord.email,
            first_name=tenant.first_name,
            last_name=tenant.last_name,
            gender=tenant.gender,
            phone_number=tenant.phone_number,
            city=tenant.city,
            dob=tenant.dob,
        )


def test_update_user_phone_number_to_existing_email_fail(
    tenant: Tenant, landlord: Landlord, session: Session, application: Application
):
    prev_phone_number = tenant.phone_number
    assert prev_phone_number != landlord.phone_number
    with pytest.raises(ApplicationError):
        application.update_profile(
            session,
            tenant,
            phone_number=landlord.phone_number,
            first_name=tenant.first_name,
            last_name=tenant.last_name,
            gender=tenant.gender,
            email=tenant.email,
            city=tenant.city,
            dob=tenant.dob,
        )


@pytest.mark.parametrize(
    "user",
    [
        "tenant",
        "landlord",
        "admin",
    ],
    indirect=True,
)
def test_set_bank_detail(user: User, session: Session, application: Application):
    assert not user.bank_detail
    account_name = "Test Account Name"
    account_number = "Test Account Number"
    application.set_bank_detail(session, user, account_name, account_number)
    xuser = session.query(User).get(user.id)
    assert xuser.bank_detail
    assert xuser.bank_detail.account_name == account_name
    assert xuser.bank_detail.account_number == account_number
    assert xuser.bank_detail.user_id == user.id


@pytest.mark.parametrize(
    "user, user_create_data",
    [
        ("tenant", "tenant_create_data"),
        ("landlord", "landlord_create_data"),
        ("admin", "admin_create_data"),
    ],
    indirect=True,
)
def test_update_password(
    user: User,
    user_create_data: dict,
    session: Session,
    application: Application,
):
    old_password = user_create_data["password"]
    new_password = "newuserpassword"
    assert old_password != new_password
    application.update_password(session, user, old_password, new_password)
    assert user.hashed_password != old_password
    assert user.hashed_password != new_password
    assert not util.password_is_match(old_password, user.hashed_password)
    assert util.password_is_match(new_password, user.hashed_password)


@pytest.mark.parametrize(
    "user",
    [
        "tenant",
        "landlord",
        "admin",
    ],
    indirect=True,
)
def test_update_description(
    user: User,
    session: Session,
    application: Application,
):
    prev_description = user.description
    new_description = "new description"
    assert prev_description != new_description
    application.update_profile(
        session,
        user,
        first_name=user.first_name,
        last_name=user.last_name,
        email=user.email,
        phone_number=user.phone_number,
        city=user.city,
        gender=user.gender,
        dob=user.dob,
        description=new_description,
    )
    xuser = session.query(User).get(user.id)
    assert xuser.description == new_description


def test_set_looking_for(tenant: Tenant, session: Session, application: Application):
    assert not tenant.looking_for
    house_type = HouseType.BUNGALOW
    city = "preferred city"
    max_budget = 45.78
    application.set_looking_for(session, tenant, house_type, city, max_budget)
    assert tenant.looking_for
    assert tenant.looking_for.id
    assert tenant.looking_for.house_type == HouseType.BUNGALOW
    assert tenant.looking_for.city == city
    assert tenant.looking_for.max_budget == max_budget


def test_create_amenity_ok(session: Session, application: Application):
    assert not session.query(Amenity).count()
    application.create_amenity(session, "hello")
    assert session.query(Amenity).count() == 1
    amenity = session.query(Amenity).all()[0]
    assert amenity.title == "hello"


def test_create_exisiting_amenity_fail(session: Session, application: Application):
    assert not session.query(Amenity).count()
    application.create_amenity(session, "hello")
    assert session.query(Amenity).count() == 1
    amenity = session.query(Amenity).all()[0]
    assert amenity.title == "hello"
    with pytest.raises(ApplicationError):
        application.create_amenity(session, "hello")


def test_create_apartment_ok(
    session: Session, landlord: Landlord, application: Application
):
    assert not session.query(Apartment).count()
    application.create_apartment(
        session,
        landlord,
        name="Apartment Name",
        monthly_price=450.70,
        utilities_price=320.15,
        address="some address",
        country="Nigeria",
        state="Kano",
        city="Kano",
        description="Apartment description",
        house_type=HouseType.DUPLEX,
        bedrooms=3,
        bathrooms=4,
        size=1200,
        longitude=1324.4,
        latitude=234.5,
        furnish_type=FurnishType.FURNISHED,
        available_from=datetime.now().date(),
        available_to=datetime.now().date(),
        amenities=[],
    )
    assert session.query(Apartment).count() == 1
    apartment: Apartment = session.query(Apartment).all()[0]
    apartment.landlord == landlord
    apartment.name == "Apartment Name"
    apartment.monthly_price == 450.7
    apartment.utilities_price == 320.15
    apartment.address == "some address"
    apartment.country == "Nigeria"
    apartment.state == "Kano"
    apartment.city == "Kano"
    apartment.description == "Apartment description"
    apartment.house_type == HouseType.DUPLEX,
    apartment.bedrooms == 3
    apartment.bathrooms == 4
    apartment.size == 1200
    apartment.furnish_type == FurnishType.FURNISHED
    apartment.available_from == datetime.now().date()
    apartment.available_to == datetime.now().date(),
    apartment.amenities == []


def test_update_apartment_ok(
    session: Session, landlord: Landlord, application: Application
):
    application.create_amenity(session, "first")
    amenity1 = session.query(Amenity).filter(Amenity.title == "first").first()
    assert not session.query(Apartment).count()
    application.create_apartment(
        session,
        landlord,
        name="Apartment Name",
        monthly_price=450.70,
        utilities_price=320.15,
        address="some address",
        country="Nigeria",
        state="Kano",
        city="Kano",
        description="Apartment description",
        house_type=HouseType.DUPLEX,
        bedrooms=3,
        bathrooms=4,
        size=1200,
        longitude=1324.5,
        latitude=324.6,
        furnish_type=FurnishType.UNFURNISHED,
        available_from=datetime.now().date(),
        available_to=datetime.now().date(),
        amenities=[amenity1],
    )
    assert session.query(Apartment).count() == 1
    apartment: Apartment = session.query(Apartment).all()[0]
    apartment.landlord == landlord
    apartment.name == "Apartment Name"
    apartment.monthly_price == 450.7
    apartment.utilities_price == 320.15
    apartment.address == "some address"
    apartment.country == "Nigeria"
    apartment.state == "Kano"
    apartment.city == "Kano"
    apartment.description == "Apartment description"
    apartment.house_type == HouseType.DUPLEX,
    apartment.bedrooms == 3
    apartment.bathrooms == 4
    apartment.size == 1200
    apartment.furnish_type == FurnishType.UNFURNISHED
    apartment.available_from == datetime.now().date()
    apartment.available_to == datetime.now().date(),
    apartment.amenities == [amenity1]
    application.create_amenity(session, "pool")
    application.create_amenity(session, "barn")
    assert session.query(Amenity).count() == 3
    amenities = session.query(Amenity).all()
    application.update_apartment(
        session, apartment.landlord, apartment.id, amenities=amenities
    )
    xapartment = application.apartment_service.get(session, apartment.id)
    assert xapartment.amenities == amenities


def test_landlord_invite_tenant_to_apply(
    application: Application,
    session: Session,
    landlord: Landlord,
    tenant: Tenant,
    apartment: Apartment,
):
    assert not session.query(BookingRequest).count()
    booking_request: BookingRequest = application.invite_tenant_to_apply(
        session, landlord, tenant, apartment
    )
    assert booking_request.apartment_id == apartment.id
    assert booking_request.tenant_id == tenant.id
    assert not booking_request.apartment_application_id
    assert booking_request.status == BookingRequestStatus.PENDING


def test_tenant_accept_invitation_to_apply_for_apartment(
    application: Application,
    session: Session,
    tenant: Tenant,
    booking_request: BookingRequest,
):
    application.accept_application_invitation(session, tenant, booking_request)
    booking_req = session.query(BookingRequest).get(booking_request.id)
    assert booking_req.status == BookingRequestStatus.ACCEPTED
    assert booking_req.apartment_application_id is not None


def test_tenant_reject_invitation_to_apply_for_apartment(
    application: Application,
    session: Session,
    tenant: Tenant,
    booking_request: BookingRequest,
):
    application.reject_application_invitation(session, tenant, booking_request)
    booking_req = session.query(BookingRequest).get(booking_request.id)
    assert booking_req.status == BookingRequestStatus.REJECTED
    assert not booking_req.apartment_application_id


def test_tenant_reject_accepted_invitation_fail(
    application: Application,
    session: Session,
    tenant: Tenant,
    booking_request: BookingRequest,
):
    booking_req = application.accept_application_invitation(
        session, tenant, booking_request
    )
    with pytest.raises(ApplicationError):
        application.reject_application_invitation(session, tenant, booking_req)


def test_tenant_accept_rejected_invitation_fail(
    application: Application,
    session: Session,
    tenant: Tenant,
    booking_request: BookingRequest,
):
    booking_req = application.reject_application_invitation(
        session, tenant, booking_request
    )
    with pytest.raises(ApplicationError):
        application.accept_application_invitation(session, tenant, booking_req)


def test_invite_tenant_for_already_awarded_apartment_fail(
    application: Application,
    session: Session,
    tenant: Tenant,
    another_tenant: Tenant,
    landlord: Landlord,
    awarded_apartment_application,
):
    with pytest.raises(ApplicationError):
        application.invite_tenant_to_apply(
            session, landlord, another_tenant, awarded_apartment_application.apartment
        )


def test_non_authenticated_user_authenticate_google_non_existing_user_ok(
    session: Session, application: Application
):
    assert not session.query(User).count()
    assert not session.query(SocialAccount).count()
    access_token = "mock_access_token"
    id_token = "mock_id_token"
    email = "mock@email.com"
    first_name = "mockfname"
    last_name = "mocklname"
    role = UserRole.TENANT
    result = application.authenticate_google(
        session, access_token, id_token, email, first_name, last_name, role
    )
    assert isinstance(result, bytes)
    assert session.query(User).count()
    assert session.query(SocialAccount).count()
    user = session.query(User).all()[0]
    account = session.query(SocialAccount).all()[0]
    assert account in user.social_accounts
    assert account.access_token == access_token
    assert account.id_token == id_token
    assert account.user == user
    assert account.account_email == email
    assert not account.account_id
    assert user.email == email
    assert user.first_name == first_name
    assert user.last_name == last_name
    assert not user.hashed_password
    assert user.role == UserRole.TENANT
    assert account.account_type == SocialAccountType.GOOGLE


def test_authenticate_user_created_from_google_auth_ok(
    session: Session, application: Application
):
    assert not session.query(User).count()
    assert not session.query(SocialAccount).count()
    access_token = "mock_access_token"
    id_token = "mock_id_token"
    email = "mock@email.com"
    first_name = "mockfname"
    last_name = "mocklname"
    role = UserRole.TENANT
    result = application.authenticate_google(
        session, access_token, id_token, email, first_name, last_name, role
    )
    assert isinstance(result, bytes)
    result = application.authenticate_google(
        session,
        "diff_access_tooken",
        "diff_id_token",
        email,
        "diff_first_name",
        "diff_last_name",
        role,
    )
    assert isinstance(result, bytes)
    assert session.query(User).count() == 1
    assert session.query(SocialAccount).count() == 1
    user = session.query(User).all()[0]
    account = session.query(SocialAccount).all()[0]
    assert account in user.social_accounts
    assert account.access_token == "diff_access_tooken"
    assert account.id_token == "diff_id_token"
    assert account.user == user
    assert account.account_email == email
    assert not account.account_id
    assert user.email == email
    assert user.first_name == first_name
    assert user.last_name == last_name
    assert not user.hashed_password
    assert user.role == UserRole.TENANT
    assert account.account_type == SocialAccountType.GOOGLE


def test_authenticated_user_link_google_acccount_to_existing_user_ok(
    session: Session, application: Application, tenant: Tenant
):
    assert session.query(User).count() == 1
    assert not session.query(SocialAccount).count()
    access_token = "mock_access_token"
    id_token = "mock_id_token"
    email = tenant.email
    first_name = "mockfname"
    last_name = "mocklname"
    role = UserRole.TENANT
    result = application.authenticate_google(
        session,
        access_token,
        id_token,
        email,
        first_name,
        last_name,
        role,
        authenticated_user=tenant,
    )
    assert isinstance(result, bytes)
    assert session.query(User).count() == 1
    assert session.query(SocialAccount).count() == 1
    user = session.query(User).all()[0]
    account = session.query(SocialAccount).all()[0]
    assert account in user.social_accounts
    assert account.access_token == access_token
    assert account.id_token == id_token
    assert account.account_email == email
    assert account.user == user
    assert user.email == email
    assert user.first_name == tenant.first_name
    assert user.last_name == tenant.last_name
    assert user.hashed_password
    assert user.role == UserRole.TENANT
    assert account.account_type == SocialAccountType.GOOGLE


def test_non_authenticated_user_sign_up_with_google_when_user_with_email_already_exists_fail(
    tenant: Tenant, session: Session, application: Application
):
    assert session.query(User).count() == 1
    assert not session.query(SocialAccount).count()
    with pytest.raises(ApplicationError):
        application.authenticate_google(
            session,
            "accesstoken",
            "idtoken",
            tenant.email,
            "fname",
            "lname",
            UserRole.LANDLORD,
        )


def test_authenticated_user_link_google_account_already_linked_to_another_user_fail(
    tenant: Tenant, landlord: Landlord, session: Session, application: Application
):
    assert session.query(User).count() == 2
    assert not session.query(SocialAccount).count()
    email = "someemail"
    access_token = "someacctoken"
    id_token = "someidtoken"
    fname = "fname"
    lname = "lname"
    application.authenticate_google(
        session, access_token, id_token, email, fname, lname, UserRole.TENANT, tenant
    )
    assert session.query(SocialAccount).count()
    assert session.query(SocialAccount).all()[0].user == tenant
    with pytest.raises(ApplicationError):
        application.authenticate_google(
            session,
            "diff token",
            "diff id_token",
            email,
            "diff fname",
            "diff lname",
            UserRole.LANDLORD,
            landlord,
        )


def test_authenticated_user_link_a_different_google_account_from_already_linked_one_ok(
    tenant: Tenant, session: Session, application: Application
):
    assert session.query(User).count() == 1
    assert not session.query(SocialAccount).count()
    application.authenticate_google(
        session,
        "oneaccess_token",
        "oneid_token",
        "one_email",
        "onefname",
        "onelname",
        UserRole.TENANT,
        tenant,
    )
    assert session.query(SocialAccount).count()
    saccount = session.query(SocialAccount).all()[0]
    assert saccount.user == tenant
    assert saccount.account_email == "one_email"
    assert saccount.access_token == "oneaccess_token"
    assert saccount.id_token == "oneid_token"
    application.authenticate_google(
        session,
        "diff token",
        "diff id_token",
        "diff email",
        "diff fname",
        "diff lname",
        UserRole.LANDLORD,
        tenant,
    )
    saccount = session.query(SocialAccount).all()[0]
    assert saccount.user == tenant
    assert saccount.account_email == "diff email"
    assert saccount.access_token == "diff token"
    assert saccount.id_token == "diff id_token"


def test_non_authenticated_user_authenticate_facebook_non_existing_user_ok(
    session: Session, application: Application
):
    assert not session.query(User).count()
    assert not session.query(SocialAccount).count()
    email = "mock@email.com"
    first_name = "mockfname"
    last_name = "mocklname"
    mock_id = "mockfbid"
    access_token = "acc_token"
    role = UserRole.TENANT
    result = application.authenticate_facebook(
        session, mock_id, access_token, email, first_name, last_name, role
    )
    assert isinstance(result, bytes)
    assert session.query(User).count()
    assert session.query(SocialAccount).count()
    user = session.query(User).all()[0]
    account = session.query(SocialAccount).all()[0]
    assert account in user.social_accounts
    assert account.access_token == access_token
    assert not account.id_token
    assert account.user == user
    assert account.account_email == email
    assert account.account_id == mock_id
    assert user.email == email
    assert user.first_name == first_name
    assert user.last_name == last_name
    assert not user.hashed_password
    assert user.role == UserRole.TENANT
    assert account.account_type == SocialAccountType.FACEBOOK


def test_authenticate_user_created_from_facebook_auth_ok(
    session: Session, application: Application
):
    assert not session.query(User).count()
    assert not session.query(SocialAccount).count()
    mock_id = "mockid"
    access_token = "acctoken"
    email = "mock@email.com"
    first_name = "mockfname"
    last_name = "mocklname"
    role = UserRole.TENANT
    result = application.authenticate_facebook(
        session, mock_id, access_token, email, first_name, last_name, role
    )
    assert isinstance(result, bytes)
    result = application.authenticate_facebook(
        session,
        mock_id,
        "diff_acc_token",
        email,
        "diff_first_name",
        "diff_last_name",
        role,
    )
    assert isinstance(result, bytes)
    assert session.query(User).count() == 1
    assert session.query(SocialAccount).count() == 1
    user = session.query(User).all()[0]
    account = session.query(SocialAccount).all()[0]
    assert account in user.social_accounts
    assert account.access_token == "diff_acc_token"
    assert not account.id_token
    assert account.user == user
    assert account.account_email == email
    assert account.account_id == mock_id
    assert user.email == email
    assert user.first_name == first_name
    assert user.last_name == last_name
    assert not user.hashed_password
    assert user.role == UserRole.TENANT
    assert account.account_type == SocialAccountType.FACEBOOK


def test_authenticated_user_link_facebook_acccount_to_existing_user_ok(
    session: Session, application: Application, tenant: Tenant
):
    assert session.query(User).count() == 1
    assert not session.query(SocialAccount).count()
    access_token = "mock_access_token"
    mockid = "mock_id"
    email = tenant.email
    first_name = "mockfname"
    last_name = "mocklname"
    role = UserRole.TENANT
    result = application.authenticate_facebook(
        session,
        mockid,
        access_token,
        email,
        first_name,
        last_name,
        role,
        authenticated_user=tenant,
    )
    assert isinstance(result, bytes)
    assert session.query(User).count() == 1
    assert session.query(SocialAccount).count() == 1
    user = session.query(User).all()[0]
    account = session.query(SocialAccount).all()[0]
    assert account in user.social_accounts
    assert account.access_token == access_token
    assert not account.id_token
    assert account.user == user
    assert account.account_email == email
    assert user.email == email
    assert user.first_name == tenant.first_name
    assert user.last_name == tenant.last_name
    assert user.hashed_password
    assert user.role == UserRole.TENANT
    assert account.account_id == mockid
    assert account.account_type == SocialAccountType.FACEBOOK


def test_non_authenticated_user_sign_up_with_facebook_when_user_with_email_already_exists_fail(
    tenant: Tenant, session: Session, application: Application
):
    assert session.query(User).count() == 1
    assert not session.query(SocialAccount).count()
    with pytest.raises(ApplicationError):
        application.authenticate_facebook(
            session,
            "userid",
            "accesstoken",
            tenant.email,
            "fname",
            "lname",
            UserRole.LANDLORD,
        )


def test_authenticated_user_link_facebook_account_already_linked_to_another_user_fail(
    tenant: Tenant, landlord: Landlord, session: Session, application: Application
):
    assert session.query(User).count() == 2
    assert not session.query(SocialAccount).count()
    email = "someemail"
    access_token = "someacctoken"
    mockid = "someid"
    fname = "fname"
    lname = "lname"
    application.authenticate_facebook(
        session, mockid, access_token, email, fname, lname, UserRole.TENANT, tenant
    )
    assert session.query(SocialAccount).count()
    assert session.query(SocialAccount).all()[0].user == tenant
    with pytest.raises(ApplicationError):
        application.authenticate_facebook(
            session,
            mockid,
            "diff token",
            "diff email",
            "diff fname",
            "diff lname",
            UserRole.LANDLORD,
            landlord,
        )


def test_authenticated_user_link_a_different_facebook_account_from_already_linked_one_ok(
    tenant: Tenant, session: Session, application: Application
):
    assert session.query(User).count() == 1
    assert not session.query(SocialAccount).count()
    application.authenticate_facebook(
        session,
        "oneid",
        "oneaccess_token",
        "one_email",
        "onefname",
        "onelname",
        UserRole.TENANT,
        tenant,
    )
    assert session.query(SocialAccount).count()
    saccount = session.query(SocialAccount).all()[0]
    assert saccount.user == tenant
    assert saccount.account_email == "one_email"
    assert saccount.access_token == "oneaccess_token"
    assert saccount.account_id == "oneid"
    application.authenticate_facebook(
        session,
        "diff id",
        "diff token",
        "diff email",
        "diff fname",
        "diff lname",
        UserRole.LANDLORD,
        tenant,
    )
    saccount = session.query(SocialAccount).all()[0]
    assert saccount.user == tenant
    assert saccount.account_email == "diff email"
    assert saccount.access_token == "diff token"
    assert saccount.account_id == "diff id"
