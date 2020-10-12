from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm.session import Session
from digirent.api import dependencies as deps
from digirent.api.invites.schema import InviteCreateSchema, InviteSchema
from digirent.app import Application
from digirent.app.error import ApplicationError
from digirent.database.models import Apartment, BookingRequest, Landlord, Tenant


router = APIRouter()


@router.post("/", status_code=201, response_model=InviteSchema)
def invite_tenant(
    data: InviteCreateSchema,
    landlord: Landlord = Depends(deps.get_current_landlord),
    session: Session = Depends(deps.get_database_session),
    application: Application = Depends(deps.get_application),
):
    try:
        existing_request = (
            session.query(BookingRequest)
            .filter(BookingRequest.apartment_id == data.apartment_id)
            .filter(BookingRequest.tenant_id == data.tenant_id)
            .first()
        )
        if existing_request:
            raise HTTPException(
                400, "Tenant has already been invited to apply for this apartment"
            )
        tenant: Tenant = session.query(Tenant).get(data.tenant_id)
        if not tenant:
            raise HTTPException(404, "Tenant not found")
        apartment: Apartment = (
            session.query(Apartment)
            .filter(Apartment.landlord_id == landlord.id)
            .filter(Apartment.id == data.apartment_id)
            .first()
        )
        if not apartment:
            raise HTTPException(404, "Apartment not found")
        return application.invite_tenant_to_apply(session, landlord, tenant, apartment)
    except ApplicationError as e:
        raise HTTPException(400, str(e))


@router.post("/{invitation_id}", response_model=InviteSchema)
def accept_invite(
    invitation_id: UUID,
    tenant: Tenant = Depends(deps.get_current_tenant),
    session: Session = Depends(deps.get_database_session),
    application: Application = Depends(deps.get_application),
):
    try:
        invitation = (
            session.query(BookingRequest)
            .filter(BookingRequest.tenant_id == tenant.id)
            .filter(BookingRequest.id == invitation_id)
            .first()
        )
        if not invitation:
            raise HTTPException(404, "Invite not found")
        return application.accept_application_invitation(session, tenant, invitation)
    except ApplicationError as e:
        raise HTTPException(400, str(e))


@router.delete("/{invitation_id}", response_model=InviteSchema)
def rejct_invite(
    invitation_id: UUID,
    tenant: Tenant = Depends(deps.get_current_tenant),
    session: Session = Depends(deps.get_database_session),
    application: Application = Depends(deps.get_application),
):
    try:
        invitation = (
            session.query(BookingRequest)
            .filter(BookingRequest.tenant_id == tenant.id)
            .filter(BookingRequest.id == invitation_id)
            .first()
        )
        if not invitation:
            raise HTTPException(404, "Invite not found")
        return application.reject_application_invitation(session, tenant, invitation)
    except ApplicationError as e:
        raise HTTPException(400, str(e))
