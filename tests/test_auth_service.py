from jwt import PyJWTError
import pytest
from sqlalchemy.orm.session import Session
from digirent.core.services.user import UserService
from digirent.core.services.auth import AuthService
from digirent.database.models import User


def test_authenticate_user_by_email_ok(
    auth_service: AuthService,
    existing_user: User,
    session: Session,
    new_user_data: dict,
):
    assert session.query(User).count() == 1
    token = auth_service.authenticate(
        session, new_user_data["email"], new_user_data["password"]
    )
    assert token
    assert isinstance(token, bytes)


def test_authenticate_user_by_username_ok(
    auth_service: AuthService,
    existing_user: User,
    session: Session,
    new_user_data: dict,
):
    assert session.query(User).count() == 1
    token = auth_service.authenticate(
        session, new_user_data["username"], new_user_data["password"]
    )
    assert token
    assert isinstance(token, bytes)


def test_authenticate_user_by_phonenumber_ok(
    auth_service: AuthService,
    existing_user: User,
    session: Session,
    new_user_data: dict,
):
    assert session.query(User).count() == 1
    token = auth_service.authenticate(
        session, new_user_data["phone_number"], new_user_data["password"]
    )
    assert token
    assert isinstance(token, bytes)


def test_authenticate_user_wrong_password_fail(
    auth_service: AuthService,
    existing_user: User,
    session: Session,
    new_user_data: dict,
):
    assert session.query(User).count() == 1
    token = auth_service.authenticate(
        session, new_user_data["email"], new_user_data["password"] + "wrong"
    )
    assert not token


def test_authenticate_token_ok(
    auth_service: AuthService,
    existing_user: User,
    session: Session,
    new_user_data: dict,
):
    assert session.query(User).count() == 1
    token = auth_service.authenticate(
        session, new_user_data["email"], new_user_data["password"]
    )
    assert token
    user = auth_service.authenticate_token(session, token)
    assert user
    assert user == existing_user


def test_authenticate_token_fail(
    auth_service: AuthService,
    existing_user: User,
    session: Session,
    new_user_data: dict,
):
    assert session.query(User).count() == 1
    with pytest.raises(PyJWTError):
        user = auth_service.authenticate_token(session, b"wrongtokentoken")
