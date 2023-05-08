import pytest
from os.path import basename
from io import BytesIO
from werkzeug.datastructures import FileStorage
from sachet.server import storage
import uuid

"""Test file share endpoints."""


# if other storage backends are implemented we test them with the same suite
# this might be redundant because test_storage tests the backends already
@pytest.mark.parametrize("client", [{"SACHET_STORAGE": "filesystem"}], indirect=True)
class TestSuite:
    def test_sharing(self, client, users, auth, rand, upload):
        # create share
        resp = client.post(
            "/files", headers=auth("jeff"), json={"file_name": "content.bin"}
        )
        assert resp.status_code == 201

        data = resp.get_json()
        url = data.get("url")

        assert url is not None
        assert "/files/" in url

        upload_data = rand.randbytes(4000)

        resp = upload(
            url + "/content",
            BytesIO(upload_data),
            headers=auth("jeff"),
            chunk_size=1230,
        )
        assert resp.status_code == 201

        # read file
        resp = client.get(
            url + "/content",
            headers=auth("jeff"),
        )
        assert resp.data == upload_data
        assert "filename=content.bin" in resp.headers["Content-Disposition"].split("; ")

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

        for f in storage.list_files():
            assert basename(url) not in f.name

    def test_modification(self, client, users, auth, rand, upload):
        # create share
        resp = client.post(
            "/files", headers=auth("jeff"), json={"file_name": "content.bin"}
        )
        data = resp.get_json()
        url = data.get("url")

        upload_data = rand.randbytes(4000)
        new_data = rand.randbytes(4000)

        # upload file to share
        resp = upload(
            url + "/content",
            BytesIO(upload_data),
            headers=auth("jeff"),
        )
        assert resp.status_code == 201

        # modify metadata
        resp = client.patch(
            url,
            headers=auth("jeff"),
            json={"file_name": "new_bin.bin"},
        )
        assert resp.status_code == 200

        # modify file contents
        resp = upload(
            url + "/content",
            BytesIO(new_data),
            headers=auth("jeff"),
            method=client.put,
        )
        assert resp.status_code == 201

        # read file
        resp = client.get(
            url + "/content",
            headers=auth("jeff"),
        )
        assert resp.data == new_data
        assert "filename=new_bin.bin" in resp.headers["Content-Disposition"].split("; ")

    def test_invalid(self, client, users, auth, rand, upload):
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
        resp = client.post(
            "/files", headers=auth("jeff"), json={"file_name": "content.bin"}
        )
        assert resp.status_code == 201
        data = resp.get_json()
        url = data.get("url")

        # test invalid methods
        resp = upload(
            url + "/content",
            BytesIO(upload_data),
            headers=auth("jeff"),
            method=client.put,
        )
        assert resp.status_code == 423
        resp = upload(
            url + "/content",
            BytesIO(upload_data),
            headers=auth("jeff"),
            method=client.patch,
        )
        assert resp.status_code == 405

        # test other user being unable to upload to this share
        resp = upload(
            url + "/content",
            BytesIO(upload_data),
            headers=auth("dave"),
        )
        assert resp.status_code == 403

        # upload file to share (properly)
        resp = upload(
            url + "/content",
            BytesIO(upload_data),
            headers=auth("jeff"),
        )
        assert resp.status_code == 201

        # test other user being unable to modify this share
        resp = upload(
            url + "/content",
            BytesIO(upload_data),
            headers=auth("dave"),
            method=client.put,
        )
        assert resp.status_code == 403

        # test not allowing re-upload
        resp = upload(
            url + "/content",
            BytesIO(upload_data),
            headers=auth("jeff"),
        )
        assert resp.status_code == 423

        # no READ permission
        resp = client.get(url, headers=auth("no_read_user"))
        assert resp.status_code == 403
        resp = client.get(url + "/content", headers=auth("no_read_user"))
        assert resp.status_code == 403

    def test_locking(self, client, users, auth, rand, upload):
        # upload share
        resp = client.post(
            "/files", headers=auth("jeff"), json={"file_name": "content.bin"}
        )
        data = resp.get_json()
        url = data.get("url")
        upload_data = rand.randbytes(4000)
        resp = upload(
            url + "/content",
            BytesIO(upload_data),
            headers=auth("jeff"),
        )
        assert resp.status_code == 201

        # lock share
        resp = client.post(
            url + "/lock",
            headers=auth("jeff"),
        )
        assert resp.status_code == 200

        # attempt to modify share
        resp = upload(
            url + "/content",
            BytesIO(upload_data),
            headers=auth("jeff"),
            method=client.put,
        )
        assert resp.status_code == 423

        # attempt to delete share
        resp = client.delete(
            url,
            headers=auth("jeff"),
        )
        assert resp.status_code == 423

        # unlock share
        resp = client.post(
            url + "/unlock",
            headers=auth("jeff"),
        )
        assert resp.status_code == 200

        # attempt to modify share
        resp = upload(
            url + "/content",
            BytesIO(upload_data),
            headers=auth("jeff"),
            method=client.put,
        )
        assert resp.status_code == 201

        # attempt to delete share
        resp = client.delete(
            url,
            headers=auth("jeff"),
        )
        assert resp.status_code == 200

        # attempt to lock/unlock without perms
        resp = client.post(
            url + "/lock",
            headers=auth("no_lock_user"),
        )
        assert resp.status_code == 403
        resp = client.post(
            url + "/unlock",
            headers=auth("no_lock_user"),
        )
        assert resp.status_code == 403
