import pytest
from pathlib import Path
from typing import IO
from digirent.core.config import (
    UPLOAD_PATH,
    NUMBER_OF_APARTMENT_IMAGES,
    NUMBER_OF_APARTMENT_VIDEOS,
)
from digirent.app.error import ApplicationError
from digirent.app import Application
from digirent.database.models import (
    Apartment,
    Landlord,
    Tenant,
    User,
)


@pytest.mark.parametrize(
    "user",
    [
        "tenant",
        "landlord",
        "admin",
    ],
    indirect=True,
)
def test_user_upload_copy_id_ok(
    application: Application, user: User, file, clear_upload  # noqa
):
    file_extension = "pdf"
    user_file_path: Path = (
        Path(UPLOAD_PATH) / "copy_ids" / (str(user.id) + "." + file_extension)
    )
    assert not user_file_path.exists()
    application.upload_copy_id(user, file, file_extension)
    assert user_file_path.exists()


@pytest.mark.parametrize(
    "user",
    [
        "tenant",
        "landlord",
        "admin",
    ],
    indirect=True,
)
def test_user_upload_another_copy_id_to_replace_previous_ok(
    application: Application, user: User, file, clear_upload  # noqa
):
    file_extension = "pdf"
    user_file_path: Path = (
        Path(UPLOAD_PATH) / "copy_ids" / (str(user.id) + "." + file_extension)
    )
    assert not user_file_path.exists()
    application.upload_copy_id(user, file, file_extension)
    assert user_file_path.exists()
    application.upload_copy_id(user, file, "doc")
    assert not user_file_path.exists()
    user_file_path: Path = Path(UPLOAD_PATH) / "copy_ids" / (str(user.id) + "." + "doc")
    assert user_file_path.exists()


def test_tenant_upload_proof_of_income(
    application: Application, tenant: Tenant, file, clear_upload  # noqa
):
    file_extension = "pdf"
    tenant_file_path: Path = (
        Path(UPLOAD_PATH) / "proof_of_income" / (str(tenant.id) + "." + file_extension)
    )
    assert not tenant_file_path.exists()
    application.upload_proof_of_income(tenant, file, file_extension)
    assert tenant_file_path.exists()


def test_tenant_upload_proof_of_enrollment(
    application: Application, tenant: Tenant, file, clear_upload  # noqa
):
    file_extension = "pdf"
    tenant_file_path: Path = (
        Path(UPLOAD_PATH)
        / "proof_of_enrollment"
        / (str(tenant.id) + "." + file_extension)
    )
    assert not tenant_file_path.exists()
    application.upload_proof_of_enrollment(tenant, file, file_extension)
    assert tenant_file_path.exists()


def test_landlord_upload_apartment_images_ok(
    application: Application,
    landlord: Landlord,
    file: IO,
    apartment: Apartment,
    clear_upload,  # noqa
):
    filename = "image1.jpg"
    target_path: Path = (
        Path(UPLOAD_PATH) / f"apartments/{landlord.id}/{apartment.id}/images/{filename}"
    )
    assert not target_path.exists()
    application.upload_apartment_image(landlord, apartment, file, filename)
    assert target_path.exists()


def test_landlord_upload_apartment_video_ok(
    application: Application,
    landlord: Landlord,
    file: IO,
    apartment: Apartment,
    clear_upload,  # noqa
):
    filename = "video1.mp4"
    target_path: Path = (
        Path(UPLOAD_PATH) / f"apartments/{landlord.id}/{apartment.id}/videos/{filename}"
    )
    assert not target_path.exists()
    application.upload_apartment_video(landlord, apartment, file, filename)
    assert target_path.exists()


def test_landlord_upload_more_images_than_supported_fail(
    application: Application,
    landlord: Landlord,
    file: IO,
    apartment: Apartment,
    clear_upload,  # noqa
):
    filenames = [f"image{i}.jpg" for i in range(NUMBER_OF_APARTMENT_IMAGES)]
    for filename in filenames:
        target_path: Path = (
            Path(UPLOAD_PATH)
            / f"apartments/{landlord.id}/{apartment.id}/images/{filename}"
        )
        assert not target_path.exists()
        application.upload_apartment_image(landlord, apartment, file, filename)
        assert target_path.exists()
    with pytest.raises(ApplicationError):
        application.upload_apartment_image(
            landlord, apartment, file, f"image{NUMBER_OF_APARTMENT_IMAGES+7}.jpg"
        )


def test_tenant_upload_apartment_images_fail(
    application: Application,
    tenant: Tenant,
    file: IO,
    apartment: Apartment,
):
    filename = "image1.jpg"
    target_path: Path = (
        Path(UPLOAD_PATH) / f"apartments/{tenant.id}/{apartment.id}/images/{filename}"
    )
    assert not target_path.exists()
    with pytest.raises(AssertionError):
        application.upload_apartment_image(tenant, apartment, file, filename)
    assert not target_path.exists()


def test_tenant_upload_apartment_video_fail(
    application: Application,
    tenant: Tenant,
    file: IO,
    apartment: Apartment,
):
    filename = "video1.mp4"
    target_path: Path = (
        Path(UPLOAD_PATH) / f"apartments/{tenant.id}/{apartment.id}/videos/{filename}"
    )
    assert not target_path.exists()
    with pytest.raises(AssertionError):
        application.upload_apartment_video(tenant, apartment, file, filename)
    assert not target_path.exists()


def test_landlord_upload_more_videos_than_supported_fail(
    application: Application,
    landlord: Landlord,
    file: IO,
    apartment: Apartment,
    clear_upload,  # noqa
):
    filenames = [f"video{i}.mp4" for i in range(NUMBER_OF_APARTMENT_VIDEOS)]
    for filename in filenames:
        target_path: Path = (
            Path(UPLOAD_PATH)
            / f"apartments/{landlord.id}/{apartment.id}/videos/{filename}"
        )
        assert not target_path.exists()
        application.upload_apartment_video(landlord, apartment, file, filename)
        assert target_path.exists()
    with pytest.raises(ApplicationError):
        application.upload_apartment_video(
            landlord, apartment, file, f"video{NUMBER_OF_APARTMENT_VIDEOS+7}.mp4"
        )


def test_landlord_upload_unsupported_image_format_fail(
    application: Application,
    landlord: Landlord,
    file: IO,
    apartment: Apartment,
):
    filename = "image1.unsupported"
    target_path: Path = (
        Path(UPLOAD_PATH) / f"apartments/{landlord.id}/{apartment.id}/images/{filename}"
    )
    assert not target_path.exists()
    with pytest.raises(ApplicationError):
        application.upload_apartment_image(landlord, apartment, file, filename)
    assert not target_path.exists()


def test_landlord_upload_unsupported_video_format_fail(
    application: Application,
    landlord: Landlord,
    file: IO,
    apartment: Apartment,
):
    filename = "video1.unsupported"
    target_path: Path = (
        Path(UPLOAD_PATH) / f"apartments/{landlord.id}/{apartment.id}/images/{filename}"
    )
    assert not target_path.exists()
    with pytest.raises(ApplicationError):
        application.upload_apartment_image(landlord, apartment, file, filename)
    assert not target_path.exists()


def test_authenticated_user_upload_profile_photo_ok(
    application: Application,
    landlord: Landlord,
    file: IO,
    clear_upload,  # noqa
):
    filename = "profile1.jpg"
    target_path: Path = Path(UPLOAD_PATH) / f"profile_images/{landlord.id}.jpg"
    assert not target_path.exists()
    application.upload_profile_image(landlord, file, filename)
    assert target_path.exists()
