from digirent.app import Application
from digirent.database.enums import HouseType, UserRole
from tests.conftest import application
import pytest
from sqlalchemy.orm.session import Session
from fastapi.testclient import TestClient
from digirent.database.models import Admin, Amenity, Apartment, Landlord
from datetime import datetime


apartment_create_data = dict(
    name="Apartment Name",
    monthlyPrice=450.70,
    utilitiesPrice=320.15,
    address="some address",
    country="Nigeria",
    state="Kano",
    city="Kano",
    description="Apartment description",
    houseType=HouseType.DUPLEX,
    bedrooms=3,
    bathrooms=4,
    size=1200,
    furnishType="furnish type",
    availableFrom=str(datetime.now().date()),
    availableTo=str(datetime.now().date()),
    amenities=[],
)


def test_landlord_create_apartments_ok(
    client: TestClient,
    session: Session,
    landlord_auth_header: dict,
    application: Application,
):
    application.create_amenity(session, "first")
    application.create_amenity(session, "second")
    create_data = {**apartment_create_data, "amenities": ["first", "second"]}
    assert not session.query(Apartment).count()
    response = client.post(
        "/api/apartments/", json=create_data, headers=landlord_auth_header
    )
    assert response.status_code == 201
    assert session.query(Apartment).count() == 1


def test_landlord_update_apartments_ok(
    client: TestClient,
    session: Session,
    landlord_auth_header: dict,
    application: Application,
):
    application.create_amenity(session, "first")
    application.create_amenity(session, "second")
    assert not session.query(Apartment).count()
    response = client.post(
        "/api/apartments/", json=apartment_create_data, headers=landlord_auth_header
    )
    assert response.status_code == 201
    assert session.query(Apartment).count() == 1
    apartment = session.query(Apartment).all()[0]
    assert apartment.name != "updated name"
    assert apartment.amenities == []
    response = client.put(
        f"/api/apartments/{apartment.id}",
        json={"name": "updated name", "amenities": ["first", "second"]},
        headers=landlord_auth_header,
    )
    assert response.status_code == 200
    session.expire_all()
    assert session.query(Apartment).count() == 1
    apartment = session.query(Apartment).all()[0]
    assert apartment.name == "updated name"
    assert len(apartment.amenities) == 2


def test_landlord_update_not_owned_apartment_fail(
    client: TestClient,
    session: Session,
    landlord_auth_header: dict,
    application: Application,
):
    data = {
        "first_name": "Another",
        "last_name": "Landlord",
        "email": "anodae@gmail.com",
        "phone_number": "00023456788",
        "dob": None,
        "hashed_password": "testpassword",
    }
    apartment_create_data = dict(
        name="Apartment Name",
        monthly_price=450.70,
        utilities_price=320.15,
        address="some address",
        country="Nigeria",
        state="Kano",
        city="Kano",
        description="Apartment description",
        house_type=HouseType.DUPLEX,
        bedrooms=3,
        bathrooms=4,
        size=1200,
        furnish_type="furnish type",
        available_from=datetime.now().date(),
        available_to=datetime.now().date(),
        amenities=[],
    )
    new_landlord = Landlord(**data)
    session.add(new_landlord)
    session.commit()
    assert len(application.landlord_service.all(session)) == 2
    application.create_apartment(session, new_landlord, **apartment_create_data)
    new_apartment = session.query(Apartment).all()[0]
    assert len(application.apartment_service.all(session)) == 1
    response = client.put(
        f"/api/apartments/{new_apartment.id}",
        json={"name": "updated name"},
        headers=landlord_auth_header,
    )
    assert response.status_code == 400


def test_tenant_create_apartments_fail(
    client: TestClient,
    session: Session,
    tenant_auth_header: dict,
    application: Application,
):
    application.create_amenity(session, "first")
    application.create_amenity(session, "second")
    create_data = {**apartment_create_data, "amenities": ["first", "second"]}
    assert not session.query(Apartment).count()
    response = client.post(
        "/api/apartments/", json=create_data, headers=tenant_auth_header
    )
    assert response.status_code == 403


def test_tenant_update_apartment_fail(
    client: TestClient,
    session: Session,
    landlord_auth_header: dict,
    tenant_auth_header: dict,
    application: Application,
):
    application.create_amenity(session, "first")
    application.create_amenity(session, "second")
    assert not session.query(Apartment).count()
    response = client.post(
        "/api/apartments/", json=apartment_create_data, headers=landlord_auth_header
    )
    assert response.status_code == 201
    assert session.query(Apartment).count() == 1
    apartment = session.query(Apartment).all()[0]
    assert apartment.name != "updated name"
    assert apartment.amenities == []
    response = client.put(
        f"/api/apartments/{apartment.id}",
        json={"name": "updated name", "amenities": ["first", "second"]},
        headers=tenant_auth_header,
    )
    assert response.status_code == 403
