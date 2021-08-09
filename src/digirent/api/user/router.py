from datetime import timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from jwt import PyJWTError
from digirent.api.apartments.schema import ApartmentSchema
from digirent.app.error import ApplicationError
from pathlib import Path
from sqlalchemy.orm.session import Session
from digirent.app import Application
import digirent.api.dependencies as dependencies
from digirent.database.models import Apartment, Landlord, Tenant, User
from digirent.database.enums import ActivityTokenType
from .schema import UserCreateSchema, UserSchema
from digirent import util
from digirent.core import config


router = APIRouter()

EMAIL_VERIFICATION_TOKEN_VALUE = ActivityTokenType.EMAIL_VERIFICATION.value

verification_email_path = Path(__file__).parents[4] / "templates/verification.html"


def generate_verification_url(user_email: str) -> str:
    token = util.create_token(
        {"type": EMAIL_VERIFICATION_TOKEN_VALUE, "email": user_email},
        expires_delta=timedelta(hours=24),
        secret=config.ACTIVITY_TOKEN_SECRET_KEY,
    )
    return f"{config.CLIENT_HOST}/verify?token={token.decode('utf-8')}"


def generate_email_verification_text(first_name: str, url: str) -> str:
    return f"""
        Hello, {first_name},
        Thank you for signing up on Digi rent.
        Please follow this url to verify your account {url}
    """


def generate_email_verification_html(user_name: str, url: str) -> str:
    with open(verification_email_path) as f:
        content = f.read()
        content = content.replace("{{user_name}}", user_name)
        content = content.replace("{{verification_url}}", url)
        return content


@router.post("/tenant", response_model=UserSchema)
async def register_tenant(
    data: UserCreateSchema,
    background_tasks: BackgroundTasks,
    application: Application = Depends(dependencies.get_application),
    session: Session = Depends(dependencies.get_database_session),
):
    try:
        existing_user_with_email = (
            session.query(User).filter(User.email == data.email).one_or_none()
        )
        if existing_user_with_email:
            raise HTTPException(409, "User with email already exists")
        existing_user_with_phonenumber = (
            session.query(User)
            .filter(User.phone_number == data.phone_number)
            .one_or_none()
        )
        if existing_user_with_phonenumber:
            raise HTTPException(409, "User with phone number aready exists")
        tenant = Tenant(**data.dict(exclude_unset=True, exclude={"password"}))
        tenant.hashed_password = util.hash_password(data.password)
        session.add(tenant)
        session.commit()
        url = generate_verification_url(tenant.email)
        background_tasks.add_task(
            util.send_email,
            to=tenant.email,
            subject="Verify Acccount",
            message=generate_email_verification_text(tenant.first_name, url),
            html=generate_email_verification_html(tenant.first_name, url),
        )
        return tenant
    except ApplicationError as e:
        raise HTTPException(401, str(e))


@router.post("/landlord", response_model=UserSchema)
async def register_landlord(
    data: UserCreateSchema,
    background_tasks: BackgroundTasks,
    application: Application = Depends(dependencies.get_application),
    session: Session = Depends(dependencies.get_database_session),
):
    try:
        existing_user_with_email = (
            session.query(User).filter(User.email == data.email).one_or_none()
        )
        if existing_user_with_email:
            raise HTTPException(409, "User with email already exists")
        existing_user_with_phonenumber = (
            session.query(User)
            .filter(User.phone_number == data.phone_number)
            .one_or_none()
        )
        if existing_user_with_phonenumber:
            raise HTTPException(409, "User with phone number aready exists")
        landlord = Landlord(**data.dict(exclude_unset=True, exclude={"password"}))
        landlord.hashed_password = util.hash_password(data.password)
        session.add(landlord)
        session.commit()
        url = generate_verification_url(landlord.email)
        background_tasks.add_task(
            util.send_email,
            to=landlord.email,
            subject="Verify Acccount",
            message=generate_email_verification_text(landlord.first_name, url),
            html=generate_email_verification_html(landlord.first_name, url),
        )
        return landlord
    except ApplicationError as e:
        raise HTTPException(401, str(e))


