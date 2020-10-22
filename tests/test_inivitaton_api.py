from fastapi.testclient import TestClient
from sqlalchemy.orm.session import Session
from digirent.app import Application
from digirent.database.models import (
    Apartment,
    ApartmentApplication,
    BookingRequest,
    Tenant,
)
from digirent.database.enums import ApartmentApplicationStatus, BookingRequestStatus


def test_landlord_invite_tenant_to_apply_for_apartment_ok(
    client: TestClient,
    session: Session,
    apartment: Apartment,
    tenant: Tenant,
    landlord_auth_header: dict,
):
    assert not session.query(BookingRequest).count()
    response = client.post(
        "/api/invites/",
        json={"tenantId": str(tenant.id), "apartmentId": str(apartment.id)},
        headers=landlord_auth_header,
    )
    assert response.status_code == 201
    result = response.json()
    assert "apartmentId" in result
    assert "tenantId" in result
    assert "status" in result
    assert session.query(BookingRequest).count()


def test_landlord_invite_tenant_to_apply_for_already_awarded_apartment_fail(
    client: TestClient,
    session: Session,
    awarded_apartment_application: ApartmentApplication,
    another_tenant: Tenant,
    landlord_auth_header: dict,
):
    assert awarded_apartment_application.status == ApartmentApplicationStatus.AWARDED
    assert not session.query(BookingRequest).count()
    response = client.post(
        "/api/invites/",
        json={
            "tenantId": str(another_tenant.id),
            "apartmentId": str(awarded_apartment_application.apartment_id),
        },
        headers=landlord_auth_header,
    )
    assert response.status_code == 400
    assert not session.query(BookingRequest).count()


def test_landlord_invite_tenant_to_apply_for_another_landlords_apartment_fail(
    client: TestClient,
    session: Session,
    apartment: Apartment,
    tenant: Tenant,
    another_landlord_auth_header: dict,
):
    assert not session.query(BookingRequest).count()
    response = client.post(
        "/api/invites/",
        json={"tenantId": str(tenant.id), "apartmentId": str(apartment.id)},
        headers=another_landlord_auth_header,
    )
    assert response.status_code == 404
    assert not session.query(BookingRequest).count()


def test_tenant_accept_invitation_ok(
    client: TestClient,
    session: Session,
    booking_request: BookingRequest,
    tenant_auth_header: dict,
):
    assert session.query(BookingRequest).count() == 1
    assert booking_request.status == BookingRequestStatus.PENDING
    response = client.post(
        f"/api/invites/{booking_request.id}",
        headers=tenant_auth_header,
    )
    assert response.status_code == 200
    result = response.json()
    assert "apartmentId" in result
    assert "tenantId" in result
    assert "status" in result
    assert result["status"] == BookingRequestStatus.ACCEPTED.value
    session.expire_all()
    assert booking_request.status == BookingRequestStatus.ACCEPTED


def test_tenant_reject_invitation_ok(
    client: TestClient,
    session: Session,
    booking_request: BookingRequest,
    tenant_auth_header: dict,
):
    assert session.query(BookingRequest).count() == 1
    assert booking_request.status == BookingRequestStatus.PENDING
    response = client.delete(
        f"/api/invites/{booking_request.id}",
        headers=tenant_auth_header,
    )
    assert response.status_code == 200
    result = response.json()
    assert "apartmentId" in result
    assert "tenantId" in result
    assert "status" in result
    assert result["status"] == BookingRequestStatus.REJECTED.value
    session.expire_all()
    assert booking_request.status == BookingRequestStatus.REJECTED


def test_tenant_accept_rejected_invitation_fail(
    client: TestClient,
    session: Session,
    booking_request: BookingRequest,
    application: Application,
    tenant: Tenant,
    tenant_auth_header: dict,
):
    rejected_invite = application.reject_application_invitation(
        session, tenant, booking_request
    )
    assert session.query(BookingRequest).count() == 1
    assert booking_request.status == BookingRequestStatus.REJECTED
    response = client.post(
        f"/api/invites/{rejected_invite.id}",
        headers=tenant_auth_header,
    )
    assert response.status_code == 400
    assert booking_request.status == BookingRequestStatus.REJECTED


def test_tenant_reject_accepted_invitation_fail(
    client: TestClient,
    session: Session,
    booking_request: BookingRequest,
    application: Application,
    tenant: Tenant,
    tenant_auth_header: dict,
):
    rejected_invite = application.accept_application_invitation(
        session, tenant, booking_request
    )
    assert session.query(BookingRequest).count() == 1
    assert booking_request.status == BookingRequestStatus.ACCEPTED
    response = client.delete(
        f"/api/invites/{rejected_invite.id}",
        headers=tenant_auth_header,
    )
    assert response.status_code == 400
    assert booking_request.status == BookingRequestStatus.ACCEPTED
