from typing import List
from fastapi import APIRouter, Depends, File, UploadFile
from fastapi.exceptions import HTTPException
from sqlalchemy.orm.session import Session
from digirent.app import Application
from digirent.app.error import ApplicationError
from digirent.database.enums import UserRole
from digirent.database.models import Apartment, ApartmentApplication, Tenant, User
from .schema import (
    BankDetailSchema,
    LookingForSchema,
    PasswordUpdateSchema,
    ProfileSchema,
    ProfileUpdateSchema,
)
import digirent.api.dependencies as dependencies
from digirent.api.apartment_applications import schema as apartment_applications_schema


router = APIRouter()


@router.get("/", response_model=ProfileSchema)
async def me(user: User = Depends(dependencies.get_current_user)):
    return user


@router.put("/", response_model=ProfileSchema)
def update_profile_information(
    data: ProfileUpdateSchema,
    user: User = Depends(dependencies.get_current_user),
    app: Application = Depends(dependencies.get_application),
    session: Session = Depends(dependencies.get_database_session),
):
    try:
        return app.update_profile(session, user, **data.dict(by_alias=False))
    except ApplicationError as e:
        if "not found" in str(e).lower():
            raise HTTPException(404, str(e))
        raise HTTPException(400, str(e))


@router.post("/looking-for", response_model=ProfileSchema)
def set_tenant_looking_for(
    data: LookingForSchema,
    tenant: Tenant = Depends(dependencies.get_current_tenant),
    app: Application = Depends(dependencies.get_application),
    session: Session = Depends(dependencies.get_database_session),
):
    try:
        return app.set_looking_for(
            session, tenant, data.house_type, data.city, data.max_budget
        )
    except ApplicationError as e:
        if "not found" in str(e).lower():
            raise HTTPException(404, str(e))
        raise HTTPException(400, str(e))


@router.post("/bank", response_model=ProfileSchema)
def set_user_bank_details(
    data: BankDetailSchema,
    user: User = Depends(dependencies.get_current_user),
    app: Application = Depends(dependencies.get_application),
    session: Session = Depends(dependencies.get_database_session),
):
    try:
        return app.set_bank_detail(
            session, user, data.account_name, data.account_number
        )
    except ApplicationError as e:
        if "not found" in str(e).lower():
            raise HTTPException(404, str(e))
        raise HTTPException(400, str(e))


@router.put("/password", response_model=ProfileSchema)
def update_password(
    data: PasswordUpdateSchema,
    user: User = Depends(dependencies.get_current_user),
    app: Application = Depends(dependencies.get_application),
    session: Session = Depends(dependencies.get_database_session),
):
    try:
        return app.update_password(session, user, data.old_password, data.new_password)
    except ApplicationError as e:
        if "not found" in str(e).lower():
            raise HTTPException(404, str(e))
        raise HTTPException(400, str(e))


@router.post("/upload/copy-id", status_code=201, response_model=ProfileSchema)
def upload_copy_id(
    file: UploadFile = File(...),
    user: User = Depends(dependencies.get_current_user),
    app: Application = Depends(dependencies.get_application),
):
    try:
        file_extension = file.filename.split(".")[-1]
        return app.upload_copy_id(user, file.file, file_extension)
    except ApplicationError as e:
        if "not found" in str(e).lower():
            raise HTTPException(404, str(e))
        raise HTTPException(400, str(e))


@router.post("/upload/proof-of-income", status_code=201, response_model=ProfileSchema)
def upload_proof_of_income(
    file: UploadFile = File(...),
    tenant: Tenant = Depends(dependencies.get_current_tenant),
    app: Application = Depends(dependencies.get_application),
):
    try:
        file_extension = file.filename.split(".")[-1]
        return app.upload_proof_of_income(tenant, file.file, file_extension)
    except ApplicationError as e:
        if "not found" in str(e).lower():
            raise HTTPException(404, str(e))
        raise HTTPException(400, str(e))


@router.post(
    "/upload/proof-of-enrollment", status_code=201, response_model=ProfileSchema
)
def upload_proof_of_enrollment(
    file: UploadFile = File(...),
    tenant: Tenant = Depends(dependencies.get_current_tenant),
    app: Application = Depends(dependencies.get_application),
):
    try:
        file_extension = file.filename.split(".")[-1]
        return app.upload_proof_of_enrollment(tenant, file.file, file_extension)
    except ApplicationError as e:
        if "not found" in str(e).lower():
            raise HTTPException(404, str(e))
        raise HTTPException(400, str(e))


@router.post("/upload/profile-image", status_code=201, response_model=ProfileSchema)
def upload_profile_photo(
    file: UploadFile = File(...),
    user: User = Depends(dependencies.get_current_user),
    app: Application = Depends(dependencies.get_application),
):
    try:
        return app.upload_profile_image(user, file.file, file.filename)
    except ApplicationError as e:
        if "not found" in str(e).lower():
            raise HTTPException(404, str(e))
        raise HTTPException(400, str(e))


@router.get(
    "/applciations",
    status_code=200,
    response_model=List[apartment_applications_schema.ApartmentApplicationSchema],
)
def fetch_my_apartment_applications(
    user: User = Depends(dependencies.get_current_user),
    session: Session = Depends(dependencies.get_database_session),
):
    if user.role == UserRole.TENANT:
        return (
            session.query(ApartmentApplication)
            .filter(ApartmentApplication.tenant_id == user.id)
            .all()
        )
    elif user.role == UserRole.LANDLORD:
        return (
            session.query(ApartmentApplication)
            .join(Apartment)
            .filter(Apartment.landlord_id == user.id)
            .all()
        )
    else:
        raise HTTPException(403, "Forbidden")
