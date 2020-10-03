import digirent.util as util
from sqlalchemy.orm.session import Session
from digirent.database.enums import Gender, HouseType
from digirent.database.models import Landlord, Tenant, User, UserRole
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
    assert "description" in result
    assert "city" in result
    assert "gender" in result


def test_fetch_profile_without_token_fail(client: TestClient):
    response = client.get(f"/api/me/")
    assert response.status_code == 401


@pytest.mark.parametrize(
    "user, user_auth_header",
    [
        ("tenant", "tenant_auth_header"),
        ("landlord", "landlord_auth_header"),
        ("admin", "admin_auth_header"),
    ],
    indirect=True,
)
def test_update_user_profile_information(
    client: TestClient, user: User, user_auth_header: dict, session: Session
):
    new_user_first_name = "some name"
    new_user_last_name = "some last name"
    new_gender = Gender.FEMALE
    assert user.first_name != new_user_first_name
    assert user.last_name != new_user_last_name
    response = client.put(
        "/api/me/",
        headers=user_auth_header,
        json={
            "firstName": new_user_first_name,
            "lastName": new_user_last_name,
            "email": user.email,
            "phoneNumber": user.phone_number,
            "dob": str(user.dob) if user.dob else None,
            "city": user.city,
            "gender": new_gender,
        },
    )
    session.expire_all()
    xuser = session.query(User).get(user.id)
    assert response.status_code == 200
    assert xuser.first_name == new_user_first_name
    assert xuser.last_name == new_user_last_name


@pytest.mark.parametrize(
    "user, user_auth_header",
    [
        ("tenant", "tenant_auth_header"),
        ("landlord", "landlord_auth_header"),
        ("admin", "admin_auth_header"),
    ],
    indirect=True,
)
def test_update_user_profile_description(
    client: TestClient, user: User, session: Session, user_auth_header: dict
):
    new_description = "some description"
    assert user.description != new_description
    response = client.put(
        "/api/me/",
        headers=user_auth_header,
        json={
            "description": new_description,
            "firstName": user.first_name,
            "lastName": user.last_name,
            "email": user.email,
            "phone_number": user.phone_number,
        },
    )
    session.expire_all()
    xuser = session.query(User).get(user.id)
    assert response.status_code == 200
    assert xuser.description == new_description


def test_update_set_tenant_lookingfor(
    client: TestClient, session: Session, tenant: Tenant, tenant_auth_header: dict
):
    assert not tenant.looking_for
    response = client.post(
        "/api/me/looking-for",
        headers=tenant_auth_header,
        json={
            "houseType": HouseType.BUNGALOW.value,
            "city": "Some City",
            "maxBudget": 34.50,
        },
    )
    assert response.status_code == 200
    session.expire_all()
    assert tenant.looking_for
    assert tenant.looking_for.house_type == HouseType.BUNGALOW
    assert tenant.looking_for.city == "Some City"
    assert tenant.looking_for.max_budget == 34.5


def test_update_set_landlord_lookingfor_fail(
    client: TestClient, session: Session, landlord: Landlord, landlord_auth_header: dict
):
    response = client.post(
        "/api/me/looking-for",
        headers=landlord_auth_header,
        json={
            "houseType": HouseType.BUNGALOW.value,
            "city": "Some City",
            "maxBudget": 34.50,
        },
    )
    assert response.status_code == 403


@pytest.mark.parametrize(
    "user, user_auth_header",
    [
        ("tenant", "tenant_auth_header"),
        ("landlord", "landlord_auth_header"),
        ("admin", "admin_auth_header"),
    ],
    indirect=True,
)
def test_set_user_bank_details(
    client: TestClient, session: Session, user: User, user_auth_header: dict
):
    assert not user.bank_detail
    response = client.post(
        "/api/me/bank",
        headers=user_auth_header,
        json={
            "accountName": "Test Account Name",
            "accountNumber": "000000013423",
        },
    )
    assert response.status_code == 200
    session.expire_all()
    assert user.bank_detail
    assert user.bank_detail.account_name == "Test Account Name"
    assert user.bank_detail.account_number == "000000013423"


@pytest.mark.parametrize(
    "user, user_auth_header, user_create_data",
    [
        ("tenant", "tenant_auth_header", "tenant_create_data"),
        ("landlord", "landlord_auth_header", "landlord_create_data"),
        ("admin", "admin_auth_header", "admin_create_data"),
    ],
    indirect=True,
)
def test_update_user_password(
    client: TestClient,
    user: User,
    session: Session,
    user_auth_header: dict,
    user_create_data: dict,
):
    old_password = user_create_data["password"]
    new_password = "newpass"
    assert util.password_is_match(old_password, user.hashed_password)
    assert not util.password_is_match(new_password, user.hashed_password)
    response = client.put(
        "/api/me/password",
        headers=user_auth_header,
        json={
            "oldPassword": old_password,
            "newPassword": new_password,
        },
    )
    assert response.status_code == 200
    session.expire_all()
    assert not util.password_is_match(old_password, user.hashed_password)
    assert util.password_is_match(new_password, user.hashed_password)
