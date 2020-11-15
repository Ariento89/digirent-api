from sqlalchemy.orm.session import Session
from digirent.core import config
from digirent import util
from digirent.database.models import ApartmentApplication, Invoice, User
from digirent.database.enums import InvoiceType, InvoiceStatus, UserRole
from mollie.api.client import Client


mollie_client = Client()
mollie_client.set_api_key(config.MOLLIE_API_KEY)


def create_rent_payment(
    session: Session, apartment_application: ApartmentApplication
) -> Invoice:
    redirect_url: str = config.MOLLIE_REDIRECT_URL
    webhook_url: str = config.MOLLIE_WEBHOOK_URL
    start_date = util.get_current_date()
    start_date_text = util.get_human_readable_date(start_date)
    next_date = util.get_date_x_days_from(start_date, config.RENT_PAYMENT_DURATION_DAYS)
    next_date_text = util.get_human_readable_date(next_date)
    # TODO generate in util
    description = f"Invoice for payment from {start_date_text} to {next_date_text}"
    amount = round(apartment_application.apartment.total_price, 2)
    invoice = Invoice(
        apartment_application_id=apartment_application.id,
        type=InvoiceType.RENT,
        status=InvoiceStatus.PENDING,
        amount=amount,
        description=description,
        next_date=next_date,
    )
    session.add(invoice)
    session.flush()
    mollie_amount = util.float_to_mollie_amount(invoice.amount)
    payment = mollie_client.payments.create(
        {
            "amount": {"currency": "EUR", "value": mollie_amount},
            "description": description,
            "redirectUrl": redirect_url,
            "webhookUrl": webhook_url,
            "metadata": {
                "type": invoice.type,
                "invoice_id": str(invoice.id),
                "created_date": str(start_date),
                "next_date": str(next_date),
            },
        }
    )
    invoice.payment_id = payment.id
    return invoice


def create_subscription_payment(session: Session, user: User) -> Invoice:
    role_amount_mapping = {
        UserRole.TENANT: config.USER_SUBSCRIPTION_AMOUNT,
        UserRole.LANDLORD: config.LANDLORD_SUBSCRIPTION_AMOUNT,
    }
    redirect_url: str = config.MOLLIE_REDIRECT_URL
    webhook_url: str = config.MOLLIE_WEBHOOK_URL
    start_date = util.get_current_date()
    start_date_text = util.get_human_readable_date(start_date)
    next_date = util.get_date_x_days_from(
        start_date, config.SUBSCRIPTION_PAYMENT_DURATION_DAYS
    )
    next_date_text = util.get_human_readable_date(next_date)
    # TODO generate in util
    description = f"Invoice for payment from {start_date_text} to {next_date_text}"
    amount = round(role_amount_mapping[user.role], 2)
    invoice = Invoice(
        user_id=user.id,
        type=InvoiceType.SUBSCRIPTION,
        status=InvoiceStatus.PENDING,
        amount=amount,
        description=description,
        next_date=next_date,
    )
    session.add(invoice)
    session.flush()
    mollie_amount = util.float_to_mollie_amount(invoice.amount)
    payment = mollie_client.payments.create(
        {
            "amount": {"currency": "EUR", "value": mollie_amount},
            "description": description,
            "redirectUrl": redirect_url,
            "webhookUrl": webhook_url,
            "metadata": {
                "type": invoice.type,
                "invoice_id": str(invoice.id),
                "created_date": str(start_date),
                "next_date": str(next_date),
            },
        }
    )
    invoice.payment_id = payment.id
    return invoice
