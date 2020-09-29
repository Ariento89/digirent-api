from jwt import PyJWTError
import pytest
from sqlalchemy.orm.session import Session
from digirent.core.services.user import UserService
from digirent.core.services.auth import AuthService
from digirent.database.models import User


@pytest.mark.parametrize(
    "user, user_create_data",
    [
        ("tenant", "tenant_create_data"),
        ("landlord", "landlord_create_data"),
        ("admin", "admin_create_data"),
    ],
    indirect=True,
)
def test_authenticate_user_by_email_ok(
    user,
    user_create_data,
    auth_service: AuthService,
    session: Session,
):
    assert session.query(User).count() == 1
    token = auth_service.authenticate(
        session, user_create_data["email"], user_create_data["password"]
    )
    assert token
    assert isinstance(token, bytes)


@pytest.mark.parametrize(
    "user, user_create_data",
    [
        ("tenant", "tenant_create_data"),
        ("landlord", "landlord_create_data"),
        ("admin", "admin_create_data"),
    ],
    indirect=True,
)
def test_authenticate_user_by_phonenumber_ok(
    auth_service: AuthService,
    user: User,
    session: Session,
    user_create_data: dict,
):
    assert session.query(User).count() == 1
    token = auth_service.authenticate(
        session, user_create_data["phone_number"], user_create_data["password"]
    )
    assert token
    assert isinstance(token, bytes)


@pytest.mark.parametrize(
    "user, user_create_data",
    [
        ("tenant", "tenant_create_data"),
        ("landlord", "landlord_create_data"),
        ("admin", "admin_create_data"),
    ],
    indirect=True,
)
def test_authenticate_user_wrong_password_fail(
    auth_service: AuthService,
    user: User,
    session: Session,
    user_create_data: dict,
):
    assert session.query(User).count() == 1
    token = auth_service.authenticate(
        session, user_create_data["email"], user_create_data["password"] + "wrong"
    )
    assert not token


@pytest.mark.parametrize(
    "user, user_create_data",
    [
        ("tenant", "tenant_create_data"),
        ("landlord", "landlord_create_data"),
        ("admin", "admin_create_data"),
    ],
    indirect=True,
)
def test_authenticate_token_ok(
    auth_service: AuthService,
    user: User,
    session: Session,
    user_create_data: dict,
):
    assert session.query(User).count() == 1
    token = auth_service.authenticate(
        session, user_create_data["email"], user_create_data["password"]
    )
    assert token
    xuser = auth_service.authenticate_token(session, token)
    assert xuser
    assert user == xuser


def test_authenticate_token_fail(
    auth_service: AuthService,
    session: Session,
):
    assert session.query(User).count() == 0
    with pytest.raises(PyJWTError):
        user = auth_service.authenticate_token(session, b"wrongtokentoken")
