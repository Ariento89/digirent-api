from digirent.app import Application
from tests.conftest import application
import pytest
from sqlalchemy.orm.session import Session
from fastapi.testclient import TestClient
from digirent.database.models import Amenity


def test_admin_create_amenity_ok(
    client: TestClient, session: Session, admin_auth_header: dict
):
    assert not session.query(Amenity).count()
    response = client.post(
        "/api/amenities/", json={"title": "hello"}, headers=admin_auth_header
    )
    assert response.status_code == 201
    assert session.query(Amenity).count()
    assert session.query(Amenity).all()[0].title == "hello"


@pytest.mark.parametrize(
    "non_admin_user, non_admin_user_auth_header",
    [
        ("tenant", "tenant_auth_header"),
        ("landlord", "landlord_auth_header"),
    ],
    indirect=True,
)
def test_non_admin_create_amenity_fail(
    non_admin_user, non_admin_user_auth_header, session: Session, client: TestClient
):
    assert not session.query(Amenity).count()
    response = client.post(
        "/api/amenities/", json={"title": "hello"}, headers=non_admin_user_auth_header
    )
    assert response.status_code == 403
    assert not session.query(Amenity).count()


@pytest.mark.parametrize(
    "user, user_auth_header",
    [
        ("tenant", "tenant_auth_header"),
        ("landlord", "landlord_auth_header"),
        ("admin", "admin_auth_header"),
    ],
    indirect=True,
)
def test_fetch_amenities(
    user,
    user_auth_header,
    session: Session,
    client: TestClient,
    application: Application,
):
    application.create_amenity(session, "pool")
    application.create_amenity(session, "barn")
    assert session.query(Amenity).count() == 2
    response = client.get("/api/amenities/", headers=user_auth_header)
    assert response.status_code == 200
    result = response.json()
    assert isinstance(result, list)
    assert len(result) == 2
