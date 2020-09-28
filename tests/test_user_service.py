from tests.conftest import new_user_data
import pytest
from sqlalchemy.orm.session import Session
from digirent.core.services.user import UserService
from digirent.database.models import User


def test_hash_password(user_service: UserService):
    password = "testpass"
    hashed_password = user_service.hash_password(password)
    assert password != hashed_password


def test_password_is_match(user_service: UserService):
    password = "testpass"
    hashed_password = user_service.hash_password(password)
    assert not user_service.password_is_match("wrong", hashed_password)
    assert user_service.password_is_match(password, hashed_password)


def test_create_user_with_existing_email_fail(
    existing_user: User,
    session: Session,
    user_service: UserService,
    new_user_data: dict,
):
    assert session.query(User).count() == 1
    new_dict = {}
    for key, val in new_user_data.items():
        if key != "email":
            new_dict[key] = new_user_data[key] + "xyz"
        else:
            new_dict[key] = new_user_data[key]
    result = user_service.create_user(session, **new_dict)
    assert isinstance(result, str)
    assert "email" in result.lower()


def test_create_user_with_existing_username_fail(
    existing_user: User,
    session: Session,
    user_service: UserService,
    new_user_data: dict,
):
    assert session.query(User).count() == 1
    new_dict = {}
    for key, val in new_user_data.items():
        if key != "username":
            new_dict[key] = new_user_data[key] + "xyz"
        else:
            new_dict[key] = new_user_data[key]
    result = user_service.create_user(session, **new_dict)
    assert isinstance(result, str)
    assert "username" in result.lower()


def test_create_user_with_existing_phonenumber_fail(
    existing_user: User,
    session: Session,
    user_service: UserService,
    new_user_data: dict,
):
    assert session.query(User).count() == 1
    new_dict = {}
    for key, val in new_user_data.items():
        if key != "phone_number":
            new_dict[key] = new_user_data[key] + "xyz"
        else:
            new_dict[key] = new_user_data[key]
    result = user_service.create_user(session, **new_dict)
    assert isinstance(result, str)
    assert "phone number" in result.lower()


def test_get_user_by_id(
    existing_user: User, session: Session, user_service: UserService
):
    assert session.query(User).count() == 1
    user = user_service.get_user_by_id(session, existing_user.id)
    assert user is not None
    assert existing_user == user


def test_get_user_by_email(
    existing_user: User, session: Session, user_service: UserService
):
    assert session.query(User).count() == 1
    user = user_service.get_user_by_email(session, existing_user.email)
    assert user is not None
    assert existing_user == user


def test_get_user_by_username(
    existing_user: User, session: Session, user_service: UserService
):
    assert session.query(User).count() == 1
    user = user_service.get_user_by_username(session, existing_user.username)
    assert user is not None
    assert existing_user == user


def test_get_user_by_phonenumber(
    existing_user: User, session: Session, user_service: UserService
):
    assert session.query(User).count() == 1
    user = user_service.get_user_by_phone_number(session, existing_user.phone_number)
    assert user is not None
    assert existing_user == user