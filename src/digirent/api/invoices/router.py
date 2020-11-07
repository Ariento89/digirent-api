from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm.session import Session
from mollie.api.client import Client
from mollie.api.error import Error
from digirent.core import config
from digirent.api import dependencies as deps
from digirent.database.enums import InvoiceStatus
from digirent.database.models import Admin, Invoice
from .schema import InvoiceType, InvoiceSchema

router = APIRouter()

mollie_client = Client()
mollie_client.set_api_key(config.MOLLIE_API_KEY)


@router.get("/", response_model=List[InvoiceSchema])
def fetch_all_invoices(
    apartment_application_id: Optional[UUID] = None,
    user_id: Optional[UUID] = None,
    type: Optional[InvoiceType] = None,
    admin: Admin = Depends(deps.get_current_admin_user),
    session: Session = Depends(deps.get_database_session),
):
    query = session.query(Invoice)
    if type:
        query = query.filter(Invoice.type == type)
    if apartment_application_id:
        query = query.filter(
            Invoice.apartment_application_id == apartment_application_id
        )
    elif user_id:
        query = query.filter(Invoice.user_id == user_id)
    return query.all()


@router.post("/{invoice_id}/verify", response_model=InvoiceSchema)
def verify_invoice(
    invoice_id: UUID,
    admin: Admin = Depends(deps.get_current_admin_user),
    session: Session = Depends(deps.get_database_session),
):
    invoice: Invoice = session.query(Invoice).get(invoice_id)
    if not invoice:
        raise HTTPException(404, "Invoice not found")
    try:
        payment = mollie_client.payments.get(invoice.payment_id)
        if payment.is_paid():
            invoice.status = InvoiceStatus.PAID
            session.commit()
        elif payment.is_pending():
            pass
        elif not payment.is_open():
            invoice.status = InvoiceStatus.FAILED
            session.commit()
    except Error as err:
        # TODO log error
        print("\n\n\n\n\n")
        print(err)
        print("\n\n\n\n\n")
        raise HTTPException(400, str(err))
    return invoice
