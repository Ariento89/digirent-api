import os
from starlette.config import Config
from starlette.datastructures import CommaSeparatedStrings
from pathlib import Path

APP_ENV: str = os.getenv("APP_ENV", "dev")


# eg .env.dev, .env.production, .env.test
p: Path = Path(__file__).parents[3] / f"env/.env.{APP_ENV}"
config: Config = Config(p if p.exists() else None)

PROJECT_NAME: str = "Digi Rent"

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
