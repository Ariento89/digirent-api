from digirent.database.models import User
import pytest
from uuid import UUID
from fastapi.testclient import TestClient
from digirent.api.me.schema import ProfileSchema
from digirent.api.auth.schema import TokenSchema
from pytest_mock import MockFixture
from digirent.app import Application
from digirent.app.error import ApplicationError
from sqlalchemy.orm.session import Session


@pytest.mark.parametrize(
    "user, user_create_data",
    [
        ("tenant", "tenant_create_data"),
        ("landlord", "landlord_create_data"),
        ("admin", "admin_create_data"),
    ],
    indirect=True,
)
def test_tenant_auth_ok(client: TestClient, user: User, user_create_data: dict):
    response = client.post(
        f"/api/auth/",
        data={
            "username": user.email,
            "password": user_create_data["password"],
        },
    )
    result = response.json()
    assert response.status_code == 200
    assert "access_token" in result
    assert "token_type" in result


def test_user_auth_fail(client: TestClient):
    response = client.post(
        f"/api/auth/",
        data={
            "username": "wrong email",
            "password": "wrongpassword",
        },
    )
    result = response.json()
    assert response.status_code == 401
    assert "access_token" not in result
    assert "token_type" not in result
