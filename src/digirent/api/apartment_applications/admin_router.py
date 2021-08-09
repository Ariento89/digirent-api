from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm.query import Query
from sqlalchemy.orm.session import Session
from fastapi import (
    APIRouter,
    Depends,
)
from digirent.api import dependencies as deps
from digirent.api.apartment_applications.schema import (
    ApartmentApplicationSchema,
)
from digirent.database.models import (
    Admin,
    Apartment,
    ApartmentApplication,
)

router = APIRouter()


@router.get(
    "/",
    response_model=List[ApartmentApplicationSchema],
)
def fetch_applications_for_apartments(
    apartment_id: Optional[UUID] = None,
    landlord_id: Optional[UUID] = None,
    tenant_id: Optional[UUID] = None,
    admin: Admin = Depends(deps.get_current_admin_user),
    session: Session = Depends(deps.get_database_session),
):
    """
    Endpoint for admin to fetch apartment applications.

    TODO: include date range filter
    """
    query: Query = session.query(ApartmentApplication).join(
        Apartment, ApartmentApplication.apartment_id == Apartment.id
    )
    if apartment_id is not None:
        query = query.filter(ApartmentApplication.apartment_id == apartment_id)
    if landlord_id is not None:
        query = query.filter(Apartment.landlord_id == landlord_id)
    if tenant_id is not None:
        query = query.filter(Apartment.tenant_id == tenant_id)
    return query.all()
