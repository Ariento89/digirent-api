from digirent.app.error import ApplicationError
from tests.conftest import application, existing_user, new_user_data
import pytest
from digirent.app import Application
from sqlalchemy.orm.session import Session
from digirent.database.models import User


def testt_create_user(application: Application, session: Session, new_user_data: dict):
    assert not session.query(User).count()
    user = application.create_user(session, **new_user_data)
    assert user
    assert session.query(User).count() == 1


def testt_create_user_fail(
    application: Application, session: Session, new_user_data: dict
):
    assert not session.query(User).count()
    user = application.create_user(session, **new_user_data)
    assert user
    assert session.query(User).count() == 1
    with pytest.raises(ApplicationError):
        application.create_user(session, **new_user_data)
    assert session.query(User).count() == 1


def test_authenticate_user_ok(
    existing_user: User, application: Application, new_user_data: dict, session: Session
):
    token = application.authenticate_user(
        session, existing_user.username, new_user_data["password"]
    )
    assert token
    assert isinstance(token, bytes)


def test_authenticate_user_fail(
    existing_user: User, application: Application, new_user_data: dict, session: Session
):
    with pytest.raises(ApplicationError):
        application.authenticate_user(session, existing_user.username, "wrongpassword")


def test_authenticate_token_ok(
    existing_user: User, application: Application, new_user_data: dict, session: Session
):
    token = application.authenticate_user(
        session, existing_user.username, new_user_data["password"]
    )
    user: User = application.authenticate_token(session, token)
    assert user == existing_user


def test_authenticate_token_fail(
    existing_user: User, application: Application, new_user_data: dict, session: Session
):
    with pytest.raises(ApplicationError):
        application.authenticate_token(session, b"wrongtoken")
