import io
import os
from pathlib import Path
from digirent.core.config import UPLOAD_PATH
from digirent.core.services.file_service import FileService

folder_path = Path(UPLOAD_PATH)


def test_import_file_ok(file_service: FileService, clear_upload):
    file = io.BytesIO()
    content = b"test content"
    file.write(content)
    file.seek(0)
    result = file_service.store_file(folder_path, "file.ext", file)
    assert isinstance(result, Path)
    assert result.exists()


def test_list_files_ok(file_service: FileService):
    for i in range(5):
        file = io.BytesIO()
        content = b"test content"
        file.write(content)
        file.seek(0)
        result = file_service.store_file(folder_path, f"file{i}.ext", file)
        assert isinstance(result, Path)
    assert len(os.listdir(Path(UPLOAD_PATH))) == 5
    result = file_service.list_files(folder_path)
    assert len(result) == 5
    assert all(x in result for x in [f"file{f}.ext" for f in range(5)])


def test_list_files_in_non_existing_directory_fail(file_service: FileService):
    target_path = Path(UPLOAD_PATH) / "nonexisting"
    assert not target_path.exists()
    file_service.list_files(target_path) == []


def test_get_file(file_service: FileService, clear_upload):
    file = io.BytesIO()
    content = b"test content"
    file.write(content)
    file.seek(0)
    result = file_service.store_file(folder_path, "test.txt", file)
    assert isinstance(result, Path)
    assert result.exists()
    result_file = file_service.get("test.txt", folder_path)
    file.seek(0)
    result_file.seek(0)
    assert result_file.read() == file.read()


def test_get_non_existing_file(file_service: FileService):
    file = io.BytesIO()
    content = b"test content"
    file.write(content)
    file.seek(0)
    result = file_service.store_file(folder_path, "test.txt", file)
    assert isinstance(result, Path)
    assert result.exists()
    result_file = file_service.get("something.txt", folder_path)
    assert not result_file


def test_delete_file_ok(file_service: FileService):
    file = io.BytesIO()
    content = b"test content"
    file.write(content)
    file.seek(0)
    result = file_service.store_file(folder_path, "test.txt", file)
    assert isinstance(result, Path)
    assert result.exists()
    file_service.delete("test.txt", folder_path)
    assert not result.exists()


def test_delete_non_existing_file_fail(file_service: FileService):
    file = io.BytesIO()
    content = b"test content"
    file.write(content)
    file.seek(0)
    result = file_service.store_file(folder_path, "test.txt", file)
    assert isinstance(result, Path)
    assert result.exists()
    res = file_service.delete("test.txt", folder_path)
    assert not result.exists()
    assert res
    res = file_service.delete("test.txt", folder_path)
    assert not res
