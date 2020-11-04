import os
from typing import List
from starlette.config import Config
from starlette.datastructures import CommaSeparatedStrings
from pathlib import Path

APP_ENV: str = os.getenv("APP_ENV", "dev")


# eg .env.dev, .env.production, .env.test
p: Path = Path(__file__).parents[3] / f"env/.env.{APP_ENV}"
config: Config = Config(p if p.exists() else None)

PROJECT_NAME: str = "Digi Rent"

IS_DEVELOPMENT: bool = APP_ENV == "dev"

IS_TEST: bool = APP_ENV == "test"

IS_PRODUCTION: bool = APP_ENV == "prod"

ALLOWED_HOSTS: CommaSeparatedStrings = config(
    "ALLOWED_HOSTS", cast=CommaSeparatedStrings, default="localhost"
)

DATABASE_URL: str = config("DATABASE_URL", cast=str)

SECRET_KEY: str = config("SECRET_KEY", cast=str)

JWT_ALGORITHM: str = config("JWT_ALGORITHM", cast=str, default="HS256")

ACCESS_TOKEN_EXPIRE_MINUTES: int = config(
    "ACCESS_TOKEN_EXPIRE_MINUTES", cast=int, default=60
)

CLIENT_HOST: str = config("CLIENT_HOST", cast=str)  # host for frontend

SENDGRID_API_KEY: str = config("SENDGRID_API_KEY", cast=str, default=None)

EMAIL_SENDER: str = config("EMAIL_SENDER", cast=str)

MAIL_SERVER: str = config("MAIL_SERVER", cast=str, default=None)

MAIL_PORT: int = config("MAIL_PORT", cast=int, default=25)

MAIL_USERNAME: str = config("MAIL_USERNAME", cast=str, default=None)

MAIL_PASSWORD: str = config("MAIL_PASSWORD", cast=str, default=None)

UPLOAD_PATH: str = config("UPLOAD_PATH", cast=str, default="upload")

NUMBER_OF_APARTMENT_IMAGES: int = config("NUMBER_OF_APARTMENT_IMAGES", cast=int)

NUMBER_OF_APARTMENT_VIDEOS: int = config("NUMBER_OF_APARTMENT_VIDEOS", cast=int)

SUPPORTED_FILE_EXTENSIONS: List[str] = ["pdf", "doc", "docx"]

SUPPORTED_IMAGE_EXTENSIONS: List[str] = ["jpg", "jpeg", "png"]

SUPPORTED_VIDEO_EXTENSIONS: List[str] = ["mp4", "avi", "mkv"]

SIGNREQUEST_API_KEY: str = config("SIGNREQUEST_API_KEY", cast=str)

SIGNREQUEST_TEMPLATE_URL: str = config("SIGNREQUEST_TEMPLATE_URL", cast=str)

GOOGLE_CLIENT_ID: str = config("GOOGLE_CLIENT_ID", cast=str)

GOOGLE_CLIENT_SECRET: str = config("GOOGLE_CLIENT_SECRET", cast=str)

FACEBOOK_CLIENT_ID: str = config("FACEBOOK_CLIENT_ID", cast=str)

FACEBOOK_CLIENT_SECRET: str = config("FACEBOOK_CLIENT_SECRET", cast=str)

SQLALCHEMY_LOG: bool = config("SQLALCHEMY_LOG", cast=bool, default=False)

MOLLIE_API_KEY: str = config("MOLLIE_API_KEY", cast=str)

MOLLIE_WEBHOOK_URL: str = config("MOLLIE_WEBHOOK_URL", cast=str)

MOLLIE_REDIRECT_URL: str = config("MOLLIE_REDIRECT_URL", cast=str)

RENT_PAYMENT_DURATION_DAYS: int = config("RENT_PAYMENT_DURATION_DAYS", cast=int)

SUBSCRIPTION_PAYMENT_DURATION_DAYS: int = config(
    "SUBSCRIPTION_PAYMENT_DURATION_DAYS", cast=int
)
