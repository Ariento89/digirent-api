import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.session import Session
from digirent.database.services.user import UserService
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
    new_dict["hashed_password"] = new_dict["password"]
    del new_dict["password"]
    with pytest.raises(IntegrityError) as e:
        user_service.create(session, **new_dict)
        assert "unique constraint" in str(e).lower()


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
    new_dict["hashed_password"] = new_dict["password"]
    del new_dict["password"]
    with pytest.raises(IntegrityError) as e:
        user_service.create(session, **new_dict)
        assert "unique constraint" in str(e).lower()


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
    xuser = user_service.get_by_email(session, user.email)
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
    xuser = user_service.get_by_phone_number(session, user.phone_number)
    assert xuser is not None
    assert user == xuser
