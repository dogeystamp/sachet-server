from sachet.storage import Storage
from pathlib import Path
from sachet.server import app
from werkzeug.utils import secure_filename
import json


class FileSystem(Storage):
    def __init__(self):
        config_path = Path(app.config["SACHET_FILE_DIR"])
        if config_path.is_absolute():
            self._directory = config_path
        else:
            self._directory = Path(app.instance_path) / config_path

        self._files_directory = self._directory / Path("files")
        self._meta_directory = self._directory / Path("meta")

        self._files_directory.mkdir(mode=0o700, exist_ok=True, parents=True)
        self._meta_directory.mkdir(mode=0o700, exist_ok=True, parents=True)

        if not self._directory.is_dir():
            raise OSError(f"'{app.config['SACHET_FILE_DIR']}' is not a directory.")

    def _get_path(self, name):
        name = secure_filename(name)
        return self._files_directory / Path(name)

    def _get_meta_path(self, name):
        name = secure_filename(name)
        return self._meta_directory / Path(name)

    def create(self, name):
        path = self._get_path(name)
        if path.exists():
            raise OSError(f"Path {path} already exists.")

        meta_path = self._get_meta_path(name)
        if meta_path.exists():
            raise OSError(f"Path {meta_path} already exists.")

        path.touch()
        meta_path.touch()

    def delete(self, name):
        path = self._get_path(name)
        if not path.exists():
            raise OSError(f"Path {path} does not exist.")
        path.unlink()

    def open(self, name, mode="r"):
        path = self._get_path(name)
        if not path.exists():
            raise OSError(f"Path {path} does not exist.")

        return path.open(mode=mode)

    def read_metadata(self, name):
        meta_path = self._get_meta_path(name)
        if not meta_path.exists():
            raise OSError(f"Path {meta_path} does not exist.")

        with meta_path.open() as meta_file:
            content = meta_file.read()
            return json.loads(content)

    def write_metadata(self, name, data):
        meta_path = self._get_meta_path(name)
        if not meta_path.exists():
            raise OSError(f"Path {meta_path} does not exist.")

        with meta_path.open("w") as meta_file:
            content = json.dumps(data)
            meta_file.write(content)

    def rename(self, name, new_name):
        path = self._get_path(name)
        if not path.exists():
            raise OSError(f"Path {path} does not exist.")
        new_path = self._get_path(new_name)
        if path.exists():
            raise OSError(f"Path {path} already exists.")

        meta_path = self._get_meta_path(name)
        if not path.exists():
            raise OSError(f"Path {meta_path} does not exist.")
        new_meta_path = self._get_meta_path(name)
        if path.exists():
            raise OSError(f"Path {path} already exists.")

        path.rename(new_path)
        meta_path.rename(new_meta_path)

    def list_files(self):
        return [x for x in self._files_directory.iterdir() if x.is_file()]
