import pytest
from io import BytesIO
from werkzeug.datastructures import FileStorage
import uuid

"""Test anonymous authentication to endpoints."""


def test_files(client, auth, rand):
    # set create perm for anon users
    resp = client.patch(
        "/admin/settings",
        headers=auth("administrator"),
        json={"default_permissions": ["CREATE"]},
    )
    assert resp.status_code == 200

    # create share
    resp = client.post("/files", json={"file_name": "content.bin"})
    assert resp.status_code == 201

    data = resp.get_json()
    url = data.get("url")

    assert url is not None
    assert "/files/" in url

    upload_data = rand.randbytes(4000)

    # upload file to share
    resp = client.post(
        url + "/content",
        data={"upload": FileStorage(stream=BytesIO(upload_data), filename="upload")},
        content_type="multipart/form-data",
    )
    assert resp.status_code == 201

    # set read perm for anon users
    resp = client.patch(
        "/admin/settings",
        headers=auth("administrator"),
        json={"default_permissions": ["READ"]},
    )
    assert resp.status_code == 200

    # read file
    resp = client.get(
        url + "/content",
    )
    assert resp.data == upload_data
    assert "filename=content.bin" in resp.headers["Content-Disposition"].split("; ")

    # set modify perm for anon users
    resp = client.patch(
        "/admin/settings",
        headers=auth("administrator"),
        json={"default_permissions": ["MODIFY"]},
    )
    assert resp.status_code == 200

    # modify share
    upload_data = rand.randbytes(4000)
    resp = client.put(
        url + "/content",
        data={"upload": FileStorage(stream=BytesIO(upload_data), filename="upload")},
        content_type="multipart/form-data",
    )
    assert resp.status_code == 200
    resp = client.patch(
        url,
        json={"file_name": "new_bin.bin"},
    )
    # set read perm for anon users
    resp = client.patch(
        "/admin/settings",
        headers=auth("administrator"),
        json={"default_permissions": ["READ"]},
    )
    assert resp.status_code == 200
    resp = client.get(
        url + "/content",
    )
    assert resp.data == upload_data
    assert "filename=new_bin.bin" in resp.headers["Content-Disposition"].split("; ")

    # set list perm for anon users
    resp = client.patch(
        "/admin/settings",
        headers=auth("administrator"),
        json={"default_permissions": ["LIST"]},
    )
    assert resp.status_code == 200

    # test listing file
    resp = client.get(
        "/files",
        json={},
    )
    data = resp.get_json()
    assert resp.status_code == 200
    listed = data.get("data")
    assert len(listed) == 1
    assert listed[0].get("initialized") is True

    # set delete perm for anon users
    resp = client.patch(
        "/admin/settings",
        headers=auth("administrator"),
        json={"default_permissions": ["DELETE"]},
    )
    assert resp.status_code == 200

    # test deletion
    resp = client.delete(
        url,
    )
    assert resp.status_code == 200

    # set delete perm for anon users
    resp = client.patch(
        "/admin/settings",
        headers=auth("administrator"),
        json={"default_permissions": ["READ"]},
    )
    assert resp.status_code == 200
    # file shouldn't exist anymore
    resp = client.get(
        url + "/content",
    )
    assert resp.status_code == 404
