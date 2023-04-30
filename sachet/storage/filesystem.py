from sachet.storage import Storage
from flask import current_app
from pathlib import Path
from werkzeug.utils import secure_filename
import json


class FileSystem(Storage):
    def __init__(self):
        config_path = Path(current_app.config["SACHET_FILE_DIR"])
        if config_path.is_absolute():
            self._directory = config_path
        else:
            self._directory = Path(current_app.instance_path) / config_path

        self._files_directory = self._directory / Path("files")

        self._files_directory.mkdir(mode=0o700, exist_ok=True, parents=True)

        if not self._directory.is_dir():
            raise OSError(f"'{current_app.config['SACHET_FILE_DIR']}' is not a directory.")

    def _get_path(self, name):
        name = secure_filename(name)
        return self._files_directory / Path(name)

    def list_files(self):
        return [
            self.get_file(x.name)
            for x in self._files_directory.iterdir()
            if x.is_file()
        ]

    def get_file(self, name):
        return self.File(self, name)

    class File:
        def __init__(self, storage, name):
            self.name = name
            self._storage = storage
            self._path = self._storage._get_path(name)
            self._path.touch()

        def delete(self, name):
            self._path.unlink()

        def open(self, mode="r"):
            return self._path.open(mode=mode)

        def rename(self, new_name):
            new_path = self._storage._get_path(new_name)
            if new_path.exists():
                raise OSError(f"Path {path} already exists.")

            self._path.rename(new_path)
