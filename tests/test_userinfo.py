import pytest
from bitmask import Bitmask
from sachet.server.models import Permissions, User
from datetime import datetime

user_schema = User.get_schema(User)


def test_get(client, auth, validate_info):
    """Test accessing the user information endpoint as a normal user."""

    # access user info endpoint
    resp = client.get("/users/jeff", headers=auth("jeff"))
    assert resp.status_code == 200
    validate_info("jeff", resp.get_json())

    # access other user's info endpoint
    resp = client.get("/users/administrator", headers=auth("jeff"))
    assert resp.status_code == 403


def test_userinfo_admin(client, auth, validate_info):
    """Test accessing other user's information as an admin."""

    # first test that admin can access its own info
    resp = client.get(
        "/users/administrator",
        headers=auth("administrator"),
    )
    assert resp.status_code == 200
    validate_info("administrator", resp.get_json())

    # now test accessing other user's info
    resp = client.get("/users/jeff", headers=auth("administrator"))
    assert resp.status_code == 200
    validate_info("jeff", resp.get_json())


def test_patch(client, users, auth, validate_info):
    """Test modifying user information as an administrator."""

    # try with regular user to make sure it doesn't work
    resp = client.patch(
        "/users/jeff",
        json={"permissions": ["ADMIN"]},
        headers=auth("jeff"),
    )
    assert resp.status_code == 403

    # test malformed patch
    resp = client.patch(
        "/users/jeff",
        json="hurr durr",
        headers=auth("administrator"),
    )
    assert resp.status_code == 400

    resp = client.patch(
        "/users/jeff",
        json={"permissions": ["ADMIN"]},
        headers=auth("administrator"),
    )
    assert resp.status_code == 200

    # modify the expected values
    users["jeff"]["permissions"] = Bitmask(Permissions.ADMIN)

    # request new info
    resp = client.get("/users/jeff", headers=auth("jeff"))
    assert resp.status_code == 200
    validate_info("jeff", resp.get_json())

    # test password change through patch
    resp = client.patch(
            "/users/jeff",
            json=dict(password="123"),
            headers=auth("administrator"),
            )
    assert resp.status_code == 200

    # sign in with new token
    resp = client.post(
        "/users/login", json=dict(username="jeff", password="123")
    )
    assert resp.status_code == 200
    data = resp.get_json()
    new_token = data.get("auth_token")
    assert new_token

    # test that we're logged in
    resp = client.get("/users/jeff", headers=dict(Authorization=f"bearer {new_token}"))
    assert resp.status_code == 200


def test_put(client, users, auth, validate_info):
    """Test replacing user information as an administrator."""

    # try with regular user to make sure it doesn't work
    resp = client.patch(
        "/users/jeff",
        json=dict(),
        headers=auth("jeff"),
    )
    assert resp.status_code == 403

    new_data = {k: v for k, v in users["jeff"].items()}
    new_data["permissions"] = Bitmask(Permissions.ADMIN)

    json_data = user_schema.dump(new_data)
    json_data.update(dict(password="123"))

    resp = client.put(
        "/users/jeff",
        json=json_data,
        headers=auth("administrator"),
    )
    assert resp.status_code == 200

    # modify the expected values
    users["jeff"]["permissions"] = Bitmask(Permissions.ADMIN)

    # request new info
    resp = client.get("/users/jeff", headers=auth("jeff"))
    assert resp.status_code == 200
    validate_info("jeff", resp.get_json())

    # sign in with new token
    resp = client.post(
        "/users/login", json=dict(username="jeff", password="123")
    )
    assert resp.status_code == 200
    data = resp.get_json()
    new_token = data.get("auth_token")
    assert new_token

    # test that we're logged in
    resp = client.get("/users/jeff", headers=dict(Authorization=f"bearer {new_token}"))
    assert resp.status_code == 200
