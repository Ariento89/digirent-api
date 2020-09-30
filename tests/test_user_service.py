from datetime import datetime
from tests.conftest import landlord_auth_header, user_create_data
import pytest
from sqlalchemy.orm.session import Session
from digirent.core.services.user import UserService
from digirent.database.models import Landlord, Tenant, User


@pytest.fixture
def user_data() -> dict:
    return {
        "first_name": "Test",
        "last_name": "Data",
        "email": "testemail@gmail.com",
        "dob": None,
        "password": "testpass",
        "phone_number": "00000000",
    }


def test_hash_password(user_service: UserService):
    password = "testpass"
    hashed_password = user_service.hash_password(password)
    assert password != hashed_password


def test_password_is_match(user_service: UserService):
    password = "testpass"
    hashed_password = user_service.hash_password(password)
    assert not user_service.password_is_match("wrong", hashed_password)
    assert user_service.password_is_match(password, hashed_password)


@pytest.mark.parametrize(
    "user_create_data",
    ["tenant_create_data", "landlord_create_data", "admin_create_data"],
    indirect=True,
)
def test_create_user_ok(
    user_service: UserService, user_create_data: dict, session: Session
):
    assert session.query(User).count() == 0
    user_create_data["dob"] = (
        None if "dob" not in user_create_data else user_create_data["dob"]
    )
    user: User = user_service.create_user(session, **user_create_data)
    assert user.email == user_create_data["email"]
    assert user.id
    assert user.phone_number == user_create_data["phone_number"]
    assert user.first_name == user_create_data["first_name"]
    assert user.last_name == user_create_data["last_name"]
    assert user.hashed_password != user_create_data["password"]


@pytest.mark.parametrize(
    "user, user_create_data",
    [
        ("tenant", "tenant_create_data"),
        ("landlord", "landlord_create_data"),
        ("admin", "admin_create_data"),
    ],
    indirect=True,
)
def test_create_user_with_existing_email_fail(
    user: User,
    user_create_data: dict,
    session: Session,
    user_service: UserService,
):
    assert session.query(User).count() == 1
    new_dict = {}
    new_dict = {**user_create_data, "phone_number": "000000000"}
    result = user_service.create_user(session, **new_dict)
    assert isinstance(result, str)
    assert "email" in result.lower()


@pytest.mark.parametrize(
    "user, user_create_data",
    [
        ("tenant", "tenant_create_data"),
        ("landlord", "landlord_create_data"),
        ("admin", "admin_create_data"),
    ],
    indirect=True,
)
def test_create_user_with_existing_phonenumber_fail(
    user: User,
    session: Session,
    user_service: UserService,
    user_create_data: dict,
):
    assert session.query(User).count() == 1
    new_dict = {**user_create_data, "email": "somedifferent@email.com"}
    result = user_service.create_user(session, **new_dict)
    assert isinstance(result, str)
    assert "phone number" in result.lower()


@pytest.mark.parametrize(
    "user",
    [
        "tenant",
        "landlord",
        "admin",
    ],
    indirect=True,
)
def test_get_user_by_id(user: User, session: Session, user_service: UserService):
    assert session.query(User).count() == 1
    xuser = user_service.get_user_by_id(session, user.id)
    assert xuser is not None
    assert user == xuser


@pytest.mark.parametrize(
    "user",
    [
        "tenant",
        "landlord",
        "admin",
    ],
    indirect=True,
)
def test_get_user_by_email(user: User, session: Session, user_service: UserService):
    assert session.query(User).count() == 1
    xuser = user_service.get_user_by_email(session, user.email)
    assert xuser is not None
    assert user == xuser


@pytest.mark.parametrize(
    "user",
    [
        "tenant",
        "landlord",
        "admin",
    ],
    indirect=True,
)
def test_get_user_by_phonenumber(
    user: User, session: Session, user_service: UserService
):
    assert session.query(User).count() == 1
    xuser = user_service.get_user_by_phone_number(session, user.phone_number)
    assert xuser is not None
    assert user == xuser


