from datetime import datetime
from typing import List
from digirent.database.enums import (
    ApartmentApplicationStatus,
    ContractStatus,
)
from digirent.app.error import ApplicationError
import pytest
from digirent.app import Application
from sqlalchemy.orm.session import Session
from sqlalchemy import or_
from digirent.database.models import (
    Apartment,
    ApartmentApplication,
    Contract,
    Tenant,
)


def test_tenant_apply_for_apartment(
    application: Application, tenant: Tenant, apartment: Apartment, session: Session
):
    assert not session.query(ApartmentApplication).count()
    application.apply_for_apartment(session, tenant, apartment)
    assert session.query(ApartmentApplication).count()
    apartment_application = session.query(ApartmentApplication).all()[0]
    assert apartment_application.tenant == tenant
    assert apartment_application.apartment == apartment
    assert apartment_application.status == ApartmentApplicationStatus.NEW


def test_landlord_reject_new_apartment_application_ok(
    new_apartment_application: ApartmentApplication,
    application: Application,
    session: Session,
):
    tenant_application = application.reject_apartment_application(
        session, new_apartment_application
    )
    assert tenant_application.status == ApartmentApplicationStatus.REJECTED
    tenant_application_db = (
        session.query(ApartmentApplication)
        .filter_by(tenant_id=new_apartment_application.tenant.id)
        .filter_by(apartment_id=new_apartment_application.apartment.id)
        .one_or_none()
    )
    assert tenant_application_db.status == ApartmentApplicationStatus.REJECTED


def test_landlord_consider_a_tenant_application_ok(
    new_apartment_application: ApartmentApplication,
    application: Application,
    session: Session,
):
    tenant_application = application.consider_apartment_application(
        session, new_apartment_application
    )
    assert tenant_application.status == ApartmentApplicationStatus.CONSIDERED
    tenant_application_db = (
        session.query(ApartmentApplication)
        .filter_by(tenant_id=new_apartment_application.tenant.id)
        .filter_by(apartment_id=new_apartment_application.apartment.id)
        .one_or_none()
    )
    assert tenant_application_db.status == ApartmentApplicationStatus.CONSIDERED


def test_landlord_start_move_in_process_ok(
    considered_apartment_application: ApartmentApplication,
    application: Application,
    session: Session,
):
    assert not session.query(Contract).count()
    tenant_application = application.process_apartment_application(
        session, considered_apartment_application
    )
    assert tenant_application.status == ApartmentApplicationStatus.PROCESSING
    assert session.query(Contract).count() == 1
    contract: Contract = session.query(Contract).all()[0]
    assert contract.status == ContractStatus.NEW


def test_tenant_sign_contract_for_move_in_process_ok(
    process_apartment_application: ApartmentApplication,
    application: Application,
    session: Session,
):
    assert process_apartment_application.status == ApartmentApplicationStatus.PROCESSING
    assert process_apartment_application.contract.status == ContractStatus.NEW
    assert not process_apartment_application.contract.tenant_has_signed
    application.tenant_signed_contract(session, process_apartment_application)
    assert process_apartment_application.contract.tenant_has_signed
    assert process_apartment_application.contract.status == ContractStatus.NEW


def test_landlord_sign_contract_for_move_in_process_ok(
    process_apartment_application: ApartmentApplication,
    application: Application,
    session: Session,
):
    assert process_apartment_application.status == ApartmentApplicationStatus.PROCESSING
    assert process_apartment_application.contract.status == ContractStatus.NEW
    assert not process_apartment_application.contract.landlord_has_signed
    application.landlord_signed_contract(session, process_apartment_application)
    assert process_apartment_application.contract.landlord_has_signed
    assert process_apartment_application.contract.status == ContractStatus.NEW


def test_landlord_provide_keys_to_tenant_on_awarded_application_ok(
    application: Application,
    awarded_apartment_application: ApartmentApplication,
    session: Session,
):

    contract: Contract = awarded_apartment_application.contract
    assert not contract.landlord_has_provided_keys
    assert contract.status == ContractStatus.SIGNED
    application.provide_keys_to_tenant(session, awarded_apartment_application)
    apartment_application = session.query(ApartmentApplication).get(
        awarded_apartment_application.id
    )
    assert apartment_application.contract.landlord_has_provided_keys
    assert apartment_application.contract.status == ContractStatus.SIGNED


def test_tenant_accept_keys_from_landlord_on_awarded_application_ok(
    application: Application,
    awarded_apartment_application: ApartmentApplication,
    session: Session,
):
    contract: Contract = awarded_apartment_application.contract
    assert not contract.tenant_has_received_keys
    assert contract.status == ContractStatus.SIGNED
    application.provide_keys_to_tenant(session, awarded_apartment_application)
    application.tenant_receive_keys(session, awarded_apartment_application)
    apartment_application = session.query(ApartmentApplication).get(
        awarded_apartment_application.id
    )
    assert apartment_application.contract.tenant_has_received_keys
    assert apartment_application.contract.status == ContractStatus.COMPLETED


