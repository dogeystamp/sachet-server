import pytest
from bitmask import Bitmask
from sachet.server.models import Permissions, User
from datetime import datetime

user_schema = User.get_schema(User)


def test_get(client, auth, validate_info):
    """Test accessing the user information endpoint as a normal user."""

    # access user info endpoint
    resp = client.get(
        "/users/jeff", headers=auth("jeff")
    )
    assert resp.status_code == 200
    validate_info("jeff", resp.get_json())

    # access other user's info endpoint
    resp = client.get(
        "/users/administrator", headers=auth("jeff")
    )
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
    resp = client.get(
        "/users/jeff", headers=auth("administrator")
    )
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
    resp = client.get(
        "/users/jeff", headers=auth("jeff")
    )
    assert resp.status_code == 200
    validate_info("jeff", resp.get_json())


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
    new_data["register_date"] = datetime(2022, 2, 2, 0, 0, 0)

    resp = client.put(
        "/users/jeff",
        json=user_schema.dump(new_data),
        headers=auth("administrator"),
    )
    assert resp.status_code == 200

    # modify the expected values
    users["jeff"]["permissions"] = Bitmask(Permissions.ADMIN)

    # request new info
    resp = client.get(
        "/users/jeff", headers=auth("jeff")
    )
    assert resp.status_code == 200
    validate_info("jeff", resp.get_json())
