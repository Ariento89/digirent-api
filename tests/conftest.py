from datetime import datetime

import pytest
import io
import shutil
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm.session import Session
from starlette.config import environ
from pathlib import Path

from digirent.core.services.file_service import FileService


environ["APP_ENV"] = "test"

from digirent.core.config import DATABASE_URL, UPLOAD_PATH
import digirent.util as util
from digirent.database.services.base import DBService
from digirent.web_app import get_app
from digirent.database.models import (
    Admin,
    Amenity,
    Apartment,
    ApartmentApplication,
    Contract,
    Landlord,
    Tenant,
    User,
)
from digirent.database.enums import (
    ApartmentApplicationStatus,
    BookingRequestStatus,
    ContractStatus,
    FurnishType,
    HouseType,
    UserRole,
)
from digirent.app.container import ApplicationContainer
from digirent.database.base import SessionLocal, Base
from digirent.database.services.user import UserService
from digirent.app import Application


@pytest.fixture(autouse=True)
def create_test_database():
    metadata: MetaData = Base.metadata
    url = str(DATABASE_URL)
    engine = create_engine(url)
    metadata.create_all(engine)
    yield  # Run the tests.
    metadata.drop_all(engine)


@pytest.fixture
def app() -> FastAPI:
    return get_app()


@pytest.fixture
def application() -> Application:
    return ApplicationContainer.app()


@pytest.fixture
def client(app) -> TestClient:
    return TestClient(app)


@pytest.fixture
def session() -> Session:
    session: Session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def tenant_create_data() -> dict:
    return {
        "first_name": "Tenant",
        "last_name": "Doe",
        "email": "tenantdoe@gmail.com",
        "dob": datetime.now().date(),
        "phone_number": "0022345678",
        "password": "testpassword",
        "role": UserRole.TENANT,
    }


@pytest.fixture
def landlord_create_data() -> dict:
    return {
        "first_name": "Landlord",
        "last_name": "Doe",
        "email": "landlorddoe@gmail.com",
        "phone_number": "0002345678",
        "dob": None,
        "password": "testpassword",
        "role": UserRole.LANDLORD,
    }


@pytest.fixture
def admin_create_data() -> dict:
    return {
        "first_name": "Admin",
        "last_name": "Doe",
        "email": "admindoe@gmail.com",
        "phone_number": "0012345678",
        "dob": None,
        "password": "testpassword",
        "role": UserRole.ADMIN,
    }


@pytest.fixture
def user_service():
    return UserService()


@pytest.fixture
def tenant_service():
    return DBService[Tenant](Tenant)


@pytest.fixture
def landlord_service():
    return DBService[Landlord](Landlord)


@pytest.fixture
def apartment_service():
    return DBService[Apartment](Apartment)


@pytest.fixture
def amenity_service():
    return DBService[Amenity](Amenity)


@pytest.fixture
def file_service():
    return FileService()


@pytest.fixture
def tenant(session: Session, tenant_create_data: dict) -> Tenant:
    create_data = {**tenant_create_data}
    hashed_password = util.hash_password(create_data["password"])
    del create_data["password"]
    del create_data["role"]
    create_data["hashed_password"] = hashed_password
    tenant = Tenant(**create_data)
    session.add(tenant)
    session.commit()
    assert session.query(Tenant).get(tenant.id)
    return tenant


@pytest.fixture
def landlord(session: Session, landlord_create_data: dict) -> Landlord:
    create_data = {**landlord_create_data}
    hashed_password = util.hash_password(create_data["password"])
    del create_data["password"]
    del create_data["role"]
    create_data["hashed_password"] = hashed_password
    landlord = Landlord(**create_data)
    session.add(landlord)
    session.commit()
    assert session.query(Landlord).get(landlord.id)
    return landlord


