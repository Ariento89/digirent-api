import os
from typing import IO, List, Union
from pathlib import Path


class FileService:
    def store_file(self, folderpath: Path, filename: str, file: IO) -> Union[Path, str]:
        file.seek(0)
        if not folderpath.exists():
            folderpath.mkdir(parents=True)
        filepath = folderpath / filename
        with open(filepath, "wb") as f:
            f.write(file.read())
        return filepath

    def get(self, filename, folder_path: Path):
        if not folder_path.exists():
            return
        path: Path = folder_path / filename
        if not path.exists():
            return
        return open(path, "rb")

    def delete(self, filename, folder_path: Path):
        path = folder_path / f"{filename}"
        if not path.exists():
            return False
        os.remove(path)
        return True

    def list_files(self, folder_path: Path) -> List[str]:
        return os.listdir(folder_path) if folder_path.exists() else []
