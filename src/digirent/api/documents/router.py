from fastapi import (
    Depends,
    HTTPException,
    APIRouter,
    UploadFile,
    File,
    Response,
)
from pathlib import Path
from digirent.api.documents.schema import FileUploadResponseSchema
from digirent.app.error import ApplicationError
from digirent.database.models import User, Tenant
from digirent.app import Application
from digirent.api import dependencies as deps
from digirent.core import config
from digirent.util import (
    get_copy_ids_path,
    get_proof_of_enrollment_path,
    get_proof_of_income_path,
)


router = APIRouter()


@router.post("/copy-id", status_code=201, response_model=FileUploadResponseSchema)
def upload_copy_id(
    file: UploadFile = File(...),
    user: User = Depends(deps.get_current_user),
    app: Application = Depends(deps.get_application),
):
    try:
        file_extension = file.filename.split(".")[-1]
        app.upload_copy_id(user, file.file, file_extension)
        return {"status": "Success", "message": "Copy Id uploaded successfully"}
    except ApplicationError as e:
        if "not found" in str(e).lower():
            raise HTTPException(404, str(e))
        raise HTTPException(400, str(e))


@router.get("/copy-id")
def download_copy_id(
    user: User = Depends(deps.get_current_user),
):
    """
    Download user copy id
    """
    possible_filenames = [
        f"{user.id}.{ext}" for ext in config.SUPPORTED_FILE_EXTENSIONS
    ]
    copy_id_folder_path = get_copy_ids_path()
    for filename in possible_filenames:
        file_path: Path = copy_id_folder_path / filename
        if file_path.exists():
            with open(file_path, "rb") as f:
                return Response(
                    f.read(),
                    media_type="application/octet-stream",
                    headers={"Content-Disposition": f"attachment;filename={filename}"},
                )


@router.post(
    "/proof-of-income", status_code=201, response_model=FileUploadResponseSchema
)
def upload_proof_of_income(
    file: UploadFile = File(...),
    tenant: Tenant = Depends(deps.get_current_tenant),
    app: Application = Depends(deps.get_application),
):
    try:
        file_extension = file.filename.split(".")[-1]
        app.upload_proof_of_income(tenant, file.file, file_extension)
        return {"status": "Success", "message": "Proof of income uploaded successfully"}
    except ApplicationError as e:
        if "not found" in str(e).lower():
            raise HTTPException(404, str(e))
        raise HTTPException(400, str(e))


@router.get("/proof-of-income")
def download_proof_of_income(
    tenant: Tenant = Depends(deps.get_current_tenant),
):
    """
    Download user proof of income
    """
    possible_filenames = [
        f"{tenant.id}.{ext}" for ext in config.SUPPORTED_FILE_EXTENSIONS
    ]
    folder_path = get_proof_of_income_path()
    for filename in possible_filenames:
        file_path: Path = folder_path / filename
        if file_path.exists():
            with open(file_path, "rb") as f:
                return Response(
                    f.read(),
                    media_type="application/octet-stream",
                    headers={"Content-Disposition": f"attachment;filename={filename}"},
                )


@router.post(
    "/proof-of-enrollment",
    status_code=201,
    response_model=FileUploadResponseSchema,
)
def upload_proof_of_enrollment(
    file: UploadFile = File(...),
    tenant: Tenant = Depends(deps.get_current_tenant),
    app: Application = Depends(deps.get_application),
):
    try:
        file_extension = file.filename.split(".")[-1]
        app.upload_proof_of_enrollment(tenant, file.file, file_extension)
        return {
            "status": "Success",
            "message": "Proof of enrollment uploaded successfully",
        }
    except ApplicationError as e:
        if "not found" in str(e).lower():
            raise HTTPException(404, str(e))
        raise HTTPException(400, str(e))


@router.get("/proof-of-enrollment")
def download_proof_of_enrollment(
    tenant: Tenant = Depends(deps.get_current_tenant),
):
    """
    Download user proof of enrollment
    """
    possible_filenames = [
        f"{tenant.id}.{ext}" for ext in config.SUPPORTED_FILE_EXTENSIONS
    ]
    folder_path = get_proof_of_enrollment_path()
    for filename in possible_filenames:
        file_path: Path = folder_path / filename
        if file_path.exists():
            with open(file_path, "rb") as f:
                return Response(
                    f.read(),
                    media_type="application/octet-stream",
                    headers={"Content-Disposition": f"attachment;filename={filename}"},
                )


@router.post("/profile-image", status_code=201, response_model=FileUploadResponseSchema)
def upload_profile_photo(
    file: UploadFile = File(...),
    user: User = Depends(deps.get_current_user),
    app: Application = Depends(deps.get_application),
):
    try:
        app.upload_profile_image(user, file.file, file.filename)
        return {"status": "Success", "message": "Profile image uploaded successfully"}
    except ApplicationError as e:
        if "not found" in str(e).lower():
            raise HTTPException(404, str(e))
        raise HTTPException(400, str(e))
