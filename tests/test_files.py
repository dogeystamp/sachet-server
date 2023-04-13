import pytest
from io import BytesIO
from werkzeug.datastructures import FileStorage

"""Test file share endpoints."""


# if other storage backends are implemented we test them with the same suite
# this might be redundant because test_storage tests the backends already
@pytest.mark.parametrize("client", [{"SACHET_STORAGE": "filesystem"}], indirect=True)
class TestSuite:
    def test_sharing(self, client, users, auth, rand):
        # create share
        resp = client.post(
            "/files", headers=auth("jeff")
        )
        assert resp.status_code == 201

        data = resp.get_json()
        url = data.get("url")

        assert url is not None
        assert "/files/" in url

        upload_data = rand.randbytes(4000)

        # upload file to share
        resp = client.post(
            url + "/content",
            headers=auth("jeff"),
            data={
                "upload": FileStorage(stream=BytesIO(upload_data), filename="upload")
            },
            content_type="multipart/form-data",
        )
        assert resp.status_code == 201

        # test not allowing re-upload
        resp = client.post(
            url + "/content",
            headers=auth("jeff"),
            data={
                "upload": FileStorage(stream=BytesIO(upload_data), filename="upload")
            },
            content_type="multipart/form-data",
        )
        assert resp.status_code == 423

        # read file
        resp = client.get(
            url + "/content",
            headers=auth("jeff"),
        )
        assert resp.data == upload_data

        # test deletion
        resp = client.delete(
            url,
            headers=auth("jeff"),
        )
        assert resp.status_code == 200

        # file shouldn't exist anymore
        resp = client.get(
            url + "/content",
            headers=auth("jeff"),
        )
        assert resp.status_code == 404
