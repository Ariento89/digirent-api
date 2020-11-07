from fastapi import APIRouter, Body, HTTPException, Depends
from sqlalchemy.orm.session import Session
from mollie.api.client import Client
from mollie.api.error import Error
from digirent.core import config
from digirent.api import dependencies as deps
from digirent.database.enums import InvoiceStatus, InvoiceType
from digirent.database.models import Invoice

router = APIRouter()

mollie_client = Client()
mollie_client.set_api_key(config.MOLLIE_API_KEY)


@router.route("/webhook", methods=["GET", "POST", "PUT"])
def payments_webhook_callback(
    payload: Body(...), session: Session = Depends(deps.get_database_session)
):
    try:
        if "id" not in payload:
            raise HTTPException(404, "Unknown payment id")

        payment_id = payload["id"]
        payment = mollie_client.payments.get(payment_id)
        # TODO Better key fields
        invoice_type = payment.metadata["type"]
        invoice_id = payment.metadata["invoice_id"]

        try:
            invoice_type = InvoiceType(invoice_type)
        except ValueError:
            # TODO log error here
            print("\n\n\n\n\n")
            print(f"Invalid invoice type {invoice_type}")
            print("\n\n\n\n\n")
            return

        invoice: Invoice = session.query(Invoice).get(invoice_id)

        if not invoice:
            # TODO log error here
            print("\n\n\n\n\n")
            print(f"Invoice with id {invoice_id} not found")
            print("\n\n\n\n\n")
            return

        if payment.is_paid():
            invoice.status = InvoiceStatus.PAID
            session.commit()
        elif payment.is_pending():
            pass
        elif not payment.is_open():
            invoice.status = InvoiceStatus.FAILED
            session.commit()
        return
    except Error as err:
        # TODO log error
        print("\n\n\n\n\n")
        print(err)
        print("\n\n\n\n\n")
        raise HTTPException(400, str(err))