@router.get("/landlords", response_model=List[UserSchema])
def fetch_all_landlords(
    # TODO pagination
    tenant: Tenant = Depends(dependencies.get_current_tenant),
    session: Session = Depends(dependencies.get_database_session),
):
    return session.query(Landlord).all()


@router.get("/tenants", response_model=List[UserSchema])
def fetch_all_tenants(
    # TODO pagination
    landlord: Landlord = Depends(dependencies.get_current_landlord),
    session: Session = Depends(dependencies.get_database_session),
):
    return session.query(Tenant).all()


@router.post("/verify/resend")
def resend_verification_email(
    background_tasks: BackgroundTasks,
    user: User = Depends(dependencies.get_current_user),
    session: Session = Depends(dependencies.get_database_session),
):
    if user.email_verified:
        raise HTTPException(400, "User email already verified")
    url = generate_verification_url(user.email)
    background_tasks.add_task(
        util.send_email,
        to=user.email,
        subject="Verify Acccount",
        message=generate_email_verification_text(user.first_name, url),
        html=generate_email_verification_html(user.first_name, url),
    )
    return {"status": "Success", "message": "Email sent successfully"}


@router.post("/verify/{token}")
def verify_email(
    token: str,
    session: Session = Depends(dependencies.get_database_session),
):
    error = HTTPException(400, "Invalid token")
    try:
        payload = util.get_payload_from_token(
            token, secret=config.ACTIVITY_TOKEN_SECRET_KEY
        )
        token_type = payload["type"]
        if token_type != EMAIL_VERIFICATION_TOKEN_VALUE:
            raise error
        email = payload["email"]
        user_with_email: User = (
            session.query(User).filter(User.email == email).one_or_none()
        )
        if not user_with_email:
            raise error
        user_with_email.email_verified = True
        session.commit()
    except PyJWTError:
        raise error
    except KeyError:
        raise error


@router.get("/landlords/apartments", response_model=List[ApartmentSchema])
def fetch_landlord_apartments(
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    min_size: Optional[float] = None,
    max_size: Optional[float] = None,
    min_bedrooms: Optional[int] = None,
    max_bedrooms: Optional[int] = None,
    min_bathrooms: Optional[int] = None,
    max_bathrooms: Optional[int] = None,
    is_descending: Optional[bool] = False,
    is_archived: Optional[bool] = False,
    session: Session = Depends(dependencies.get_database_session),
    landlord: Landlord = Depends(dependencies.get_current_active_landlord),
):
    """Fetch authenticated landlords apartment"""
    query = session.query(Apartment)
    query = query.filter(Apartment.is_archived.is_(is_archived)).filter(
        Apartment.landlord == landlord.id
    )
    if min_price:
        query = query.filter(Apartment.monthly_price >= min_price)
    if max_price:
        query = query.filter(Apartment.monthly_price <= max_price)
    if min_size:
        query = query.filter(Apartment.size >= min_size)
    if max_size:
        query = query.filter(Apartment.size <= max_size)
    if min_bedrooms:
        query = query.filter(Apartment.bedrooms >= min_bedrooms)
    if max_bedrooms:
        query = query.filter(Apartment.bedrooms <= max_bedrooms)
    if min_bathrooms:
        query = query.filter(Apartment.bathrooms >= min_bathrooms)
    if max_bathrooms:
        query = query.filter(Apartment.bathrooms <= max_bathrooms)
    if latitude and longitude:
        center = "POINT({} {})".format(longitude, latitude)
        query = query.filter(Apartment.location.ST_Distance_Sphere(center) < 5000)
    query = (
        query.order_by(Apartment.created_at.desc())
        if is_descending
        else query.order_by(Apartment.created_at.asc())
    )
    return query.all()
