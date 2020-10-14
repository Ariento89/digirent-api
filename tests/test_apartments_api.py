import pytest
from pathlib import Path
from digirent.app import Application
from digirent.core.services.file_service import FileService
from digirent.database.enums import FurnishType, HouseType
from sqlalchemy.orm.session import Session
from fastapi.testclient import TestClient
from digirent.database.models import Apartment, Landlord, Tenant
from datetime import datetime
from digirent.core.config import UPLOAD_PATH

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
    furnishType=FurnishType.FURNISHED,
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
    result = response.json()
    expected_keys = [*apartment_create_data.keys(), "id", "amenityTitles", "totalPrice"]
    expected_keys.remove("amenities")
    assert all(key in result for key in expected_keys)
    assert isinstance(result, dict)
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
    result = response.json()
    expected_keys = [*apartment_create_data.keys(), "id", "amenityTitles", "totalPrice"]
    expected_keys.remove("amenities")
    assert all(key in result for key in expected_keys)
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
        furnish_type=FurnishType.FURNISHED,
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


def test_landlord_upload_apartment_image_ok(
    landlord_auth_header: dict,
    landlord: Landlord,
    file_service: FileService,
    client: TestClient,
    apartment: Apartment,
    file,
):
    filename = "image1.jpg"
    image_folder_path = (
        Path(UPLOAD_PATH) / f"apartments/{landlord.id}/{apartment.id}/images"
    )
    assert len(file_service.list_files(image_folder_path)) == 0
    file_path = image_folder_path / filename
    assert not file_path.exists()
    response = client.post(
        f"/api/apartments/{apartment.id}/images",
        files={"image": (filename, file, "image/jpeg")},
        headers=landlord_auth_header,
    )
    result = response.json()
    expected_keys = [*apartment_create_data.keys(), "id", "amenityTitles"]
    expected_keys.remove("amenities")
    assert all(key in result for key in expected_keys)
    assert response.status_code == 200
    assert len(file_service.list_files(image_folder_path)) == 1
    assert file_path.exists()


def test_landlord_upload_apartment_video_ok(
    landlord_auth_header: dict,
    landlord: Landlord,
    file_service: FileService,
    client: TestClient,
    apartment: Apartment,
    file,
):
    filename = "video1.mp4"
    video_folder_path = (
        Path(UPLOAD_PATH) / f"apartments/{landlord.id}/{apartment.id}/videos"
    )
    assert len(file_service.list_files(video_folder_path)) == 0
    file_path = video_folder_path / filename
    assert not file_path.exists()
    response = client.post(
        f"/api/apartments/{apartment.id}/videos",
        files={"video": (filename, file, "video/jpeg")},
        headers=landlord_auth_header,
    )
    result = response.json()
    expected_keys = [*apartment_create_data.keys(), "id", "amenityTitles"]
    expected_keys.remove("amenities")
    assert all(key in result for key in expected_keys)
    assert response.status_code == 200
    assert len(file_service.list_files(video_folder_path)) == 1
    assert file_path.exists()


def test_tenant_upload_apartment_image_fail(
    tenant_auth_header: dict,
    tenant: Tenant,
    file_service: FileService,
    client: TestClient,
    apartment: Apartment,
    file,
):
    filename = "image1.mp4"
    image_folder_path = (
        Path(UPLOAD_PATH) / f"apartments/{tenant.id}/{apartment.id}/images"
    )
    assert len(file_service.list_files(image_folder_path)) == 0
    file_path = image_folder_path / filename
    assert not file_path.exists()
    response = client.post(
        f"/api/apartments/{apartment.id}/images",
        files={"image": (filename, file, "image/jpeg")},
        headers=tenant_auth_header,
    )
    assert response.status_code == 403
    assert len(file_service.list_files(image_folder_path)) == 0
    assert not file_path.exists()


def test_tenant_upload_apartment_video_fail(
    tenant_auth_header: dict,
    tenant: Tenant,
    file_service: FileService,
    client: TestClient,
    apartment: Apartment,
    file,
):
    filename = "video1.mp4"
    video_folder_path = (
        Path(UPLOAD_PATH) / f"apartments/{tenant.id}/{apartment.id}/videos"
    )
    assert len(file_service.list_files(video_folder_path)) == 0
    file_path = video_folder_path / filename
    assert not file_path.exists()
    response = client.post(
        f"/api/apartments/{apartment.id}/videos",
        files={"video": (filename, file, "video/jpeg")},
        headers=tenant_auth_header,
    )
    assert response.status_code == 403
    assert len(file_service.list_files(video_folder_path)) == 0
    assert not file_path.exists()