def test_all_other_applications_rejected_on_application_completed_ok(
    session: Session,
    application: Application,
    new_apartment_applications: List[ApartmentApplication],
):
    assert len(new_apartment_applications) == 5
    assert all(
        app.status == ApartmentApplicationStatus.NEW
        for app in new_apartment_applications
    )
    app1, app2, app3, app4, app5 = new_apartment_applications
    application.reject_apartment_application(session, app1)
    application.consider_apartment_application(session, app2)
    application.consider_apartment_application(session, app3)
    application.process_apartment_application(session, app3)
    application.consider_apartment_application(session, app4)
    application.consider_apartment_application(session, app5)
    assert app1.status == ApartmentApplicationStatus.REJECTED
    assert all(
        app.status == ApartmentApplicationStatus.CONSIDERED
        for app in (app2, app4, app5)
    )
    assert app3.status == ApartmentApplicationStatus.PROCESSING
    application.tenant_signed_contract(session, app3)
    application.landlord_signed_contract(session, app3)
    assert app1.status == ApartmentApplicationStatus.REJECTED
    assert all(
        app.status == ApartmentApplicationStatus.CONSIDERED
        for app in (app2, app4, app5)
    )
    assert app3.status == ApartmentApplicationStatus.AWARDED
    application.provide_keys_to_tenant(session, app3)
    application.tenant_receive_keys(session, app3)
    assert all(
        app.status == ApartmentApplicationStatus.REJECTED
        for app in (app1, app2, app4, app5)
    )
    assert app3.status == ApartmentApplicationStatus.COMPLETED


def test_landlord_reject_apartment_application_not_in_new_status_fail(
    application: Application,
    session: Session,
    considered_apartment_application: ApartmentApplication,
):
    assert (
        considered_apartment_application.status == ApartmentApplicationStatus.CONSIDERED
    )
    with pytest.raises(ApplicationError):
        application.reject_apartment_application(
            session, considered_apartment_application
        )


def test_landlord_consider_apartment_application_not_in_new_status_fail(
    application: Application,
    session: Session,
    awarded_apartment_application: ApartmentApplication,
):
    assert awarded_apartment_application.status == ApartmentApplicationStatus.AWARDED
    with pytest.raises(ApplicationError):
        application.consider_apartment_application(
            session, awarded_apartment_application
        )


def test_landlord_start_move_in_process_for_application_not_in_considered_status_fail(
    application: Application,
    session: Session,
    new_apartment_application: ApartmentApplication,
):
    assert new_apartment_application.status == ApartmentApplicationStatus.NEW
    with pytest.raises(ApplicationError):
        application.process_apartment_application(session, new_apartment_application)


def test_landlord_start_move_in_process_for_another_apartment_application_when_there_is_an_ongoing_move_in_process_fail(
    application: Application,
    session: Session,
    process_apartment_application: ApartmentApplication,
    another_new_apartment_application: ApartmentApplication,
):
    assert another_new_apartment_application.id != process_apartment_application.id
    assert process_apartment_application.status == ApartmentApplicationStatus.PROCESSING
    assert another_new_apartment_application.status == ApartmentApplicationStatus.NEW
    application.consider_apartment_application(
        session, another_new_apartment_application
    )
    assert (
        another_new_apartment_application.status
        == ApartmentApplicationStatus.CONSIDERED
    )
    with pytest.raises(ApplicationError):
        application.process_apartment_application(
            session, another_new_apartment_application
        )


def test_tenant_sign_contract_for_application_not_in_processing_status_fail(
    new_apartment_application: ApartmentApplication,
    session: Session,
    application: Application,
):
    with pytest.raises(ApplicationError):
        application.tenant_signed_contract(session, new_apartment_application)


def test_tenant_sign_contract_not_in_new_status_fail(
    awarded_apartment_application: ApartmentApplication,
    session: Session,
    application: Application,
):
    with pytest.raises(ApplicationError):
        application.tenant_signed_contract(session, awarded_apartment_application)


def test_landlord_sign_contract_not_in_new_status_fail(
    new_apartment_application: ApartmentApplication,
    session: Session,
    application: Application,
):
    with pytest.raises(ApplicationError):
        application.landlord_signed_contract(session, new_apartment_application)


