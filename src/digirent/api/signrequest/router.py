from uuid import UUID
from fastapi import APIRouter, Depends
import digirent.api.dependencies as dependencies
from digirent.database.models import Admin
from digirent.core.services.sign_request import (
    get_event,
    get_list_of_events,
    get_list_of_documents,
    get_document,
)

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
    return get_document(document_id)
