from celery import Celery
from digirent.core import config


app = Celery(
    "app",
    broker=config.CELERY_BROKER_URL,
    backend=config.CELERY_BACKEND_URL,
    include=["digirent.worker.rent", "digirent.worker.subscription"],
)


# Route all rent tasks to rent queue
# Route all subuscription tasks to subscription queue
# Create rent and subscription beat schedule for invoices
app.conf.update(
    task_routes={
        "digirent.worker.rent.*": {"queue": "rent-queue"},
        "digirent.worker.subscription.*": {"queue": "subscription-queue"},
    },
    beat_schedule={
        "create_rent_invoice": {
            "task": "digirent.worker.rent.generate_rent_invoices",
            "schedule": 300,
        },
        "create_subscription_invoice": {
            "task": "digirent.worker.subscription.generate_subscription_invoices",
            "schedule": 300,
        },
    },
)