def test_landlord_process_another_application_when_one_application_is_complete_fail(
    another_considered_apartment_application: ApartmentApplication,
    completed_apartment_application: ApartmentApplication,
    session: Session,
    application: Application,
):
    with pytest.raises(ApplicationError):
        application.process_apartment_application(
            session, another_considered_apartment_application
        )


def test_another_tenant_apply_for_completed_apartment_application_fail(
    another_tenant: Tenant,
    session: Session,
    completed_apartment_application: ApartmentApplication,
    application: Application,
):
    with pytest.raises(ApplicationError):
        application.apply_for_apartment(
            session, another_tenant, completed_apartment_application.apartment
        )


def test_landlord_process_another_appliation_when_one_application_was_unsuccessful_ok(
    session: Session,
    application: Application,
    failed_apartment_application: ApartmentApplication,
    another_considered_apartment_application: ApartmentApplication,
):
    assert (
        another_considered_apartment_application.status
        == ApartmentApplicationStatus.CONSIDERED
    )
    assert (
        not session.query(ApartmentApplication)
        .join(Contract)
        .filter(
            or_(
                ApartmentApplication.status == ApartmentApplicationStatus.PROCESSING,
                ApartmentApplication.status == ApartmentApplicationStatus.AWARDED,
            )
        )
        .count()
    )
    application.process_apartment_application(
        session, another_considered_apartment_application
    )
    session.expire_all()
    assert (
        another_considered_apartment_application.status
        == ApartmentApplicationStatus.PROCESSING
    )
    assert (
        session.query(ApartmentApplication)
        .join(Contract)
        .filter(
            or_(
                ApartmentApplication.status == ApartmentApplicationStatus.PROCESSING,
                ApartmentApplication.status == ApartmentApplicationStatus.AWARDED,
            )
        )
        .count()
        == 1
    )


def test_tenant_apply_for_apartment_if_previous_one_failed_ok(
    session: Session,
    application: Application,
    failed_apartment_application: ApartmentApplication,
):
    assert failed_apartment_application.status == ApartmentApplicationStatus.FAILED
    assert (
        session.query(ApartmentApplication)
        .filter(
            ApartmentApplication.tenant_id == failed_apartment_application.tenant_id
        )
        .filter(
            ApartmentApplication.apartment_id
            == failed_apartment_application.apartment_id
        )
        .count()
        == 1
    )
    second_app = application.apply_for_apartment(
        session,
        failed_apartment_application.tenant,
        failed_apartment_application.apartment,
    )
    session.expire_all()
    assert (
        session.query(ApartmentApplication)
        .filter(
            ApartmentApplication.tenant_id == failed_apartment_application.tenant_id
        )
        .filter(
            ApartmentApplication.apartment_id
            == failed_apartment_application.apartment_id
        )
        .count()
        == 2
    )
    assert (
        session.query(ApartmentApplication).get(second_app.id).status
        == ApartmentApplicationStatus.NEW
    )


def test_tenant_decline_new_contract_ok(
    process_apartment_application: ApartmentApplication,
    application: Application,
    session: Session,
):
    declined_on = datetime.now()
    assert process_apartment_application.contract.status == ContractStatus.NEW
    assert not process_apartment_application.contract.tenant_declined
    assert not process_apartment_application.contract.tenant_declined_on
    application.decline_contract(
        session,
        process_apartment_application,
        declined_on,
        process_apartment_application.tenant,
    )
    session.expire_all()
    apartment_application = session.query(ApartmentApplication).get(
        process_apartment_application.id
    )
    assert apartment_application.status == ApartmentApplicationStatus.FAILED
    assert apartment_application.contract.status == ContractStatus.DECLINED
    assert apartment_application.contract.tenant_declined_on == declined_on
    assert apartment_application.contract.tenant_declined


def test_tenant_or_landlord_decline_already_signed_contract_fail(
    awarded_apartment_application: ApartmentApplication,
    session: Session,
    application: Application,
):
    assert awarded_apartment_application.contract.status == ContractStatus.SIGNED
    with pytest.raises(ApplicationError):
        application.decline_contract(
            session,
            awarded_apartment_application,
            datetime.utcnow(),
            awarded_apartment_application.tenant,
        )
    with pytest.raises(ApplicationError):
        application.decline_contract(
            session,
            awarded_apartment_application,
            datetime.utcnow(),
            awarded_apartment_application.apartment.landlord,
        )


def test_tenant_or_landlord_sign_already_declined_contract_fail(
    process_apartment_application: ApartmentApplication,
    session: Session,
    application: Application,
):
    assert process_apartment_application.contract.status == ContractStatus.NEW
    application.decline_contract(
        session,
        process_apartment_application,
        datetime.now(),
        process_apartment_application.tenant,
    )
    assert process_apartment_application.contract.status == ContractStatus.DECLINED
    with pytest.raises(ApplicationError):
        application.tenant_signed_contract(session, process_apartment_application)
    with pytest.raises(ApplicationError):
        application.landlord_signed_contract(session, process_apartment_application)