@pytest.fixture
def admin(session: Session, admin_create_data: dict) -> User:
    create_data = {**admin_create_data}
    hashed_password = util.hash_password(create_data["password"])
    del create_data["password"]
    del create_data["role"]
    create_data["hashed_password"] = hashed_password
    admin = Admin(**create_data)
    session.add(admin)
    session.commit()
    assert session.query(Admin).get(admin.id)
    return admin


@pytest.fixture
def tenant_auth_header(client: TestClient, tenant: User, tenant_create_data: dict):
    response = client.post(
        "/api/auth/",
        data={
            "username": tenant.email,
            "password": tenant_create_data["password"],
        },
    )
    result = response.json()
    assert response.status_code == 200
    assert "access_token" in result
    assert "token_type" in result
    return {"Authorization": f"Bearer {result['access_token']}"}


@pytest.fixture
def landlord_auth_header(
    client: TestClient, landlord: User, landlord_create_data: dict
):
    response = client.post(
        "/api/auth/",
        data={
            "username": landlord.email,
            "password": landlord_create_data["password"],
        },
    )
    result = response.json()
    assert response.status_code == 200
    assert "access_token" in result
    assert "token_type" in result
    return {"Authorization": f"Bearer {result['access_token']}"}


@pytest.fixture
def admin_auth_header(client: TestClient, admin: User, admin_create_data: dict):
    response = client.post(
        "/api/auth/",
        data={
            "username": admin.email,
            "password": admin_create_data["password"],
        },
    )
    result = response.json()
    assert response.status_code == 200
    assert "access_token" in result
    assert "token_type" in result
    return {"Authorization": f"Bearer {result['access_token']}"}


@pytest.fixture
def user_create_data(request):
    return request.getfixturevalue(request.param)


@pytest.fixture
def non_admin_user_create_data(request):
    return request.getfixturevalue(request.param)


@pytest.fixture
def user(request):
    return request.getfixturevalue(request.param)


@pytest.fixture
def user_auth_header(request):
    return request.getfixturevalue(request.param)


@pytest.fixture
def non_admin_user(request):
    return request.getfixturevalue(request.param)


@pytest.fixture
def non_admin_user_auth_header(request):
    return request.getfixturevalue(request.param)


@pytest.fixture
def file():
    xfile = io.BytesIO()
    xfile.write(b"Copy data")
    xfile.seek(0)
    return xfile


@pytest.fixture
def clear_upload():
    yield
    shutil.rmtree(UPLOAD_PATH)
    assert not Path(UPLOAD_PATH).exists()


@pytest.fixture
def apartment(
    session: Session, landlord: Landlord, application: Application
) -> Apartment:
    apartment = application.create_apartment(
        session,
        landlord,
        "apartment name",
        450.35,
        320.40,
        "some address",
        "Nigeria",
        "Kano",
        "KN",
        "some description",
        HouseType.BUNGALOW,
        3,
        2,
        1200,
        FurnishType.UNFURNISHED,
        datetime.utcnow().date(),
        datetime.utcnow().date(),
        [],
    )
    assert session.query(Apartment).get(apartment.id)
    return apartment


@pytest.fixture
def another_landlord(session: Session, application: Application) -> Landlord:
    return application.create_landlord(
        session,
        "Another",
        "Landlord",
        datetime.utcnow().date(),
        "another_landlord@gmail.com",
        "001234578",
        "password",
    )


@pytest.fixture
def another_tenant(session: Session, application: Application) -> Tenant:
    return application.create_tenant(
        session,
        "Another",
        "Tenant",
        datetime.utcnow().date(),
        "another_tenant@gmail.com",
        "01023478",
        "password",
    )


@pytest.fixture
def another_landlord_auth_header(client: TestClient, another_landlord: Landlord):
    response = client.post(
        "/api/auth/",
        data={
            "username": another_landlord.email,
            "password": "password",
        },
    )
    result = response.json()
    assert response.status_code == 200
    assert "access_token" in result
    assert "token_type" in result
    return {"Authorization": f"Bearer {result['access_token']}"}


