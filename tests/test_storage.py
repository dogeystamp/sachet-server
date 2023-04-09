import pytest

from sachet.server import storage
from uuid import UUID

"""Test suite for storage backends (not their API endpoints)."""


# if other storage backends are implemented we test them with the same suite with this line
@pytest.mark.parametrize("client", [{"SACHET_STORAGE": "filesystem"}], indirect=True)
class TestSuite:
    def test_creation(self, client, rand):
        """Test the process of creating, writing, then reading files with metadata, and also listing files."""

        files = [
            dict(
                name=str(UUID(bytes=rand.randbytes(16))),
                data=rand.randbytes(4000),
                metadata=dict(
                    sdljkf=dict(abc="def", aaa="bbb"),
                    lkdsjf=dict(ld="sdlfj", sdljf="sdlkjf"),
                    sdlfkj="sjdlkfsldk",
                    ssjdklf=rand.randint(-1000, 1000),
                ),
            )
            for i in range(25)
        ]

        for file in files:
            storage.create(file["name"])
            with storage.open(file["name"], mode="wb") as f:
                f.write(file["data"])
            storage.write_metadata(file["name"], file["metadata"])

        for file in files:
            with storage.open(file["name"], mode="rb") as f:
                saved_data = f.read()
                assert saved_data == file["data"]
                saved_meta = storage.read_metadata(file["name"])
                assert saved_meta == file["metadata"]

        assert sorted([f.name for f in storage.list_files()]) == sorted(
            [f["name"] for f in files]
        )

    def test_rename(self, client, rand):
        files = [
            dict(
                name=str(UUID(bytes=rand.randbytes(16))),
                new_name=str(UUID(bytes=rand.randbytes(16))),
                data=rand.randbytes(4000),
                metadata=dict(
                    sdljkf=dict(abc="def", aaa="bbb"),
                    lkdsjf=dict(ld="sdlfj", sdljf="sdlkjf"),
                    sdlfkj="sjdlkfsldk",
                    ssjdklf=rand.randint(-1000, 1000),
                ),
            )
            for i in range(25)
        ]

        for file in files:
            storage.create(file["name"])
            with storage.open(file["name"], mode="wb") as f:
                f.write(file["data"])
            storage.write_metadata(file["name"], file["metadata"])
            storage.rename(file["name"], file["new_name"])

        for file in files:
            with storage.open(file["new_name"], mode="rb") as f:
                saved_data = f.read()
                assert saved_data == file["data"]
                saved_meta = storage.read_metadata(file["new_name"])
                assert saved_meta == file["metadata"]
