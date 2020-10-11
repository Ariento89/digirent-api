from uuid import UUID
from sqlalchemy.orm.session import Session
from fastapi import APIRouter, Depends, HTTPException
from digirent.api import dependencies as deps
from digirent.api.apartment_applications.schema import ApartmentApplicationSchema
from digirent.app import Application
from digirent.app.error import ApplicationError
from digirent.database.models import Apartment, ApartmentApplication, Landlord, Tenant

router = APIRouter()


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
        return app.reject_tenant_application(session, landlord, apartment_application)
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
        return app.consider_tenant_application(session, landlord, apartment_application)
    except ApplicationError as e:
        raise HTTPException(400, str(e))


@router.post("/{application_id}/accept", response_model=ApartmentApplicationSchema)
def accept_application(
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
        return app.accept_tenant_application(session, landlord, apartment_application)
        # TODO fix the mixed usage of tenant_application and apartment_application
    except ApplicationError as e:
        raise HTTPException(400, str(e))
