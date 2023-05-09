import pytest

from sachet.server import storage
from uuid import UUID

"""Test suite for storage backends (not their API endpoints)."""


# if other storage backends are implemented we test them with the same suite with this line
@pytest.mark.parametrize("client", [{"SACHET_STORAGE": "filesystem"}], indirect=True)
class TestSuite:
    def test_creation(self, client, rand):
        """Test file pipeline.

        Creating, writing, reading, listing, reading size of files."""

        files = []
        for i in range(25):
            data_size = rand.randint(3000, 5000)
            files.append(
                dict(
                    name=str(UUID(bytes=rand.randbytes(16))),
                    data_size=data_size,
                    data=rand.randbytes(data_size),
                )
            )

        for file in files:
            handle = storage.get_file(file["name"])
            with handle.open(mode="wb") as f:
                f.write(file["data"])

        for file in files:
            handle = storage.get_file(file["name"])
            with handle.open(mode="rb") as f:
                saved_data = f.read()
                assert saved_data == file["data"]
                assert handle.size == file["data_size"]

        assert sorted([f.name for f in storage.list_files()]) == sorted(
            [f["name"] for f in files]
        )

    def test_rename(self, client, rand):
        files = [
            dict(
                name=str(UUID(bytes=rand.randbytes(16))),
                new_name=str(UUID(bytes=rand.randbytes(16))),
                data=rand.randbytes(4000),
            )
            for i in range(25)
        ]

        for file in files:
            handle = storage.get_file(file["name"])
            with handle.open(mode="wb") as f:
                f.write(file["data"])
            handle.rename(file["new_name"])

        for file in files:
            handle = storage.get_file(file["new_name"])
            with handle.open(mode="rb") as f:
                saved_data = f.read()
                assert saved_data == file["data"]
