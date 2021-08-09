from typing import List
from uuid import UUID
from digirent.util import get_current_date
from digirent.database.enums import (
    InvoiceType,
    UserRole,
)
from digirent.database.models import User, Invoice
from digirent.worker.app import app
from digirent.database.base import SessionLocal
from sqlalchemy.orm.session import Session
from .helper import create_subscription_payment


@app.task
def create_subscription_invoice(user_id: UUID):
    session: Session = SessionLocal()
    try:
        user = session.query(User).get(user_id)
        print("\n\n\n\n\nStarting create subscription invoice")
        create_subscription_payment(session, user)
        session.commit()
        print("\n\n\n\nEnd create subscription invoice")
    except Exception:
        session.rollback()
    finally:
        session.close()


@app.task
def generate_subscription_invoices(*args):
    session: Session = SessionLocal()
    try:
        print("\n\n\n\n\nStarting subscription invoice worker")
        # ? should be active users TODO
        non_admin_users: List[User] = session.query(User).all()
        for user in non_admin_users:
            latest_invoice: Invoice = (
                session.query(Invoice)
                .filter(Invoice.type == InvoiceType.SUBSCRIPTION)
                .filter(Invoice.user_id == user.id)
                .order_by(Invoice.created_at.desc())
                .first()
            )
            current_date = get_current_date()
            if latest_invoice.next_date <= current_date:
                # current date is greater than or equal to last invoice's next date
                create_subscription_invoice.delay(user.id)
        print("\n\n\n\nEnd subscription invoice worker")
    except Exception:
        session.rollback()
    finally:
        session.close()
