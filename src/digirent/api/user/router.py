from typing import List
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from jwt import PyJWTError
from digirent.app.error import ApplicationError
from pathlib import Path
from sqlalchemy.orm.session import Session
from digirent.app import Application
import digirent.api.dependencies as dependencies
from digirent.database.models import Admin, Landlord, Tenant, User
from .schema import UserCreateSchema, UserSchema
from digirent import util
from digirent.core import config


router = APIRouter()

EMAIL_VERIFICATION_TOKEN_VALUE = "email_verification"

verification_email_path = Path(__file__).parents[4] / "templates/verification.html"


def generate_verification_url(user: User) -> str:
    token = util.create_token(
        {"type": EMAIL_VERIFICATION_TOKEN_VALUE, "email": user.email}
    )
    return f"{config.CLIENT_HOST}/verify?token={token.decode('utf-8')}"


def generate_email_verification_text(user: User) -> str:
    url = generate_verification_url(user)
    return f"""
        Hello, {user.first_name},
        Thank you for signing up on Digi rent.
        Please follow this url to verify your account {url}
    """


def generate_email_verification_html(user: User) -> str:
    url = generate_verification_url(user)
    with open(verification_email_path) as f:
        content = f.read()
        content = content.replace(
            "{{user_name}}", f"{user.first_name} {user.last_name}"
        )
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
        result = application.create_tenant(session, **data.dict())
        background_tasks.add_task(
            util.send_email,
            to=result.email,
            subject="Verify Acccount",
            message=generate_email_verification_text(result),
            html=generate_email_verification_html(result),
        )
        return result
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
        result = application.create_landlord(session, **data.dict())
        background_tasks.add_task(
            util.send_email,
            to=result.email,
            subject="Verify Acccount",
            message=generate_email_verification_text(result),
            html=generate_email_verification_html(result),
        )
        return result
    except ApplicationError as e:
        raise HTTPException(401, str(e))


@router.get("/", response_model=List[UserSchema])
def fetch_all_users(
    admin: Admin = Depends(dependencies.get_current_admin_user),
    session: Session = Depends(dependencies.get_database_session),
):
    return session.query(User).all()


@router.get("/landlords", response_model=List[UserSchema])
def fetch_all_landlords(
    # TODO pagination
    admin_or_tenant: Tenant = Depends(dependencies.get_current_admin_or_tenant),
    session: Session = Depends(dependencies.get_database_session),
):
    return session.query(Landlord).all()


@router.get("/tenants", response_model=List[UserSchema])
def fetch_all_tenants(
    # TODO pagination
    admin_or_landlord: Landlord = Depends(dependencies.get_current_admin_or_landlord),
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
    background_tasks.add_task(
        util.send_email,
        to=user.email,
        subject="Verify Acccount",
        message=generate_email_verification_text(user),
        html=generate_email_verification_html(user),
    )
    return {"status": "Success", "message": "Email sent successfully"}


@router.post("/verify/{token}")
def verify_email(
    token: str,
    session: Session = Depends(dependencies.get_database_session),
):
    error = HTTPException(400, "Invalid token")
    try:
        payload = util.get_payload_from_token(token)
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