def test_landlord_decline_new_contract_ok(
    process_apartment_application: ApartmentApplication,
    application: Application,
    session: Session,
):
    declined_on = datetime.now()
    assert process_apartment_application.contract.status == ContractStatus.NEW
    assert not process_apartment_application.contract.tenant_declined
    assert not process_apartment_application.contract.tenant_declined_on
    application.decline_contract(
        session,
        process_apartment_application,
        declined_on,
        process_apartment_application.apartment.landlord,
    )
    session.expire_all()
    apartment_application = session.query(ApartmentApplication).get(
        process_apartment_application.id
    )
    assert apartment_application.status == ApartmentApplicationStatus.FAILED
    assert apartment_application.contract.status == ContractStatus.DECLINED
    assert apartment_application.contract.landlord_declined_on == declined_on
    assert apartment_application.contract.landlord_declined


def test_expire_contract_ok(
    process_apartment_application: ApartmentApplication,
    application: Application,
    session: Session,
):
    expired_on = datetime.now()
    assert process_apartment_application.contract.status == ContractStatus.NEW
    assert not process_apartment_application.contract.tenant_declined
    assert not process_apartment_application.contract.tenant_declined_on
    application.expire_contract(
        session,
        process_apartment_application,
        expired_on,
    )
    session.expire_all()
    apartment_application = session.query(ApartmentApplication).get(
        process_apartment_application.id
    )
    assert apartment_application.status == ApartmentApplicationStatus.FAILED
    assert apartment_application.contract.status == ContractStatus.EXPIRED
    assert apartment_application.contract.expired_on == expired_on
    assert apartment_application.contract.expired


def test_cancel_contract_ok(
    process_apartment_application: ApartmentApplication,
    application: Application,
    session: Session,
):
    canceled_on = datetime.now()
    assert process_apartment_application.contract.status == ContractStatus.NEW
    assert not process_apartment_application.contract.tenant_declined
    assert not process_apartment_application.contract.tenant_declined_on
    application.cancel_contract(
        session,
        process_apartment_application,
        canceled_on,
    )
    session.expire_all()
    apartment_application = session.query(ApartmentApplication).get(
        process_apartment_application.id
    )
    assert apartment_application.status == ApartmentApplicationStatus.FAILED
    assert apartment_application.contract.status == ContractStatus.CANCELED
    assert apartment_application.contract.canceled_on == canceled_on
    assert apartment_application.contract.canceled


def test_landlord_provide_keys_for_contract_not_signed_fail(
    process_apartment_application: ApartmentApplication,
    session: Session,
    application: Application,
):
    assert process_apartment_application.status == ApartmentApplicationStatus.PROCESSING
    with pytest.raises(ApplicationError):
        application.provide_keys_to_tenant(session, process_apartment_application)


def test_tenant_accept_keys_for_contract_not_signed_fail(
    process_apartment_application: ApartmentApplication,
    session: Session,
    application: Application,
):
    assert process_apartment_application.status == ApartmentApplicationStatus.PROCESSING
    with pytest.raises(ApplicationError):
        application.tenant_receive_keys(session, process_apartment_application)


def test_tenant_accept_keys_when_landlord_has_not_provided_keys_fail(
    awarded_apartment_application: ApartmentApplication,
    session: Session,
    application: Application,
):
    assert awarded_apartment_application.status == ApartmentApplicationStatus.AWARDED
    assert not awarded_apartment_application.contract.landlord_has_provided_keys
    with pytest.raises(ApplicationError):
        application.tenant_receive_keys(session, awarded_apartment_application)


def test_tenant_apply_for_same_apartment_again_fail(
    application: Application, tenant: Tenant, apartment: Apartment, session: Session
):
    application.apply_for_apartment(session, tenant, apartment)
    apartment_application = session.query(ApartmentApplication).all()[0]
    assert apartment_application.tenant == tenant
    assert apartment_application.apartment == apartment
    assert apartment_application.status == ApartmentApplicationStatus.NEW
    with pytest.raises(ApplicationError):
        application.apply_for_apartment(session, tenant, apartment)


def test_tenant_apply_for_already_awarded_apartment_fail(
    application: Application,
    awarded_apartment_application: ApartmentApplication,
    another_tenant: Tenant,
    session: Session,
):
    assert awarded_apartment_application.status == ApartmentApplicationStatus.AWARDED
    with pytest.raises(ApplicationError):
        application.apply_for_apartment(
            session, another_tenant, awarded_apartment_application.apartment
        )
