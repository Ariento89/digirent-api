from fastapi.testclient import TestClient
from sqlalchemy.orm.session import Session
from digirent.database.models import Tenant, Apartment, Landlord, ApartmentApplication


def test_tenant_apply_for_apartment_ok(
    client: TestClient,
    session: Session,
    tenant: Tenant,
    apartment: Apartment,
    tenant_auth_header: dict,
):
    assert not session.query(ApartmentApplication).count()
    response = client.post(
        f"/api/applications/{apartment.id}", headers=tenant_auth_header
    )
    result = response.json()
    assert response.status_code == 201
    assert isinstance(result, dict)
    assert "tenantId" in result
    assert "apartmentId" in result
    assert "id" in result
    assert result["tenantId"] == str(tenant.id)
    assert result["apartmentId"] == str(apartment.id)
    assert session.query(ApartmentApplication).count()
    apartment_application = session.query(ApartmentApplication).get(result["id"])
    assert apartment_application
    assert apartment_application.tenant == tenant
    assert apartment_application.apartment == apartment


def test_landlord_apply_for_apartment_fail(
    client: TestClient,
    session: Session,
    landlord: Landlord,
    apartment: Apartment,
    landlord_auth_header: dict,
):
    assert not session.query(ApartmentApplication).count()
    response = client.post(
        f"/api/applications/{apartment.id}", headers=landlord_auth_header
    )
    assert response.status_code == 403
    assert not session.query(ApartmentApplication).count()
