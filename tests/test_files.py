import pytest
from io import BytesIO
from werkzeug.datastructures import FileStorage
import uuid

"""Test file share endpoints."""


# if other storage backends are implemented we test them with the same suite
# this might be redundant because test_storage tests the backends already
@pytest.mark.parametrize("client", [{"SACHET_STORAGE": "filesystem"}], indirect=True)
class TestSuite:
    def test_sharing(self, client, users, auth, rand):
        # create share
        resp = client.post("/files", headers=auth("jeff"))
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

    def test_invalid(self, client, users, auth, rand):
        """Test invalid requests."""

        upload_data = rand.randbytes(4000)

        # unauthenticated
        resp = client.post("/files")
        assert resp.status_code == 401

        # non-existent
        resp = client.get("/files/" + str(uuid.UUID(int=0)), headers=auth("jeff"))
        assert resp.status_code == 404
        resp = client.get(
            "/files/" + str(uuid.UUID(int=0)) + "/content", headers=auth("jeff")
        )
        assert resp.status_code == 404
        resp = client.post(
            "/files/" + str(uuid.UUID(int=0)) + "/content", headers=auth("jeff")
        )
        assert resp.status_code == 404
        resp = client.put(
            "/files/" + str(uuid.UUID(int=0)) + "/content", headers=auth("jeff")
        )
        assert resp.status_code == 404

        # no CREATE permission
        resp = client.post("/files", headers=auth("no_create_user"))
        assert resp.status_code == 403

        # valid share creation to move on to testing content endpoint
        resp = client.post("/files", headers=auth("jeff"))
        assert resp.status_code == 201
        data = resp.get_json()
        url = data.get("url")

        # test invalid methods
        resp = client.put(
            url + "/content",
            headers=auth("jeff"),
            data={
                "upload": FileStorage(stream=BytesIO(upload_data), filename="upload")
            },
            content_type="multipart/form-data",
        )
        assert resp.status_code == 423
        resp = client.patch(
            url + "/content",
            headers=auth("jeff"),
            data={
                "upload": FileStorage(stream=BytesIO(upload_data), filename="upload")
            },
            content_type="multipart/form-data",
        )
        assert resp.status_code == 405

        # test other user being unable to upload to this share
        resp = client.post(
            url + "/content",
            headers=auth("dave"),
            data={
                "upload": FileStorage(stream=BytesIO(upload_data), filename="upload")
            },
            content_type="multipart/form-data",
        )
        assert resp.status_code == 403

        # upload file to share (properly)
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

        # no READ permission
        resp = client.get(url, headers=auth("no_read_user"))
        assert resp.status_code == 403
        resp = client.get(url + "/content", headers=auth("no_read_user"))
        assert resp.status_code == 403
