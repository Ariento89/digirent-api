from fastapi.testclient import TestClient
from sqlalchemy.orm.session import Session
from digirent.database.enums import ApartmentApplicationStatus
from digirent.database.models import Landlord, Tenant, Apartment, ApartmentApplication


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
    apartment: Apartment,
    landlord_auth_header: dict,
):
    assert not session.query(ApartmentApplication).count()
    response = client.post(
        f"/api/applications/{apartment.id}", headers=landlord_auth_header
    )
    assert response.status_code == 403
    assert not session.query(ApartmentApplication).count()


def test_landlord_reject_tenants_application_ok(
    client: TestClient,
    apartment_application: ApartmentApplication,
    session: Session,
    landlord_auth_header: dict,
):
    assert apartment_application.status == ApartmentApplicationStatus.NEW
    response = client.post(
        f"/api/applications/{apartment_application.id}/reject",
        headers=landlord_auth_header,
    )
    result = response.json()
    assert response.status_code == 200
    assert isinstance(result, dict)
    session.expire_all()
    apartment_application = session.query(ApartmentApplication).get(
        apartment_application.id
    )
    assert apartment_application.status == ApartmentApplicationStatus.REJECTED


def test_landlord_consider_tenants_application_ok(
    client: TestClient,
    apartment_application: ApartmentApplication,
    session: Session,
    landlord_auth_header: dict,
):
    assert apartment_application.status == ApartmentApplicationStatus.NEW
    response = client.post(
        f"/api/applications/{apartment_application.id}/consider",
        headers=landlord_auth_header,
    )
    result = response.json()
    assert response.status_code == 200
    assert isinstance(result, dict)
    session.expire_all()
    apartment_application = session.query(ApartmentApplication).get(
        apartment_application.id
    )
    assert apartment_application.status == ApartmentApplicationStatus.CONSIDERED


def test_another_landlord_reject_tenants_application_fail(
    client: TestClient,
    apartment_application: ApartmentApplication,
    session: Session,
    another_landlord_auth_header: dict,
):
    assert apartment_application.status == ApartmentApplicationStatus.NEW
    response = client.post(
        f"/api/applications/{apartment_application.id}/reject",
        headers=another_landlord_auth_header,
    )
    assert response.status_code == 404
    session.expire_all()
    apartment_application = session.query(ApartmentApplication).get(
        apartment_application.id
    )
    assert apartment_application.status == ApartmentApplicationStatus.NEW


def test_another_landlord_consider_tenants_application_fail(
    client: TestClient,
    apartment_application: ApartmentApplication,
    session: Session,
    another_landlord_auth_header: dict,
):
    assert apartment_application.status == ApartmentApplicationStatus.NEW
    response = client.post(
        f"/api/applications/{apartment_application.id}/consider",
        headers=another_landlord_auth_header,
    )
    assert response.status_code == 404
    session.expire_all()
    apartment_application = session.query(ApartmentApplication).get(
        apartment_application.id
    )
    assert apartment_application.status == ApartmentApplicationStatus.NEW


def test_accept_considered_application_ok(
    client: TestClient,
    considered_apartment_application: ApartmentApplication,
    landlord_auth_header: dict,
):
    assert (
        considered_apartment_application.status == ApartmentApplicationStatus.CONSIDERED
    )
    response = client.post(
        f"/api/applications/{considered_apartment_application.id}/accept",
        headers=landlord_auth_header,
    )
    assert response.status_code == 200
    result = response.json()
    assert "id" in result
    assert "status" in result
    assert result["status"] == ApartmentApplicationStatus.AWARDED.value


def test_accept_rejected_application_fail(
    client: TestClient,
    rejected_apartment_application: ApartmentApplication,
    landlord_auth_header: dict,
):
    assert rejected_apartment_application.stage == ApartmentApplicationStatus.REJECTED
    response = client.post(
        f"/api/applications/{rejected_apartment_application.id}/accept",
        headers=landlord_auth_header,
    )
    assert response.status_code == 400
    result = response.json()
    assert "application has not yet been considered" in result["detail"].lower()


def test_accept_another_application_when_apartment_has_been_awarded(
    client: TestClient,
    another_considered_application: ApartmentApplication,
    awarded_apartment_application: ApartmentApplication,
    landlord_auth_header: dict,
):
    assert awarded_apartment_application.stage == ApartmentApplicationStatus.AWARDED
    assert another_considered_application.stage == ApartmentApplicationStatus.REJECTED
    response = client.post(
        f"/api/applications/{another_considered_application.id}/accept",
        headers=landlord_auth_header,
    )
    assert response.status_code == 400
    result = response.json()
    assert "has not yet been considered" in result["detail"].lower()


def test_landlord_fetch_apartment_applications(
    client: TestClient,
    apartment: Apartment,
    session: Session,
    apartment_application,
    landlord: Landlord,
    landlord_auth_header,
):
    assert (
        session.query(ApartmentApplication)
        .join(Apartment)
        .filter(ApartmentApplication.apartment_id == apartment.id)
        .filter(Apartment.landlord_id == landlord.id)
        .count()
    )
    response = client.get(
        f"/api/applications/{apartment.id}", headers=landlord_auth_header
    )
    assert response.status_code == 200
    result = response.json()
    assert isinstance(result, list)
    assert len(result) == 1


def test_tenant_fetch_applications(
    client: TestClient,
    apartment: Apartment,
    session: Session,
    apartment_application,
    landlord: Landlord,
    tenant_auth_header,
):
    assert (
        session.query(ApartmentApplication)
        .join(Apartment)
        .filter(ApartmentApplication.apartment_id == apartment.id)
        .filter(Apartment.landlord_id == landlord.id)
        .count()
    )
    response = client.get("/api/applications/", headers=tenant_auth_header)
    assert response.status_code == 200
    result = response.json()
    assert isinstance(result, list)
    assert len(result) == 1