@pytest.mark.parametrize(
    "user",
    [
        "tenant",
        "landlord",
        "admin",
    ],
    indirect=True,
)
def test_update_single_user_profile_information(
    user: User, session: Session, user_service: UserService
):
    assert session.query(User).count() == 1
    new_first_name = "updated first name"
    prev_last_name = user.last_name
    prev_email = user.email
    prev_phone_number = user.phone_number
    prev_gender = user.gender
    prev_city = user.city
    prev_dob = user.dob
    assert user.first_name != new_first_name
    updated_user = user_service.update_user(
        session,
        user.id,
        first_name=new_first_name,
        last_name=prev_last_name,
        email=prev_email,
        phone_number=prev_phone_number,
        gender=prev_gender,
        city=prev_city,
        dob=prev_dob,
    )
    userdb = session.query(User).get(user.id)
    assert userdb.first_name == new_first_name
    assert userdb.last_name == prev_last_name
    assert userdb.email == prev_email
    assert userdb.phone_number == prev_phone_number
    assert userdb.gender == prev_gender
    assert userdb.city == prev_city
    assert userdb.dob == prev_dob


@pytest.mark.parametrize(
    "user",
    [
        "tenant",
        "landlord",
        "admin",
    ],
    indirect=True,
)
def test_update_multiple_user_profile_information(
    user: User, session: Session, user_service: UserService
):
    assert session.query(User).count() == 1
    new_first_name = "updated first name"
    new_last_name = "updated last name"
    new_dob = datetime(4000, 5, 12).date()
    prev_last_name = user.last_name
    prev_email = user.email
    prev_phone_number = user.phone_number
    prev_gender = user.gender
    prev_city = user.city
    prev_dob = user.dob
    assert user.first_name != new_first_name
    assert prev_last_name != new_last_name
    assert prev_dob != new_dob
    updated_user = user_service.update_user(
        session,
        user.id,
        first_name=new_first_name,
        last_name=new_last_name,
        email=prev_email,
        phone_number=prev_phone_number,
        gender=prev_gender,
        city=prev_city,
        dob=new_dob,
    )
    userdb = session.query(User).get(user.id)
    assert userdb.first_name == new_first_name
    assert userdb.last_name == new_last_name
    assert userdb.email == prev_email
    assert userdb.phone_number == prev_phone_number
    assert userdb.gender == prev_gender
    assert userdb.city == prev_city
    assert userdb.dob == new_dob


# def test_update_user_email_or_phone_to_existing_fail(
#     tenant: Tenant, landlord: Landlord, session: Session, user_service: UserService
# ):
#     assert session.query(User).count() == 2
#     prev_tenant_email = tenant.email
#     new_tenant_email = landlord.email
#     prev_tenant_phone_number = tenant.phone_number
#     new_phone_number = landlord.phone_number
#     assert prev_tenant_email != new_tenant_email
#     assert tenant.phone_number != new_phone_number

#     result = user_service.update_user(
#         session,
#         tenant.id,
#         first_name=tenant.first_name,
#         last_name=tenant.last_name,
#         email=new_tenant_email,
#         phone_number=tenant.phone_number,
#         gender=tenant.gender,
#         city=tenant.city,
#         dob=tenant.dob,
#     )
#     assert isinstance(result, str)
#     tenantdb = session.query(User).get(tenant.id)
#     assert tenantdb.email != new_tenant_email
#     assert tenantdb.email == prev_tenant_email

#     result = user_service.update_user(
#         session,
#         tenant.id,
#         first_name=tenant.first_name,
#         last_name=tenant.last_name,
#         email=prev_tenant_email,
#         phone_number=new_phone_number,
#         gender=tenant.gender,
#         city=tenant.city,
#         dob=tenant.dob,
#     )
#     assert isinstance(result, str)
#     tenantdb = session.query(User).get(tenant.id)
#     assert tenantdb.phone_number != new_phone_number
#     assert tenantdb.phone_number == prev_tenant_phone_number
