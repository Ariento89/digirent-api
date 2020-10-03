import digirent.util as util
from digirent.database.services.user import UserService
from digirent.database.enums import HouseType
from tests.test_user_service import user_data
from tests.conftest import (
    admin_create_data,
    application,
    user_create_data,
    user_service,
)
from digirent.app.error import ApplicationError
import pytest
from digirent.app import Application
from sqlalchemy.orm.session import Session
from digirent.database.models import (
    Amenity,
    Landlord,
    LookingFor,
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
    with pytest.raises(ApplicationError) as e:
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
    with pytest.raises(ApplicationError) as e:
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
    user_service: UserService,
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
    with pytest.raises(ApplicationError) as e:
        application.create_amenity(session, "hello")
        assert "exists" in str(e).lower()