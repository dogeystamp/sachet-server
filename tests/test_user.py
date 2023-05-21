import pytest


def test_post(client, users, auth):
    """Test registering a user, then logging in to it."""
    # register without adequate permissions
    resp = client.post(
        "/users",
        headers=auth("no_admin_user"),
        json={"username": "claire", "permissions": [], "password": "claire123"},
    )
    assert resp.status_code == 403
    # properly register
    resp = client.post(
        "/users",
        headers=auth("administrator"),
        json={"username": "claire", "permissions": [], "password": "claire123"},
    )
    assert resp.status_code == 201
    data = resp.get_json()
    url = data.get("url")
    assert url is not None
    assert url == "/users/claire"

    # try logging in now
    resp = client.post(
        "/users/login", json={"username": "claire", "password": "claire123"}
    )
    assert resp.status_code == 200
    data = resp.get_json()
    assert data.get("status") == "success"
    assert data.get("username") == "claire"
    token = data.get("auth_token")
    assert token is not None and token != ""
