from uuid import UUID
from sqlalchemy.orm.session import Session
from fastapi import APIRouter, Depends, HTTPException
from digirent.api import dependencies as deps
from digirent.api.apartment_applications.schema import ApartmentApplicationSchema
from digirent.app import Application
from digirent.app.error import ApplicationError
from digirent.database.models import Tenant

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
