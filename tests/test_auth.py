import pytest
import jwt
from sachet.server import db
from sachet.server.users import manage

def test_unauth_perms(client):
    """Test endpoints to see if they allow unauthenticated users."""
    resp = client.get("/users/jeff")
    assert resp.status_code == 401

def test_malformed_authorization(client):
    """Test attempting authorization incorrectly."""

    # incorrect token
    token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
    resp = client.get(
        "/users/jeff",
        headers={
            "Authorization": f"bearer {token}"
        }
    )
    assert resp.status_code == 401

    # invalid token
    token = "not a.real JWT.token"
    resp = client.get(
        "/users/jeff",
        headers={
            "Authorization": f"bearer {token}"
        }
    )
    assert resp.status_code == 401

    # missing token
    token = "not a.real JWT.token"
    resp = client.get(
        "/users/jeff",
        headers={
            "Authorization": ""
        }
    )
    assert resp.status_code == 401

def test_login(client, users):
    """Test logging in."""

    # wrong password
    resp = client.post("/users/login", json={
        "username": "jeff",
        "password": users["jeff"]["password"] + "garbage"
    })
    assert resp.status_code == 401

    # logging in correctly
    resp = client.post("/users/login", json={
        "username": "jeff",
        "password": users["jeff"]["password"]
    })
    assert resp.status_code == 200
    resp_json = resp.get_json()
    assert resp_json.get("status") == "success"
    assert resp_json.get("username") == "jeff"
    token = resp_json.get("auth_token")
    assert token is not None and token != ""

def test_userinfo(client, tokens, validate_info):
    """Test accessing the user information endpoint as a normal user."""

    # access user info endpoint
    resp = client.get(
        "/users/jeff",
        headers={
            "Authorization": f"bearer {tokens['jeff']}"
        }
    )
    assert resp.status_code == 200
    validate_info("jeff", resp.get_json())


    # access other user's info endpoint
    resp = client.get(
        "/users/administrator",
        headers={
            "Authorization": f"bearer {tokens['jeff']}"
        }
    )
    assert resp.status_code == 403

def test_userinfo_admin(client, tokens, validate_info):
    """Test accessing other user's information as an admin."""

    # first test that admin can access its own info
    resp = client.get(
        "/users/administrator",
        headers={
            "Authorization": f"bearer {tokens['administrator']}"
        }
    )
    assert resp.status_code == 200
    validate_info("administrator", resp.get_json())

    # now test accessing other user's info
    resp = client.get(
        "/users/jeff",
        headers={
            "Authorization": f"bearer {tokens['administrator']}"
        }
    )
    assert resp.status_code == 200
    validate_info("jeff", resp.get_json())
