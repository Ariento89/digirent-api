from typing import Dict, List, Any
from uuid import UUID

import pytest
import stripe
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm.session import Session
from starlette.config import environ
from pytest_mock import MockFixture

environ["APP_ENV"] = "test"

from digirent.core.config import DATABASE_URL

from digirent.web_app import get_app
from digirent.api.user.schema import UserCreateSchema, UserSchema
from digirent.api.me.schema import ProfileSchema
from digirent.api.auth.schema import TokenSchema
from digirent.database.models import User, UserRole
from digirent.app.container import ServiceContainer, ApplicationContainer
from digirent.database.base import SessionLocal, Base
from digirent.core.services.auth import AuthService
from digirent.core.services.user import UserService
from digirent.app import Application
from digirent.script import create_admin_user


@pytest.fixture(autouse=True)
def create_test_database():
    metadata: MetaData = Base.metadata
    url = str(DATABASE_URL)
    engine = create_engine(url)
    metadata.create_all(engine)
    yield  # Run the tests.
    metadata.drop_all(engine)


@pytest.fixture
def app() -> FastAPI:
    return get_app()


@pytest.fixture
def application() -> Application:
    return ApplicationContainer.app()


@pytest.fixture
def client(app) -> TestClient:
    return TestClient(app)


@pytest.fixture
def session() -> Session:
    session: Session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def new_user_data() -> dict:
    return {
        "first_name": "John",
        "last_name": "Doe",
        "email": "johndoe@gmail.com",
        "username": "johndoe",
        "phone_number": "0012345678",
        "password": "testpassword",
    }


@pytest.fixture
def user_service():
    return UserService()


@pytest.fixture
def auth_service():
    return AuthService(UserService())


@pytest.fixture
def existing_user(
    session: Session, user_service: UserService, new_user_data: dict
) -> User:
    assert session.query(User).count() == 0
    result = user_service.create_user(session, **new_user_data)
    assert isinstance(result, User)
    assert session.query(User).count() == 1
    return result


@pytest.fixture
def user_auth_header(client: TestClient, existing_user: User, new_user_data: dict):
    response = client.post(
        f"/api/auth/",
        data={
            "username": existing_user.email,
            "password": new_user_data["password"],
        },
    )
    result = response.json()
    assert response.status_code == 200
    assert "access_token" in result
    assert "token_type" in result
    return {"Authorization": f"Bearer {result['access_token']}"}
