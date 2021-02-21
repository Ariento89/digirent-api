import jwt
from pathlib import Path
from typing import Any, Optional, Union
from datetime import datetime, timedelta, date
from passlib.context import CryptContext
from digirent.core import config
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def create_token(payload: dict, expires_delta: timedelta = None):
    to_encode = payload.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=60)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, config.SECRET_KEY, algorithm=config.JWT_ALGORITHM)


def create_access_token(data: dict, expires_delta: timedelta = None):
    expire = expires_delta or timedelta(minutes=config.ACCESS_TOKEN_EXPIRE_MINUTES)
    return create_token(data, expire)


def get_payload_from_token(token: Union[str, bytes]) -> Any:
    return jwt.decode(token, config.SECRET_KEY, algorithms=[config.JWT_ALGORITHM])


def decode_access_token(token: Union[str, bytes]) -> str:
    # scenario token is not valid
    payload = get_payload_from_token(token)
    user_id: str = payload.get("sub")  # type: ignore
    return user_id


def password_is_match(plain_password: str, hashed_password: str):
    return pwd_context.verify(plain_password, hashed_password)


def hash_password(plain_password: str):
    return pwd_context.hash(plain_password)


def get_copy_ids_path() -> Path:
    """
    Get the copy id path
    """
    return Path(config.UPLOAD_PATH) / "copy_ids"


def get_proof_of_income_path() -> Path:
    """
    Get the proof of income path of a tenant
    """
    return Path(config.UPLOAD_PATH) / "proof_of_income"


def get_proof_of_enrollment_path() -> Path:
    """
    Get the proof of enrollment path
    """
    return Path(config.UPLOAD_PATH) / "proof_of_enrollment"


def get_apartment_images_folder_path(landlord, apartment) -> Path:
    """
    Get images folder path of a landlord's apartment
    """
    return Path(config.UPLOAD_PATH) / f"apartments/{landlord.id}/{apartment.id}/images"


def get_apartment_videos_folder_path(landlord, apartment) -> Path:
    """
    Get videos folder path of a landlord's apartment
    """
    return Path(config.UPLOAD_PATH) / f"apartments/{landlord.id}/{apartment.id}/videos"


def get_profile_path() -> Path:
    """
    Get profile folder
    """
    return Path(config.STATIC_PATH) / "profile_images"


def get_current_date() -> date:
    return datetime.utcnow().date()


def get_date_x_days_from(date: date, days: int = 30) -> date:
    return date + timedelta(days=days)


def get_human_readable_date(date: date) -> str:
    return date.strftime("%B %d %Y")


def send_email(
    to: str,
    subject: str,
    message: str,
    html: Optional[str] = None,
):
    """
    Send out email with sendgrid
    """
    try:
        msg = Mail(
            from_email="noreply@digirent.com",
            to_emails=to,
            subject=subject,
            plain_text_content=message,
            html_content=html,
        )
        if not config.IS_TEST:
            print("\n\n\n\n")
            print(str(message))
            print("\n\n\n\n")
        sg = SendGridAPIClient(config.SENDGRID_API_KEY)
        sg.send(msg)
    except Exception as e:
        print("\n\n\n\n")
        print("Sendgrid failed")
        print(str(e))
        print("\n\n\n\n")


def float_to_mollie_amount(amount: float) -> str:
    splitted_amount = str(amount).split(".")
    if len(splitted_amount) == 1:
        return f"{amount}.00"
    before_decimal, after_decimal = str(amount).split(".")
    if len(after_decimal) > 1:
        return str(amount)
    elif len(after_decimal) == 1:
        return f"{before_decimal}.{after_decimal}0"
    else:
        return f"{before_decimal}.00"


def generate_apple_client_secret() -> str:
    headers = {"kid": config.APPLE_KEY_ID}
    payload = {
        "iss": config.APPLE_TEAM_ID,
        "iat": datetime.now(),
        "exp": datetime.now() + timedelta(days=180),
        "aud": "https://appleid.apple.com",
        "sub": config.APPLE_CLIENT_ID,
    }
    return jwt.encode(
        payload,
        config.APPLE_PRIVATE_KEY,
        algorithm="ES256",
        headers=headers,
    ).decode("utf-8")
