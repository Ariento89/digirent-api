from typing import List
from fastapi import APIRouter, Depends, HTTPException
from digirent.app.error import ApplicationError
from sqlalchemy.orm.session import Session
from digirent.app import Application
import digirent.api.dependencies as dependencies
from digirent.database.models import Admin, Landlord, Tenant, User
from .schema import UserCreateSchema, UserSchema

router = APIRouter()


@router.post("/tenant", response_model=UserSchema)
async def register_tenant(
    data: UserCreateSchema,
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
        return application.create_tenant(session, **data.dict())
    except ApplicationError as e:
        raise HTTPException(401, str(e))


@router.post("/landlord", response_model=UserSchema)
async def register_landlord(
    data: UserCreateSchema,
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
        return application.create_landlord(session, **data.dict())
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
