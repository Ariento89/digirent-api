from typing import List
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.param_functions import Body
from jwt import PyJWTError
from digirent.app.error import ApplicationError
from sqlalchemy.orm.session import Session
from digirent.app import Application
import digirent.api.dependencies as dependencies
from digirent.database.models import Admin, Landlord, Tenant, User
from .schema import UserCreateSchema, UserSchema
from digirent import util
from digirent.core import config


router = APIRouter()

EMAIL_VERIFICATION_TOKEN_VALUE = "email_verification"


def generate_email_verification(user: User):
    token = util.create_token(
        {"type": EMAIL_VERIFICATION_TOKEN_VALUE, "email": user.email}
    )
    url = f"{config.CLIENT_HOST}/verify?token={token}"
    return f"Follow this link to verify your account {url}"


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
            message=generate_email_verification(result),
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
            message=generate_email_verification(result),
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


@router.post("/verify")
def verify_email(
    token: str = Body(...),
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