def test_landlord_upload_wrong_image_file_type_fail(
    landlord_auth_header: dict,
    landlord: Landlord,
    file_service: FileService,
    client: TestClient,
    apartment: Apartment,
    file,
):
    filename = "image1.unsupported"
    image_folder_path = (
        Path(UPLOAD_PATH) / f"apartments/{landlord.id}/{apartment.id}/images"
    )
    assert len(file_service.list_files(image_folder_path)) == 0
    file_path = image_folder_path / filename
    assert not file_path.exists()
    response = client.post(
        f"/api/apartments/{apartment.id}/images",
        files={"image": (filename, file, "image/jpeg")},
        headers=landlord_auth_header,
    )
    assert response.status_code == 400
    assert len(file_service.list_files(image_folder_path)) == 0
    assert not file_path.exists()


def test_landlord_upload_wrong_video_file_type_fail(
    landlord_auth_header: dict,
    landlord: Landlord,
    file_service: FileService,
    client: TestClient,
    apartment: Apartment,
    file,
):
    filename = "video1.unsupported"
    video_folder_path = (
        Path(UPLOAD_PATH) / f"apartments/{landlord.id}/{apartment.id}/videos"
    )
    assert len(file_service.list_files(video_folder_path)) == 0
    file_path = video_folder_path / filename
    assert not file_path.exists()
    response = client.post(
        f"/api/apartments/{apartment.id}/videos",
        files={"video": (filename, file, "video/jpeg")},
        headers=landlord_auth_header,
    )
    assert response.status_code == 400
    assert len(file_service.list_files(video_folder_path)) == 0
    assert not file_path.exists()


def test_create_apartment_with_negative_monthly_price_fail(
    client: TestClient,
    session: Session,
    landlord_auth_header: dict,
    application: Application,
):
    application.create_amenity(session, "first")
    application.create_amenity(session, "second")
    create_data = {
        **apartment_create_data,
        "monthlyPrice": -30,
        "amenities": ["first", "second"],
    }
    assert not session.query(Apartment).count()
    response = client.post(
        "/api/apartments/", json=create_data, headers=landlord_auth_header
    )
    assert response.status_code == 422


def test_create_apartment_with_negative_utility_price_fail(
    client: TestClient,
    session: Session,
    landlord_auth_header: dict,
    application: Application,
):
    application.create_amenity(session, "first")
    application.create_amenity(session, "second")
    create_data = {
        **apartment_create_data,
        "utilitiesPrice": 0,
        "amenities": ["first", "second"],
    }
    assert not session.query(Apartment).count()
    response = client.post(
        "/api/apartments/", json=create_data, headers=landlord_auth_header
    )
    assert response.status_code == 422


def test_create_apartment_with_negative_bedrooms_fail(
    client: TestClient,
    session: Session,
    landlord_auth_header: dict,
    application: Application,
):
    application.create_amenity(session, "first")
    application.create_amenity(session, "second")
    create_data = {
        **apartment_create_data,
        "bedrooms": -3,
        "amenities": ["first", "second"],
    }
    assert not session.query(Apartment).count()
    response = client.post(
        "/api/apartments/", json=create_data, headers=landlord_auth_header
    )
    assert response.status_code == 422


def test_create_apartment_with_negative_bathrooms_fail(
    client: TestClient,
    session: Session,
    landlord_auth_header: dict,
    application: Application,
):
    application.create_amenity(session, "first")
    application.create_amenity(session, "second")
    create_data = {
        **apartment_create_data,
        "bathrooms": -1,
        "amenities": ["first", "second"],
    }
    assert not session.query(Apartment).count()
    response = client.post(
        "/api/apartments/", json=create_data, headers=landlord_auth_header
    )
    assert response.status_code == 422


def test_create_apartment_with_negative_size_fail(
    client: TestClient,
    session: Session,
    landlord_auth_header: dict,
    application: Application,
):
    application.create_amenity(session, "first")
    application.create_amenity(session, "second")
    create_data = {
        **apartment_create_data,
        "size": 0,
        "amenities": ["first", "second"],
    }
    assert not session.query(Apartment).count()
    response = client.post(
        "/api/apartments/", json=create_data, headers=landlord_auth_header
    )
    assert response.status_code == 422


@pytest.mark.parametrize(
    "user_auth_header",
    ["tenant_auth_header", "landlord_auth_header", "admin_auth_header"],
    indirect=True,
)
def test_fetch_apartments(
    session: Session, client: TestClient, apartment: Apartment, user_auth_header: dict
):
    assert session.query(Apartment).count() == 1
    response = client.get("/api/apartments/", headers=user_auth_header)
    assert response.status_code == 200
    result = response.json()
    assert isinstance(result, list)
    assert len(result) == 1


@pytest.mark.parametrize(
    "user_auth_header",
    ["tenant_auth_header", "landlord_auth_header", "admin_auth_header"],
    indirect=True,
)
def test_get_apartment(
    session: Session, client: TestClient, apartment: Apartment, user_auth_header: dict
):
    assert session.query(Apartment).count() == 1
    response = client.get(f"/api/apartments/{apartment.id}", headers=user_auth_header)
    assert response.status_code == 200
    result = response.json()
    assert isinstance(result, dict)
