from datetime import datetime
import random
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
from digirent.database.models import User, UserRole
from digirent.app.container import ApplicationContainer
from digirent.database.base import SessionLocal, Base
from digirent.core.services.auth import AuthService
from digirent.core.services.user import UserService
from digirent.app import Application


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
def tenant_create_data() -> dict:
    return {
        "first_name": "Tenant",
        "last_name": "Doe",
        "email": "tenantdoe@gmail.com",
        "dob": datetime.now().date(),
        "phone_number": "0012345678",
        "password": "testpassword",
        "role": UserRole.TENANT,
    }


@pytest.fixture
def landlord_create_data() -> dict:
    return {
        "first_name": "Landlord",
        "last_name": "Doe",
        "email": "landlorddoe@gmail.com",
        "phone_number": "0012345678",
        "password": "testpassword",
        "role": UserRole.LANDLORD,
    }


@pytest.fixture
def admin_create_data() -> dict:
    return {
        "first_name": "Admin",
        "last_name": "Doe",
        "email": "admindoe@gmail.com",
        "phone_number": "0012345678",
        "password": "testpassword",
        "role": UserRole.ADMIN,
    }


@pytest.fixture
def user_service():
    return UserService()


@pytest.fixture
def auth_service():
    return AuthService(UserService())


@pytest.fixture
def tenant(
    session: Session, user_service: UserService, tenant_create_data: dict
) -> User:
    assert session.query(User).count() == 0
    result = user_service.create_user(session, **tenant_create_data)
    assert isinstance(result, User)
    assert result.role == UserRole.TENANT
    assert session.query(User).count() == 1
    return result


@pytest.fixture
def landlord(
    session: Session, user_service: UserService, landlord_create_data: dict
) -> User:
    assert session.query(User).count() == 0
    landlord_create_data["dob"] = None
    result = user_service.create_user(session, **landlord_create_data)
    assert isinstance(result, User)
    assert result.role == UserRole.LANDLORD
    assert session.query(User).count() == 1
    return result


@pytest.fixture
def admin(session: Session, user_service: UserService, admin_create_data: dict) -> User:
    assert session.query(User).count() == 0
    admin_create_data["dob"] = None
    result = user_service.create_user(session, **admin_create_data)
    assert isinstance(result, User)
    assert result.role == UserRole.ADMIN
    assert session.query(User).count() == 1
    return result


@pytest.fixture
def tenant_auth_header(client: TestClient, tenant: User, tenant_create_data: dict):
    response = client.post(
        f"/api/auth/",
        data={
            "username": tenant.email,
            "password": tenant_create_data["password"],
        },
    )
    result = response.json()
    assert response.status_code == 200
    assert "access_token" in result
    assert "token_type" in result
    return {"Authorization": f"Bearer {result['access_token']}"}


@pytest.fixture
def landlord_auth_header(
    client: TestClient, landlord: User, landlord_create_data: dict
):
    response = client.post(
        f"/api/auth/",
        data={
            "username": landlord.email,
            "password": landlord_create_data["password"],
        },
    )
    result = response.json()
    assert response.status_code == 200
    assert "access_token" in result
    assert "token_type" in result
    return {"Authorization": f"Bearer {result['access_token']}"}


@pytest.fixture
def admin_auth_header(client: TestClient, admin: User, admin_create_data: dict):
    response = client.post(
        f"/api/auth/",
        data={
            "username": admin.email,
            "password": admin_create_data["password"],
        },
    )
    result = response.json()
    assert response.status_code == 200
    assert "access_token" in result
    assert "token_type" in result
    return {"Authorization": f"Bearer {result['access_token']}"}


@pytest.fixture
def user_create_data(request):
    return request.getfixturevalue(request.param)


@pytest.fixture
def non_admin_user_create_data(request):
    return request.getfixturevalue(request.param)


@pytest.fixture
def user(request):
    return request.getfixturevalue(request.param)


@pytest.fixture
def user_auth_header(request):
    return request.getfixturevalue(request.param)


@pytest.fixture
def non_admin_user(request):
    return request.getfixturevalue(request.param)