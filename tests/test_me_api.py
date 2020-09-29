from digirent.database.models import User, UserRole
import pytest
from fastapi.testclient import TestClient


@pytest.mark.parametrize(
    "user, user_auth_header",
    [
        ("tenant", "tenant_auth_header"),
        ("landlord", "landlord_auth_header"),
        ("admin", "admin_auth_header"),
    ],
    indirect=True,
)
def test_fetch_profile_ok(client: TestClient, user: User, user_auth_header: dict):
    response = client.get("/api/me/", headers=user_auth_header)
    result = response.json()
    assert response.status_code == 200
    assert "firstName" in result
    assert "lastName" in result
    assert "email" in result
    assert "id" in result
    assert "phoneNumber" in result
    assert "dob" in result


def test_fetch_profile_without_token_fail(client: TestClient):
    response = client.get(f"/api/me/")
    assert response.status_code == 401
