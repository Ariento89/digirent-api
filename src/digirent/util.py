from pathlib import Path
import jwt
from typing import Union
from datetime import datetime, timedelta
from passlib.context import CryptContext
from digirent.core.config import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    SECRET_KEY,
    JWT_ALGORITHM,
    UPLOAD_PATH,
)


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=JWT_ALGORITHM)


def decode_access_token(token: Union[str, bytes]) -> str:
    # scenario token is not valid
    payload = jwt.decode(token, SECRET_KEY, algorithms=[JWT_ALGORITHM])
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
    return Path(UPLOAD_PATH) / "copy_ids"


def get_proof_of_income_path() -> Path:
    """
    Get the proof of income path of a tenant
    """
    return Path(UPLOAD_PATH) / "proof_of_income"


def get_proof_of_enrollment_path() -> Path:
    """
    Get the proof of enrollment path
    """
    return Path(UPLOAD_PATH) / "proof_of_enrollment"


def get_apartment_images_folder_path(landlord, apartment) -> Path:
    """
    Get images folder path of a landlord's apartment
    """
    return Path(UPLOAD_PATH) / f"apartments/{landlord.id}/{apartment.id}/images"


def get_apartment_videos_folder_path(landlord, apartment) -> Path:
    """
    Get videos folder path of a landlord's apartment
    """
    return Path(UPLOAD_PATH) / f"apartments/{landlord.id}/{apartment.id}/videos"
