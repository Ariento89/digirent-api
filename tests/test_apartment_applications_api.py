from fastapi.testclient import TestClient
from sqlalchemy.orm.session import Session
from digirent.database.enums import ApartmentApplicationStatus, ContractStatus
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
    assert apartment_application.status == ApartmentApplicationStatus.NEW
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
    new_apartment_application: ApartmentApplication,
    session: Session,
    landlord_auth_header: dict,
):
    assert new_apartment_application.status == ApartmentApplicationStatus.NEW
    response = client.post(
        f"/api/applications/{new_apartment_application.id}/reject",
        headers=landlord_auth_header,
    )
    result = response.json()
    assert response.status_code == 200
    assert isinstance(result, dict)
    session.expire_all()
    rejected_apartment_application = session.query(ApartmentApplication).get(
        new_apartment_application.id
    )
    assert rejected_apartment_application.status == ApartmentApplicationStatus.REJECTED


def test_landlord_consider_tenants_application_ok(
    client: TestClient,
    new_apartment_application: ApartmentApplication,
    session: Session,
    landlord_auth_header: dict,
):
    assert new_apartment_application.status == ApartmentApplicationStatus.NEW
    response = client.post(
        f"/api/applications/{new_apartment_application.id}/consider",
        headers=landlord_auth_header,
    )
    result = response.json()
    assert response.status_code == 200
    assert isinstance(result, dict)
    session.expire_all()
    new_apartment_application = session.query(ApartmentApplication).get(
        new_apartment_application.id
    )
    assert new_apartment_application.status == ApartmentApplicationStatus.CONSIDERED


def test_another_landlord_reject_tenants_application_fail(
    client: TestClient,
    new_apartment_application: ApartmentApplication,
    session: Session,
    another_landlord_auth_header: dict,
):
    assert new_apartment_application.status == ApartmentApplicationStatus.NEW
    response = client.post(
        f"/api/applications/{new_apartment_application.id}/reject",
        headers=another_landlord_auth_header,
    )
    assert response.status_code == 404
    session.expire_all()
    new_apartment_application = session.query(ApartmentApplication).get(
        new_apartment_application.id
    )
    assert new_apartment_application.status == ApartmentApplicationStatus.NEW


def test_another_landlord_consider_tenants_application_fail(
    client: TestClient,
    new_apartment_application: ApartmentApplication,
    session: Session,
    another_landlord_auth_header: dict,
):
    assert new_apartment_application.status == ApartmentApplicationStatus.NEW
    response = client.post(
        f"/api/applications/{new_apartment_application.id}/consider",
        headers=another_landlord_auth_header,
    )
    assert response.status_code == 404
    session.expire_all()
    new_apartment_application = session.query(ApartmentApplication).get(
        new_apartment_application.id
    )
    assert new_apartment_application.status == ApartmentApplicationStatus.NEW


def test_landlord_fetch_apartment_applications(
    client: TestClient,
    apartment: Apartment,
    session: Session,
    new_apartment_application,
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
    new_apartment_application,
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


def test_process_apartment_application(
    client: TestClient,
    considered_apartment_application: ApartmentApplication,
    landlord_auth_header: dict,
    session: Session,
):
    assert not considered_apartment_application.contract
    response = client.post(
        f"/api/applications/{considered_apartment_application.id}/process",
        headers=landlord_auth_header,
    )
    assert response.status_code == 200
    session.expire_all()
    assert (
        considered_apartment_application.status == ApartmentApplicationStatus.PROCESSING
    )
    assert considered_apartment_application.contract
    assert considered_apartment_application.contract.status == ContractStatus.NEW


def test_process_another_tenants_application_when_one_is_currently_being_processed(
    client: TestClient,
    another_considered_application: ApartmentApplication,
    process_apartment_application: ApartmentApplication,
    landlord_auth_header: dict,
    session: Session,
):
    response = client.post(
        f"/api/applications/{another_considered_application.id}/process",
        headers=landlord_auth_header,
    )
    assert response.status_code == 400
    assert (
        another_considered_application.status == ApartmentApplicationStatus.CONSIDERED
    )


def test_event_handler_tenant_signed_document():
    raise Exception()


def test_event_handler_tenant_declined_document():
    raise Exception()


def test_event_handler_landlord_signed_document():
    raise Exception()


def test_event_handler_landlord_declined_document():
    raise Exception()


def test_landlord_confirm_keys_provided_to_tenant():
    raise Exception()


def test_tenant_confirm_apartment_keys_received_from_landlord():
    raise Exception()
