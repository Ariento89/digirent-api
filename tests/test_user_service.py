from tests.conftest import user_create_data
import pytest
from sqlalchemy.orm.session import Session
from digirent.core.services.user import UserService
from digirent.database.models import User


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