@pytest.fixture
def another_tenant_auth_header(client: TestClient, another_tenant: Tenant):
    response = client.post(
        "/api/auth/",
        data={
            "username": another_tenant.email,
            "password": "password",
        },
    )
    result = response.json()
    assert response.status_code == 200
    assert "access_token" in result
    assert "token_type" in result
    return {"Authorization": f"Bearer {result['access_token']}"}


@pytest.fixture
def booking_request(
    application: Application,
    tenant: Tenant,
    landlord: Landlord,
    apartment: Apartment,
    session: Session,
):
    booking_request = application.invite_tenant_to_apply(
        session, landlord, tenant, apartment
    )
    assert booking_request.status == BookingRequestStatus.PENDING
    assert not booking_request.apartment_application_id
    return booking_request


@pytest.fixture
def new_apartment_application(
    tenant: Tenant, apartment: Apartment, session: Session
) -> ApartmentApplication:
    app = ApartmentApplication(tenant_id=tenant.id, apartment_id=apartment.id)
    session.add(app)
    session.commit()
    assert app.status == ApartmentApplicationStatus.NEW
    return app


@pytest.fixture
def rejected_apartment_application(
    new_apartment_application: ApartmentApplication, session: Session
) -> ApartmentApplication:
    new_apartment_application.is_rejected = True
    session.commit()
    assert new_apartment_application.status == ApartmentApplicationStatus.REJECTED
    return new_apartment_application


@pytest.fixture
def considered_apartment_application(
    new_apartment_application: ApartmentApplication, session: Session
):
    new_apartment_application.is_considered = True
    session.commit()
    assert new_apartment_application.status == ApartmentApplicationStatus.CONSIDERED
    return new_apartment_application


@pytest.fixture
def new_contract(
    considered_apartment_application: ApartmentApplication, session: Session
):
    contract = Contract(apartment_application_id=considered_apartment_application.id)
    session.add(contract)
    session.commit()
    assert contract.status == ContractStatus.NEW
    return contract


@pytest.fixture
def process_apartment_application(
    considered_apartment_application: ApartmentApplication, new_contract: Contract
):
    assert (
        considered_apartment_application.status == ApartmentApplicationStatus.PROCESSING
    )
    return considered_apartment_application


@pytest.fixture
def signed_contract(
    process_apartment_application: ApartmentApplication, session: Session
):
    contract: Contract = process_apartment_application.contract
    contract.tenant_has_signed = True
    contract.landlord_has_signed = True
    session.commit()
    assert contract.status == ContractStatus.SIGNED
    assert process_apartment_application.status == ApartmentApplicationStatus.AWARDED
    return contract


@pytest.fixture
def completed_contract(signed_contract: Contract, session: Session):
    signed_contract.tenant_has_signed = True
    signed_contract.landlord_has_signed = True
    signed_contract.landlord_has_provided_keys = True
    signed_contract.tenant_has_received_keys = True
    session.commit()
    assert signed_contract.status == ContractStatus.COMPLETED
    assert process_apartment_application.status == ApartmentApplicationStatus.COMPLETED
    return signed_contract


@pytest.fixture
def awarded_apartment_application(
    process_apartment_application: ApartmentApplication, signed_contract: Contract
):
    assert process_apartment_application.status == ApartmentApplicationStatus.AWARDED
    return process_apartment_application


@pytest.fixture
def another_new_apartment_application(
    another_tenant: Tenant, apartment: Apartment, session: Session
) -> ApartmentApplication:
    app = ApartmentApplication(tenant_id=another_tenant.id, apartment_id=apartment.id)
    session.add(app)
    session.commit()
    assert app.status == ApartmentApplicationStatus.NEW
    return app


@pytest.fixture
def another_considered_application(
    another_tenant: Tenant, apartment: Apartment, session: Session
) -> ApartmentApplication:
    app = ApartmentApplication(tenant_id=another_tenant.id, apartment_id=apartment.id)
    app.is_considered = True
    session.add(app)
    session.commit()
    assert app.status == ApartmentApplicationStatus.CONSIDERED
    return app
