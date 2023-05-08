import pytest
from io import BytesIO
from werkzeug.datastructures import FileStorage
import uuid

"""Test anonymous authentication to endpoints."""


def test_files(client, auth, rand, upload):
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
    resp = upload(
        url + "/content",
        BytesIO(upload_data),
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
    resp = upload(
        url + "/content",
        BytesIO(upload_data),
        method=client.put,
    )
    assert resp.status_code == 201
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


def test_files_invalid(client, auth, rand, upload):
    # set create perm for anon users
    resp = client.patch(
        "/admin/settings",
        headers=auth("administrator"),
        json={"default_permissions": ["CREATE"]},
    )
    assert resp.status_code == 200

    # create an uninitialized share
    resp = client.post("/files", json={"file_name": "content.bin"})
    assert resp.status_code == 201
    data = resp.get_json()
    uninit_url = data.get("url")

    # upload a share
    resp = client.post("/files", json={"file_name": "content.bin"})
    assert resp.status_code == 201
    data = resp.get_json()
    url = data.get("url")
    upload_data = rand.randbytes(4000)
    resp = upload(
        url + "/content",
        BytesIO(upload_data)
    )
    assert resp.status_code == 201

    # disable all permissions
    resp = client.patch(
        "/admin/settings",
        headers=auth("administrator"),
        json={"default_permissions": []},
    )
    assert resp.status_code == 200

    # test initializing a share without perms
    resp = upload(
        url + "/content",
        BytesIO(upload_data)
    )
    assert resp.status_code == 401
    # test reading a share without perms
    resp = client.get(url + "/content")
    # test modifying an uninitialized share without perms
    resp = upload(
        uninit_url + "/content",
        BytesIO(upload_data),
        method=client.put
    )
    assert resp.status_code == 401
    # test modifying a share without perms
    resp = upload(
        url + "/content",
        BytesIO(upload_data),
        method=client.put
    )
    assert resp.status_code == 401

    # test deleting a share without perms
    resp = client.delete(url)
    assert resp.status_code == 401
    # test modifying share metadata without perms
    resp = client.patch(url)
    resp = client.put(url)
    assert resp.status_code == 401
    # test reading share metadata without perms
    resp = client.get(url)
    assert resp.status_code == 401

    # test listing shares without perms
    resp = client.get("/files")
    assert resp.status_code == 401
    # test creating share without perms
    resp = client.post("/files")
    assert resp.status_code == 401
