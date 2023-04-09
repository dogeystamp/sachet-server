from sachet.storage import Storage
from pathlib import Path
from werkzeug.utils import secure_filename
import json


class FileSystem(Storage):
    def __init__(self):
        # prevent circular import when inspecting this file outside of Flask
        from sachet.server import app

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
            self._meta_path = self._storage._get_meta_path(name)
            self._path.touch()
            self._meta_path.touch()
            self.metadata = self._Metadata(self)

        def delete(self, name):
            self._path.unlink()
            self._meta_path.unlink()

        def open(self, mode="r"):
            return self._path.open(mode=mode)

        def rename(self, new_name):
            new_path = self._storage._get_path(new_name)
            if new_path.exists():
                raise OSError(f"Path {path} already exists.")

            new_meta_path = self._storage._get_meta_path(new_name)
            if new_meta_path.exists():
                raise OSError(f"Path {path} already exists.")

            self._path.rename(new_path)
            self._meta_path.rename(new_meta_path)

        class _Metadata:
            def __init__(self, file):
                self.__dict__["_file"] = file

            @property
            def __data(self):
                with self._file._meta_path.open() as meta_file:
                    content = meta_file.read()
                    if len(content.strip()) == 0:
                        return {}
                    return json.loads(content)

            # there is no setter for __data because it would cause __setattr__ to infinitely recurse

            def __setattr__(self, name, value):
                data = self.__data
                data[name] = value
                with self._file._meta_path.open("w") as meta_file:
                    content = json.dumps(data)
                    meta_file.write(content)

            def __getattr__(self, name):
                return self.__data.get(name, None)
