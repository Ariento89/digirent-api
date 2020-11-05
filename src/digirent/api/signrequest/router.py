from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from signrequest_client.models.document import Document
from sqlalchemy.orm.session import Session
import digirent.api.dependencies as dependencies
from digirent.app import Application
from digirent.app.error import ApplicationError
from digirent.database.enums import UserRole
from digirent.database.models import Admin, ApartmentApplication, User
from digirent.core.services.sign_request import (
    get_event,
    get_list_of_events,
    get_list_of_documents,
    get_document,
)
from signrequest_client.rest import ApiException

router = APIRouter()


@router.get("/events/{apartment_application_id}")
def get_signrequest_events_for_apartment_application(
    apartment_application_id: UUID,
    page: int = 1,
    page_size: int = 20,
    admin: Admin = Depends(dependencies.get_current_admin_user),
):
    return get_list_of_events(apartment_application_id, page, page_size)


@router.get("/event/{event_id}")
def get_signrequest_event(
    event_id: str, admin: Admin = Depends(dependencies.get_current_admin_user)
):
    return get_event(event_id)


@router.get("/documents/{apartment_application_id}")
def get_signrequest_documents_for_apartment_application(
    apartment_application_id: UUID,
    page: int = 1,
    page_size: int = 20,
    admin: Admin = Depends(dependencies.get_current_admin_user),
):
    return get_list_of_documents(apartment_application_id, page, page_size)


@router.get("/document/{document_id}")
def get_signrequest_document(
    document_id: str, admin: Admin = Depends(dependencies.get_current_admin_user)
):
    try:
        return get_document(document_id)
    except ApiException as e:
        raise HTTPException(e.status, str(e.reason))


@router.post("/document/{document_id}/verify")
def verify_signrequest_document(
    document_id: str,
    background_tasks: BackgroundTasks,
    admin: Admin = Depends(dependencies.get_current_admin_user),
    session: Session = Depends(dependencies.get_database_session),
    application: Application = Depends(dependencies.get_application),
):
    def update_contract(signers, apartment_application_id):
        try:
            for signer in signers:
                if not signer.needs_to_sign:
                    continue
                signed_on = signer.signed_on
                signer_declined_on = signer.declined_on
                signer_email = signer.email
                apartment_application: ApartmentApplication = session.query(
                    ApartmentApplication
                ).get(apartment_application_id)
                if not apartment_application:
                    return
                signer_user: User = (
                    session.query(User).filter(User.email == signer_email).one_or_none()
                )
                if not signer_user:
                    return
                if signer.declined:
                    application.decline_contract(
                        session, apartment_application, signer_declined_on, signer_user
                    )
                if signer.signed:
                    if signer_user.role == UserRole.TENANT:
                        application.tenant_signed_contract(
                            session, apartment_application, signed_on
                        )

                    elif signer_user.role == UserRole.LANDLORD:
                        application.landlord_signed_contract(
                            session, apartment_application, signed_on
                        )
        except ApplicationError:
            # TODO log this
            return

    try:
        document: Document = get_document(document_id)
        apartment_application_id = document.external_id
        signrequest = document.signrequest
        signers = signrequest.signers
        result = [s for s in signers if s.needs_to_sign]
        background_tasks.add_task(
            update_contract,
            signers=signers,
            apartment_application_id=apartment_application_id,
        )
        return result
    except ApiException as e:
        raise HTTPException(e.status, str(e.reason))
