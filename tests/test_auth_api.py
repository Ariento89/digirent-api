import pytest
from digirent.database.models import User
from fastapi.testclient import TestClient


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
        "/api/auth/",
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
        "/api/auth/",
        data={
            "username": "wrong email",
            "password": "wrongpassword",
        },
    )
    result = response.json()
    assert response.status_code == 401
    assert "access_token" not in result
    assert "token_type" not in result
