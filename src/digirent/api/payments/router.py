from fastapi import APIRouter, Body

router = APIRouter()


@router.route("/webhook")
def payments_webhook_callback(payload: Body(...)):
    print("\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n")
    print("Payment webhook payload")
    print(payload)
    print("\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n")
    return payload
