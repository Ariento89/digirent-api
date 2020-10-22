from datetime import datetime
from typing import List
import pytest
from sqlalchemy.orm.session import Session
from digirent.app import Application
from digirent.database.enums import ApartmentApplicationStatus, ContractStatus
from digirent.database.models import Apartment, ApartmentApplication, Contract, Tenant


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
def new_apartment_applications(
    session: Session, application: Application, apartment: Apartment
) -> List[ApartmentApplication]:
    applications = []
    for i in range(5):
        tenant = application.create_tenant(
            session,
            f"fname{i}",
            f"lname{i}",
            datetime.now().date(),
            f"jdoe{i}#email.com",
            f"012345{i}",
            f"password{i}",
        )
        applications.append(application.apply_for_apartment(session, tenant, apartment))
    return applications
