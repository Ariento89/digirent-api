from typing import List
from uuid import UUID
from sqlalchemy.orm.session import Session
from fastapi import APIRouter, Depends, HTTPException
from digirent.api import dependencies as deps
from digirent.api.apartment_applications.schema import (
    ApartmentApplicationSchema,
    SignrequestEventSchema,
)
from digirent.app import Application
from digirent.app.error import ApplicationError
from digirent.database.models import Apartment, ApartmentApplication, Landlord, Tenant

router = APIRouter()


@router.post("/contract", status_code=200)
def signrequest_contract_callback(
    payload: SignrequestEventSchema,
    session: Session = Depends(deps.get_database_session),
    application: Application = Depends(deps.get_application)
    # payload: dict = Body(...)
):
    # event_uuid = payload.uuid
    # event_status = payload.status
    # event_timestamp = payload.timestamp
    # event_hash = payload.event_hash
    # event_document_id = document.uuid
    # document_status = document.status

    # TODO verify hash
    target_event_types = [
        "declined",
        "cancelled",
        "expired",
        "signed",
        "signer_signed",
        "signer_viewed_email",
        "signer_viewed",
    ]
    event_type = payload.event_type
    document = payload.document
    document_signers = document.signrequest.signers
    external_id = document.external_id
    if event_type not in target_event_types:
        return
    apartment_application: ApartmentApplication = session.query(
        ApartmentApplication
    ).get(external_id)
    if not apartment_application:
        return
    tenant: Tenant = apartment_application.tenant
    landlord: Landlord = apartment_application.apartment.landlord
    for signer in document_signers:
        if not signer.needs_to_sign:
            continue
        # TODO store date time
        # signed_on = signer.signed_on
        # signer_declined_on = signer.declined_on
        signer_email = signer.email
        if tenant.email == signer_email:
            if signer.declined:
                # TODO tenant declined contract
                pass
            elif signer.signed:
                application.tenant_signed_contract(session, apartment_application)

        if landlord.email == signer_email:
            if signer.declined:
                # TODO landlord declined contract
                pass
            elif signer.signed:
                application.landlord_signed_contract(session, apartment_application)
    return


@router.post(
    "/{apartment_id}", status_code=201, response_model=ApartmentApplicationSchema
)
def apply(
    apartment_id: UUID,
    tenant: Tenant = Depends(deps.get_current_tenant),
    session: Session = Depends(deps.get_database_session),
    application: Application = Depends(deps.get_application),
):
    try:
        apartment = application.apartment_service.get(session, apartment_id)
        if not apartment:
            raise HTTPException(404, "Apartment not found")
        return application.apply_for_apartment(session, tenant, apartment)
    except ApplicationError as e:
        raise HTTPException(400, str(e))


@router.post(
    "/{application_id}/reject",
    status_code=200,
    response_model=ApartmentApplicationSchema,
)
def reject_application(
    application_id: UUID,
    landlord: Landlord = Depends(deps.get_current_landlord),
    session: Session = Depends(deps.get_database_session),
    app: Application = Depends(deps.get_application),
):
    try:
        apartment_application: ApartmentApplication = (
            session.query(ApartmentApplication)
            .join(Apartment, ApartmentApplication.apartment_id == Apartment.id)
            .filter(ApartmentApplication.id == application_id)
            .filter(Apartment.landlord_id == landlord.id)
            .one_or_none()
        )
        if not apartment_application:
            raise HTTPException(404, "application not found")
        return app.reject_apartment_application(session, apartment_application)
    except ApplicationError as e:
        raise HTTPException(400, str(e))


@router.post(
    "/{application_id}/consider",
    status_code=200,
    response_model=ApartmentApplicationSchema,
)
def consider_application(
    application_id: UUID,
    landlord: Landlord = Depends(deps.get_current_landlord),
    session: Session = Depends(deps.get_database_session),
    app: Application = Depends(deps.get_application),
):
    try:
        apartment_application: ApartmentApplication = (
            session.query(ApartmentApplication)
            .join(Apartment, ApartmentApplication.apartment_id == Apartment.id)
            .filter(ApartmentApplication.id == application_id)
            .filter(Apartment.landlord_id == landlord.id)
            .one_or_none()
        )
        if not apartment_application:
            raise HTTPException(404, "application not found")
        return app.consider_apartment_application(session, apartment_application)
    except ApplicationError as e:
        raise HTTPException(400, str(e))


@router.post(
    "/{application_id}/process",
    status_code=200,
    response_model=ApartmentApplicationSchema,
)
def process_application(
    application_id: UUID,
    landlord: Landlord = Depends(deps.get_current_landlord),
    session: Session = Depends(deps.get_database_session),
    app: Application = Depends(deps.get_application),
):
    try:
        apartment_application: ApartmentApplication = (
            session.query(ApartmentApplication)
            .join(Apartment, ApartmentApplication.apartment_id == Apartment.id)
            .filter(ApartmentApplication.id == application_id)
            .filter(Apartment.landlord_id == landlord.id)
            .one_or_none()
        )
        if not apartment_application:
            raise HTTPException(404, "application not found")
        return app.process_apartment_application(session, apartment_application)
    except ApplicationError as e:
        raise HTTPException(400, str(e))


@router.get("/{apartment_id}", response_model=List[ApartmentApplicationSchema])
def fetch_applications_for_apartments(
    apartment_id: UUID,
    landlord: Landlord = Depends(deps.get_current_landlord),
    session: Session = Depends(deps.get_database_session),
):
    try:
        apartment = (
            session.query(Apartment)
            .filter(Apartment.landlord_id == landlord.id)
            .filter(Apartment.id == apartment_id)
            .first()
        )
        if not apartment:
            raise HTTPException(404, "Apartment not found")
        return (
            session.query(ApartmentApplication)
            .join(Apartment)
            .filter(Apartment.landlord_id == landlord.id)
            .filter(ApartmentApplication.apartment_id == apartment_id)
            .all()
        )
    except ApplicationError as e:
        raise HTTPException(400, str(e))


@router.get("/", response_model=List[ApartmentApplicationSchema])
def fetch_tenant_applications(
    tenant: Tenant = Depends(deps.get_current_tenant),
    session: Session = Depends(deps.get_database_session),
):
    try:
        return (
            session.query(ApartmentApplication)
            .filter(ApartmentApplication.tenant_id == tenant.id)
            .all()
        )
    except ApplicationError as e:
        raise HTTPException(400, str(e))
