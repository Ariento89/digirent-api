from typing import List
from uuid import UUID
from digirent.util import get_current_date
from digirent.database import models
from digirent.database.enums import (
    ApartmentApplicationStatus,
    InvoiceType,
)
from digirent.database.models import ApartmentApplication, Invoice
from digirent.worker.app import app
from digirent.database.base import SessionLocal
from sqlalchemy.orm.session import Session
from .helper import create_rent_payment


@app.task
def create_rent_invoice(apartment_application_id: UUID):
    session: Session = SessionLocal()
    try:
        apartment_application = session.query(ApartmentApplication).get(
            apartment_application_id
        )
        print("\n\n\n\n\nStarting create rent invoice")
        create_rent_payment(session, apartment_application)
        session.commit()
        print("\n\n\n\nEnd create rent invoice")
    except Exception:
        session.rollback()
    finally:
        session.close()


@app.task
def generate_rent_invoices(*args):
    session: Session = SessionLocal()
    try:
        print("\n\n\n\n\nStarting rent invoice worker")
        all_completed_apartment_applications: List[models.ApartmentApplication] = (
            session.query(models.ApartmentApplication)
            .filter(
                models.ApartmentApplication.status
                == ApartmentApplicationStatus.COMPLETED
            )
            .all()
        )
        for apartment_application in all_completed_apartment_applications:
            latest_invoice: Invoice = (
                session.query(Invoice)
                .filter(Invoice.type == InvoiceType.RENT)
                .filter(Invoice.apartment_application_id == apartment_application.id)
                .order_by(Invoice.created_at.desc())
                .first()
            )
            current_date = get_current_date()
            if latest_invoice.next_date <= current_date:
                # current date is greater than or equal to last invoice's next date
                create_rent_invoice.delay(apartment_application.id)
        print("\n\n\n\nEnd rent invoice worker")
    except Exception:
        session.rollback()
    finally:
        session.close()
