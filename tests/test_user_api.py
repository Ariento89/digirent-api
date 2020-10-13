import pytest
from digirent.database.models import Landlord, Tenant, User, UserRole
from fastapi.testclient import TestClient
from sqlalchemy.orm.session import Session


def test_create_tenant_ok(
    client: TestClient, tenant_create_data: dict, session: Session
):
    create_data = {
        "firstName": tenant_create_data["first_name"],
        "lastName": tenant_create_data["last_name"],
        "email": tenant_create_data["email"],
        "dob": str(tenant_create_data["dob"]),
        "phoneNumber": tenant_create_data["phone_number"],
        "password": tenant_create_data["password"],
    }
    assert session.query(User).count() == 0
    response = client.post("/api/users/tenant", json=create_data)
    result = response.json()
    assert response.status_code == 200
    assert session.query(User).count() == 1
    assert "firstName" in result
    assert "lastName" in result
    assert "email" in result
    assert "dob" in result
    assert "id" in result
    assert "phoneNumber" in result
    assert "role" in result
    assert result["role"] == UserRole.TENANT.value


def test_create_landlord_ok(
    client: TestClient, landlord_create_data: dict, session: Session
):
    assert session.query(User).count() == 0
    del landlord_create_data["role"]
    assert "role" not in landlord_create_data
    response = client.post("/api/users/landlord", json=landlord_create_data)
    result = response.json()
    assert response.status_code == 200
    assert session.query(User).count() == 1
    assert "firstName" in result
    assert "lastName" in result
    assert "email" in result
    assert "dob" in result
    assert "id" in result
    assert "phoneNumber" in result
    assert "role" in result
    assert result["role"] == UserRole.LANDLORD.value


def test_admin_get_users_ok(
    client: TestClient,
    tenant: Tenant,
    landlord: Landlord,
    admin_auth_header: dict,
    session: Session,
):
    assert session.query(User).count() == 3
    response = client.get("/api/users/", headers=admin_auth_header)
    result = response.json()
    assert response.status_code == 200
    assert isinstance(result, list)
    assert len(result) == 3


@pytest.mark.parametrize(
    "non_admin_user_auth_header",
    [
        "tenant_auth_header",
        "landlord_auth_header",
    ],
    indirect=True,
)
def test_non_admin_get_users_fail(
    non_admin_user_auth_header,
    client: TestClient,
    admin,
    landlord,
    tenant,
    session: Session,
):
    assert session.query(User).count() == 3
    response = client.get("/api/users/", headers=non_admin_user_auth_header)
    assert response.status_code == 403
